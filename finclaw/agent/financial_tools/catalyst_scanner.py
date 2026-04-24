"""Catalyst Scanner Tool — SEC 8-K item classifier for news-driven screening.

Scans EDGAR 8-K filings for high-signal catalyst items:
  - Item 1.01: Entry into a material definitive agreement (contracts, partnerships)
  - Item 8.01: Other events (FDA approvals, regulatory clearances, major wins)
  - Item 1.02: Termination of material agreement (negative catalyst)
  - Item 5.02: Departure/appointment of directors or principal officers (turnaround signal)
  - Item 2.02: Results of operations (earnings releases)

Also checks for secondary offering risk via S-1/S-3 filings (dilution risk for small caps).

Commands:
  scan_recent_8k    - Scan 8-Ks from the last N days, classify by catalyst type
  ticker_catalysts  - Recent 8-K catalysts for a specific ticker
  dilution_check    - Check if a ticker has recent S-1/S-3 secondary offering filings
"""

from __future__ import annotations

import asyncio
import json
import re
import time
from datetime import date, datetime, timedelta
from typing import Any

from loguru import logger

from finclaw.agent.tools.base import Tool
from finclaw.agent.financial_tools.utils import sanitize_json

_USER_AGENT = "FinClaw research@finclaw.ai"
_SLEEP_SEC = 0.15

# 8-K item → catalyst type mapping
_ITEM_CATALYST_MAP: dict[str, dict] = {
    "1.01": {"type": "material_agreement", "signal": "positive",
             "label": "New Material Agreement (contract/partnership)"},
    "1.02": {"type": "agreement_termination", "signal": "negative",
             "label": "Agreement Termination"},
    "2.02": {"type": "earnings_release", "signal": "neutral",
             "label": "Earnings/Results Release"},
    "5.02": {"type": "management_change", "signal": "watch",
             "label": "Officer/Director Change (CEO/CFO turnover)"},
    "7.01": {"type": "fda_or_regulatory", "signal": "positive",
             "label": "Regulation FD / FDA / Regulatory Disclosure"},
    "8.01": {"type": "other_event", "signal": "positive",
             "label": "Other Material Event (FDA approval, major win, etc.)"},
}

_POSITIVE_ITEMS = {"1.01", "7.01", "8.01"}
_WATCH_ITEMS = {"5.02"}  # CEO/CFO changes = turnaround signal


def _sec_get(url: str):
    import requests
    headers = {"User-Agent": _USER_AGENT, "Accept-Encoding": "gzip, deflate"}
    time.sleep(_SLEEP_SEC)
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp


def _quarter_of(d: date) -> int:
    return (d.month - 1) // 3 + 1


def _daily_idx_url(d: date) -> str:
    qtr = _quarter_of(d)
    yyyymmdd = d.strftime("%Y%m%d")
    return f"https://www.sec.gov/Archives/edgar/daily-index/{d.year}/QTR{qtr}/form.{yyyymmdd}.idx"


def _parse_8k_idx(text: str) -> list[dict]:
    """Parse EDGAR daily index for 8-K entries."""
    lines = text.splitlines()
    start = 0
    for i, line in enumerate(lines):
        if line.strip().startswith("Form Type"):
            start = i + 2
            break

    hits = []
    for line in lines[start:]:
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) < 5:
            continue
        form = parts[0].strip()
        if form != "8-K":
            continue
        filename = parts[-1].strip()
        date_raw = parts[-2].strip()
        filing_date = f"{date_raw[:4]}-{date_raw[4:6]}-{date_raw[6:]}" if re.fullmatch(r"\d{8}", date_raw) else date_raw
        cik = parts[-3].strip()
        company_name = " ".join(parts[1:-3]).strip()
        filing_url = f"https://www.sec.gov/Archives/{filename}"
        hits.append({"cik": cik, "company_name": company_name,
                     "filing_date": filing_date, "filing_url": filing_url})
    return hits


def _fetch_8k_items(filing_url: str) -> list[str]:
    """Extract reported item numbers from an 8-K filing index or text."""
    try:
        text = _sec_get(filing_url).text
    except Exception:
        return []

    # Look for "Item X.XX" patterns in the filing header/body
    items = re.findall(r"item\s+(\d+\.\d+)", text, re.I)
    return list(dict.fromkeys(items))  # deduplicated, order-preserving


def _classify_items(items: list[str]) -> dict:
    """Classify 8-K items into catalyst types."""
    catalysts = []
    for item in items:
        if item in _ITEM_CATALYST_MAP:
            catalysts.append({"item": item, **_ITEM_CATALYST_MAP[item]})

    has_positive = any(c["signal"] == "positive" for c in catalysts)
    has_management_change = any(c["type"] == "management_change" for c in catalysts)

    return {
        "items": items,
        "catalysts": catalysts,
        "has_positive_catalyst": has_positive,
        "has_management_change": has_management_change,
        "catalyst_summary": ", ".join(c["label"] for c in catalysts) if catalysts else "No mapped catalyst",
    }


def _cmd_scan_recent_8k(days_back: int = 5, filter_positive: bool = True) -> dict:
    """Scan recent 8-K filings and classify by catalyst type."""
    all_hits = []
    today = date.today()
    for offset in range(days_back):
        d = today - timedelta(days=offset)
        if d.weekday() >= 5:  # skip weekends
            continue
        try:
            text = _sec_get(_daily_idx_url(d)).text
            hits = _parse_8k_idx(text)
            for h in hits:
                h["scan_date"] = d.isoformat()
            all_hits.extend(hits)
        except Exception as exc:
            logger.debug(f"catalyst_scanner: index fetch for {d}: {exc}")
            continue

    results = []
    for h in all_hits[:200]:  # cap to avoid timeout
        items = _fetch_8k_items(h["filing_url"])
        classification = _classify_items(items)
        if filter_positive and not classification["has_positive_catalyst"] and not classification["has_management_change"]:
            continue
        results.append({
            "company_name": h["company_name"],
            "cik": h["cik"],
            "filing_date": h["filing_date"],
            **classification,
            "filing_url": h["filing_url"],
        })

    return {
        "days_back": days_back,
        "total_8k_scanned": len(all_hits),
        "catalyst_hits": len(results),
        "filter_positive_only": filter_positive,
        "results": results,
    }


def _cmd_ticker_catalysts(ticker: str, days_back: int = 90) -> dict:
    """Fetch and classify recent 8-K filings for a specific ticker."""
    # Resolve CIK
    try:
        from finclaw.agent.financial_tools.insider_tool import _ticker_to_cik
        cik = _ticker_to_cik(ticker)
    except Exception:
        cik = None

    if not cik:
        return {"error": f"CIK not found for ticker {ticker!r}. Check the symbol."}

    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    try:
        data = _sec_get(url).json()
    except Exception as exc:
        return {"error": f"EDGAR submissions fetch failed: {exc}"}

    recent = data.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])
    accessions = recent.get("accessionNumber", [])
    primary_docs = recent.get("primaryDocument", [])

    cutoff = date.today() - timedelta(days=days_back)
    cik_int = str(int(cik))

    catalysts = []
    for form, filing_date_str, acc, doc in zip(forms, dates, accessions, primary_docs):
        if form not in ("8-K", "8-K/A"):
            continue
        try:
            filing_date = datetime.strptime(filing_date_str, "%Y-%m-%d").date()
        except Exception:
            continue
        if filing_date < cutoff:
            break
        acc_nodash = acc.replace("-", "")
        doc_url = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{acc_nodash}/{doc}"
        items = _fetch_8k_items(doc_url)
        classification = _classify_items(items)
        catalysts.append({
            "filing_date": filing_date_str,
            **classification,
            "filing_url": doc_url,
        })

    return {
        "ticker": ticker.upper(),
        "days_back": days_back,
        "filing_count": len(catalysts),
        "has_recent_positive_catalyst": any(c["has_positive_catalyst"] for c in catalysts),
        "has_recent_management_change": any(c["has_management_change"] for c in catalysts),
        "filings": catalysts,
    }


def _cmd_dilution_check(ticker: str, days_back: int = 365) -> dict:
    """Check for S-1/S-3 secondary offering filings (dilution risk signal)."""
    try:
        from finclaw.agent.financial_tools.insider_tool import _ticker_to_cik
        cik = _ticker_to_cik(ticker)
    except Exception:
        cik = None

    if not cik:
        return {"error": f"CIK not found for ticker {ticker!r}"}

    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    try:
        data = _sec_get(url).json()
    except Exception as exc:
        return {"error": f"EDGAR submissions fetch failed: {exc}"}

    recent = data.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])
    accessions = recent.get("accessionNumber", [])

    cutoff = date.today() - timedelta(days=days_back)
    offering_filings = []

    for form, filing_date_str, acc in zip(forms, dates, accessions):
        if form not in ("S-1", "S-1/A", "S-3", "S-3/A", "424B4", "424B3"):
            continue
        try:
            filing_date = datetime.strptime(filing_date_str, "%Y-%m-%d").date()
        except Exception:
            continue
        if filing_date < cutoff:
            continue
        offering_filings.append({"form": form, "filing_date": filing_date_str, "accession": acc})

    has_offerings = len(offering_filings) > 0
    return {
        "ticker": ticker.upper(),
        "days_back": days_back,
        "dilution_risk": "HIGH" if has_offerings else "LOW",
        "secondary_offering_filings": len(offering_filings),
        "note": (
            "Recent S-1/S-3/424B filings indicate the company has raised or is raising new equity. "
            "For small-cap catalyst plays, check offering size vs market cap to gauge dilution severity."
            if has_offerings else
            "No secondary offering filings found in the lookback period."
        ),
        "filings": offering_filings,
    }


# ---------------------------------------------------------------------------
# Tool class
# ---------------------------------------------------------------------------

class CatalystScannerTool(Tool):
    """SEC 8-K catalyst classifier and dilution risk checker."""

    name = "catalyst_scanner"
    description = (
        "Scan SEC 8-K filings for news-driven catalysts (contracts, FDA/regulatory approvals, "
        "management changes) and check for secondary offering dilution risk (S-1/S-3 filings). "
        "Commands: "
        "'scan_recent_8k' = scan all 8-Ks from the last N days and filter for positive catalysts "
        "(Item 1.01 agreements, Item 8.01 major events, Item 5.02 management changes); "
        "'ticker_catalysts' = classify recent 8-K items for a specific ticker; "
        "'dilution_check' = check if a small-cap has filed S-1/S-3 secondary offerings recently. "
        "Used by Small-Cap Catalyst, Turnaround, and Spin-Off funnels. All data from EDGAR (free)."
    )
    parameters = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "enum": ["scan_recent_8k", "ticker_catalysts", "dilution_check"],
                "description": "Operation to perform.",
            },
            "ticker": {
                "type": "string",
                "description": "Stock ticker. Required for ticker_catalysts and dilution_check.",
            },
            "days_back": {
                "type": "integer",
                "description": "Look-back window in days. Default: 5 for scan_recent_8k, 90 for ticker_catalysts, 365 for dilution_check.",
                "minimum": 1,
                "maximum": 730,
            },
            "filter_positive": {
                "type": "boolean",
                "description": "If true (default), scan_recent_8k only returns positive/watch catalysts.",
            },
        },
        "required": ["command"],
    }

    async def execute(self, **kwargs: Any) -> str:
        command = kwargs.get("command", "")
        logger.info(f"catalyst_scanner command={command}")

        if command == "scan_recent_8k":
            days_back = int(kwargs.get("days_back", 5))
            filter_positive = bool(kwargs.get("filter_positive", True))
            result = await asyncio.to_thread(_cmd_scan_recent_8k, days_back, filter_positive)

        elif command == "ticker_catalysts":
            ticker = (kwargs.get("ticker") or "").strip().upper()
            if not ticker:
                return json.dumps({"error": "ticker is required for ticker_catalysts"})
            days_back = int(kwargs.get("days_back", 90))
            result = await asyncio.to_thread(_cmd_ticker_catalysts, ticker, days_back)

        elif command == "dilution_check":
            ticker = (kwargs.get("ticker") or "").strip().upper()
            if not ticker:
                return json.dumps({"error": "ticker is required for dilution_check"})
            days_back = int(kwargs.get("days_back", 365))
            result = await asyncio.to_thread(_cmd_dilution_check, ticker, days_back)

        else:
            result = {"error": f"Unknown command: {command!r}"}

        return json.dumps(sanitize_json(result), indent=2, ensure_ascii=False)
