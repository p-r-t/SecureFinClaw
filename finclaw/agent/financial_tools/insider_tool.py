"""Insider Transaction Tool — SEC Form 4 scraper for insider buying signals.

Uses SEC EDGAR's free XBRL/JSON API to fetch Form 4 filings (Statement of
Changes in Beneficial Ownership). No paid data source required.

Commands:
  recent_filings  - List recent Form 4 filings for a ticker (last N days)
  cluster_check   - Detect cluster buying: 3+ distinct insiders buying > $100K each
                    within a rolling 60-day window; classifies 10b5-1 vs open-market
  insider_history - Full transaction history for a ticker (acquisitions + dispositions)
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
_EDGAR_BASE = "https://data.sec.gov"
_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"

_tickers_cache: dict | None = None


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _get(url: str) -> Any:
    import requests
    headers = {"User-Agent": _USER_AGENT, "Accept-Encoding": "gzip, deflate"}
    time.sleep(_SLEEP_SEC)
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp


def _get_json(url: str) -> dict:
    return _get(url).json()


# ---------------------------------------------------------------------------
# CIK resolution
# ---------------------------------------------------------------------------

def _load_tickers() -> dict:
    global _tickers_cache
    if _tickers_cache is not None:
        return _tickers_cache
    _tickers_cache = _get_json(_TICKERS_URL)
    return _tickers_cache


def _ticker_to_cik(ticker: str) -> str | None:
    data = _load_tickers()
    ticker_upper = ticker.strip().upper()
    for rec in data.values():
        if (rec.get("ticker") or "").upper() == ticker_upper:
            return str(rec["cik_str"]).zfill(10)
    return None


# ---------------------------------------------------------------------------
# Form 4 fetching via EDGAR submissions API
# ---------------------------------------------------------------------------

def _fetch_form4_filings(ticker: str, days_back: int = 90) -> list[dict]:
    """Return Form 4 filing metadata for a ticker within the last N days."""
    cik = _ticker_to_cik(ticker)
    if not cik:
        return []

    url = f"{_EDGAR_BASE}/submissions/CIK{cik}.json"
    try:
        data = _get_json(url)
    except Exception as exc:
        logger.warning(f"insider_tool: submissions fetch failed for {ticker}: {exc}")
        return []

    recent = data.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])
    accessions = recent.get("accessionNumber", [])
    primary_docs = recent.get("primaryDocument", [])
    reporters = recent.get("reportingOwnerNames", [None] * len(forms))

    cutoff = date.today() - timedelta(days=days_back)
    cik_int = str(int(cik))

    filings = []
    for form, filing_date_str, acc, doc, reporter in zip(forms, dates, accessions, primary_docs, reporters):
        if form != "4":
            continue
        try:
            filing_date = datetime.strptime(filing_date_str, "%Y-%m-%d").date()
        except Exception:
            continue
        if filing_date < cutoff:
            break  # submissions are sorted newest-first; stop when we pass the window
        acc_nodash = acc.replace("-", "")
        doc_url = f"https://www.sec.gov/Archives/edgar/data/{cik_int}/{acc_nodash}/{doc}"
        filings.append({
            "filing_date": filing_date_str,
            "accession": acc,
            "document_url": doc_url,
            "reporter": reporter,
        })

    return filings


# ---------------------------------------------------------------------------
# Parse individual Form 4 XML for transaction details
# ---------------------------------------------------------------------------

def _parse_form4_xml(xml_text: str) -> list[dict]:
    """Extract non-derivative transactions from a Form 4 XML filing."""
    try:
        from xml.etree import ElementTree as ET
        root = ET.fromstring(xml_text)
    except Exception:
        return []

    ns = ""
    reporter_name = ""
    reporter_title = ""
    is_10b5_1 = False

    # Reporter identity
    for rp in root.findall(f".//{ns}reportingOwner"):
        rn = rp.find(f"{ns}reportingOwnerId/{ns}rptOwnerName")
        if rn is not None and rn.text:
            reporter_name = rn.text.strip()
        rt = rp.find(f"{ns}reportingOwnerRelationship/{ns}officerTitle")
        if rt is not None and rt.text:
            reporter_title = rt.text.strip()
        is_dir = rp.find(f"{ns}reportingOwnerRelationship/{ns}isDirector")
        is_off = rp.find(f"{ns}reportingOwnerRelationship/{ns}isOfficer")

    # 10b5-1 flag — check footnotes and plan adoption flag
    footnotes_text = " ".join(
        fn.text or ""
        for fn in root.findall(f".//{ns}footnote")
    ).lower()
    if "10b5-1" in footnotes_text or "10b5–1" in footnotes_text:
        is_10b5_1 = True
    plan_tag = root.find(f".//{ns}planAdoptionDate")
    if plan_tag is not None and (plan_tag.text or "").strip():
        is_10b5_1 = True

    transactions = []
    for txn in root.findall(f".//{ns}nonDerivativeTransaction"):
        try:
            code_el = txn.find(f".//{ns}transactionCode")
            code = (code_el.text or "").strip().upper() if code_el is not None else ""
            # P = purchase, S = sale, A = award/grant (exclude), J = other
            if code not in ("P", "S"):
                continue

            shares_el = txn.find(f".//{ns}transactionShares/{ns}value")
            price_el = txn.find(f".//{ns}transactionPricePerShare/{ns}value")
            date_el = txn.find(f".//{ns}transactionDate/{ns}value")
            acq_el = txn.find(f".//{ns}transactionAcquiredDisposedCode/{ns}value")

            shares = float(shares_el.text) if shares_el is not None and shares_el.text else None
            price = float(price_el.text) if price_el is not None and price_el.text else None
            txn_date = (date_el.text or "").strip() if date_el is not None else ""
            acq_code = (acq_el.text or "").strip().upper() if acq_el is not None else ""

            value = round(shares * price, 0) if shares and price else None
            direction = "buy" if acq_code == "A" else ("sell" if acq_code == "D" else code)

            transactions.append({
                "reporter_name": reporter_name,
                "reporter_title": reporter_title,
                "transaction_date": txn_date,
                "direction": direction,
                "shares": shares,
                "price_per_share": price,
                "value_usd": value,
                "is_10b5_1": is_10b5_1,
            })
        except Exception:
            continue

    return transactions


def _fetch_and_parse_form4(doc_url: str) -> list[dict]:
    """Fetch a Form 4 XML filing and return parsed transactions."""
    xml_url = doc_url
    # The primaryDocument may be an .htm file; try to get the raw XML (.xml) sibling
    if doc_url.endswith(".htm") or doc_url.endswith(".html"):
        xml_url = re.sub(r"\.(htm|html)$", ".xml", doc_url, flags=re.I)

    try:
        text = _get(xml_url).text
    except Exception:
        try:
            text = _get(doc_url).text
        except Exception as exc:
            logger.debug(f"insider_tool: could not fetch {doc_url}: {exc}")
            return []

    return _parse_form4_xml(text)


# ---------------------------------------------------------------------------
# High-level commands
# ---------------------------------------------------------------------------

def _cmd_recent_filings(ticker: str, days_back: int = 90) -> dict:
    filings = _fetch_form4_filings(ticker, days_back)
    return {
        "ticker": ticker.upper(),
        "days_back": days_back,
        "filing_count": len(filings),
        "filings": filings,
    }


def _cmd_insider_history(ticker: str, days_back: int = 180) -> dict:
    """Fetch and parse all Form 4 filings within the window."""
    filings = _fetch_form4_filings(ticker, days_back)
    all_txns = []
    for f in filings:
        txns = _fetch_and_parse_form4(f["document_url"])
        for t in txns:
            t["filing_date"] = f["filing_date"]
        all_txns.extend(txns)

    buys = [t for t in all_txns if t["direction"] == "buy"]
    sells = [t for t in all_txns if t["direction"] == "sell"]
    open_market_buys = [t for t in buys if not t["is_10b5_1"]]

    return {
        "ticker": ticker.upper(),
        "days_back": days_back,
        "total_transactions": len(all_txns),
        "open_market_buys": len(open_market_buys),
        "sells": len(sells),
        "transactions": all_txns,
    }


def _cmd_cluster_check(ticker: str, window_days: int = 60,
                        min_insiders: int = 3, min_value_per: float = 100_000) -> dict:
    """Detect cluster insider buying within a rolling window.

    Cluster = min_insiders distinct insiders each buying >= min_value_per USD
    via open-market transactions (not 10b5-1 plans) within window_days.
    """
    filings = _fetch_form4_filings(ticker, days_back=window_days)
    all_txns = []
    for f in filings:
        txns = _fetch_and_parse_form4(f["document_url"])
        for t in txns:
            t["filing_date"] = f["filing_date"]
        all_txns.extend(txns)

    qualifying_buys: dict[str, float] = {}  # reporter_name → total value
    for t in all_txns:
        if t["direction"] != "buy":
            continue
        if t["is_10b5_1"]:
            continue
        val = t.get("value_usd") or 0
        if val >= min_value_per:
            name = t["reporter_name"]
            qualifying_buys[name] = qualifying_buys.get(name, 0) + val

    cluster_insiders = {k: v for k, v in qualifying_buys.items() if v >= min_value_per}
    cluster_detected = len(cluster_insiders) >= min_insiders
    total_cluster_value = sum(cluster_insiders.values())

    # Lookback sells: any insider who also sold in last 12 months (signal integrity check)
    sell_check_filings = _fetch_form4_filings(ticker, days_back=365)
    sellers: set[str] = set()
    for f in sell_check_filings:
        txns = _fetch_and_parse_form4(f["document_url"])
        for t in txns:
            if t["direction"] == "sell" and not t["is_10b5_1"]:
                sellers.add(t["reporter_name"])

    buyers_who_also_sold = [k for k in cluster_insiders if k in sellers]

    return {
        "ticker": ticker.upper(),
        "window_days": window_days,
        "cluster_detected": cluster_detected,
        "distinct_buying_insiders": len(cluster_insiders),
        "min_insiders_threshold": min_insiders,
        "total_cluster_value_usd": total_cluster_value,
        "qualifying_insiders": [
            {"name": k, "total_bought_usd": v} for k, v in sorted(
                cluster_insiders.items(), key=lambda x: x[1], reverse=True
            )
        ],
        "signal_integrity_warning": (
            f"Note: {buyers_who_also_sold} also sold shares in the last 12 months — "
            "buying may be selective signaling rather than full conviction."
            if buyers_who_also_sold else None
        ),
    }


# ---------------------------------------------------------------------------
# Tool class
# ---------------------------------------------------------------------------

class InsiderTool(Tool):
    """SEC Form 4 insider transaction tool — cluster buying detection and history."""

    name = "insider_transactions"
    description = (
        "Fetch and analyze SEC Form 4 insider transaction filings (free, direct from EDGAR). "
        "Commands: "
        "'recent_filings' = list Form 4 filings for a ticker in the last N days; "
        "'insider_history' = parse all open-market buys and sells with dollar values; "
        "'cluster_check' = detect cluster insider buying (3+ distinct insiders, >$100K each, "
        "within 60 days, excluding 10b5-1 plans) and flag any insiders who also sold in the "
        "prior 12 months. Used by the Insider Conviction, Turnaround, and Deep Value funnels."
    )
    parameters = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "enum": ["recent_filings", "insider_history", "cluster_check"],
                "description": "Operation to perform.",
            },
            "ticker": {
                "type": "string",
                "description": "US stock ticker symbol (e.g. 'AAPL').",
            },
            "days_back": {
                "type": "integer",
                "description": "Look-back window in days. Default: 90 for recent_filings/insider_history, 60 for cluster_check.",
                "minimum": 1,
                "maximum": 730,
            },
            "min_insiders": {
                "type": "integer",
                "description": "Minimum number of distinct buying insiders for cluster detection. Default: 3.",
                "minimum": 1,
                "maximum": 20,
            },
            "min_value_per": {
                "type": "number",
                "description": "Minimum USD value per insider to qualify for cluster. Default: 100000.",
                "minimum": 0,
            },
        },
        "required": ["command", "ticker"],
    }

    async def execute(self, **kwargs: Any) -> str:
        command = kwargs.get("command", "")
        ticker = (kwargs.get("ticker") or "").strip().upper()
        if not ticker:
            return json.dumps({"error": "ticker is required"})

        logger.info(f"insider_tool command={command} ticker={ticker}")

        if command == "recent_filings":
            days_back = int(kwargs.get("days_back", 90))
            result = await asyncio.to_thread(_cmd_recent_filings, ticker, days_back)

        elif command == "insider_history":
            days_back = int(kwargs.get("days_back", 180))
            result = await asyncio.to_thread(_cmd_insider_history, ticker, days_back)

        elif command == "cluster_check":
            days_back = int(kwargs.get("days_back", 60))
            min_insiders = int(kwargs.get("min_insiders", 3))
            min_value_per = float(kwargs.get("min_value_per", 100_000))
            result = await asyncio.to_thread(
                _cmd_cluster_check, ticker, days_back, min_insiders, min_value_per
            )

        else:
            result = {"error": f"Unknown command: {command!r}"}

        return json.dumps(sanitize_json(result), indent=2, ensure_ascii=False)
