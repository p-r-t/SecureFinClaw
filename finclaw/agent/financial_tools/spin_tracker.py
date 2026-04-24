"""Spin-Off Tracker Tool — EDGAR Form 10 / Form 10-12B listing of recent spin-offs.

Spin-offs register their new entity via:
  - Form 10   : Registration of a class of securities under Section 12(b) or 12(g)
  - Form 10-12B: Section 12(b) registration — the most common spin-off form
  - Form 10-12G: Section 12(g) registration

This tool scans the EDGAR full-text search API and daily indices for recent Form 10
filings, returning metadata so the agent can identify newly spun entities.

Commands:
  recent_spins   - List Form 10/10-12B filings from the last N months
  spin_profile   - Fetch basic profile of a spun entity from its Form 10 filing
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
_SPIN_FORMS = {"10", "10-12B", "10-12G", "10-12B/A", "10-12G/A"}


def _sec_get(url: str):
    import requests
    headers = {"User-Agent": _USER_AGENT, "Accept-Encoding": "gzip, deflate"}
    time.sleep(_SLEEP_SEC)
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp


def _quarter_of(d: date) -> int:
    return (d.month - 1) // 3 + 1


def _quarterly_idx_url(year: int, qtr: int) -> str:
    return f"https://www.sec.gov/Archives/edgar/full-index/{year}/QTR{qtr}/form.idx"


def _parse_form_idx_for_spins(text: str) -> list[dict]:
    """Parse a quarterly index file for Form 10 / 10-12B entries."""
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
        if form not in _SPIN_FORMS:
            continue
        filename = parts[-1].strip()
        date_raw = parts[-2].strip()
        if re.fullmatch(r"\d{8}", date_raw):
            filing_date = f"{date_raw[:4]}-{date_raw[4:6]}-{date_raw[6:]}"
        else:
            filing_date = date_raw
        cik = parts[-3].strip()
        company_name = " ".join(parts[1:-3]).strip()
        filing_url = f"https://www.sec.gov/Archives/{filename}"
        hits.append({
            "form": form,
            "company_name": company_name,
            "cik": cik,
            "filing_date": filing_date,
            "filing_url": filing_url,
        })
    return hits


def _cmd_recent_spins(months_back: int = 18) -> dict:
    """Scan EDGAR quarterly indices for recent Form 10 spin-off registrations."""
    cutoff = date.today() - timedelta(days=months_back * 30)
    today = date.today()

    # Identify which (year, quarter) pairs to scan
    periods: list[tuple[int, int]] = []
    d = today
    while d >= cutoff:
        periods.append((d.year, _quarter_of(d)))
        # Step back one quarter
        if d.month <= 3:
            d = d.replace(year=d.year - 1, month=10, day=1)
        elif d.month <= 6:
            d = d.replace(month=1, day=1)
        elif d.month <= 9:
            d = d.replace(month=4, day=1)
        else:
            d = d.replace(month=7, day=1)

    periods = list(dict.fromkeys(periods))  # deduplicate

    all_hits: list[dict] = []
    for year, qtr in periods:
        url = _quarterly_idx_url(year, qtr)
        try:
            text = _sec_get(url).text
            hits = _parse_form_idx_for_spins(text)
            # Filter to cutoff date
            for h in hits:
                try:
                    fd = datetime.strptime(h["filing_date"], "%Y-%m-%d").date()
                except Exception:
                    continue
                if fd >= cutoff:
                    all_hits.append(h)
        except Exception as exc:
            logger.debug(f"spin_tracker: index fetch {year}/QTR{qtr} failed: {exc}")
            continue

    # Deduplicate by CIK (10-12B/A amendments may appear multiple times)
    seen_ciks: set[str] = set()
    unique_hits = []
    for h in sorted(all_hits, key=lambda x: x["filing_date"], reverse=True):
        if h["cik"] not in seen_ciks:
            seen_ciks.add(h["cik"])
            unique_hits.append(h)

    return {
        "months_back": months_back,
        "as_of": today.isoformat(),
        "spin_count": len(unique_hits),
        "note": (
            "These are Form 10/10-12B registrations — newly spun-off or carved-out entities. "
            "Cross-reference filing_date with market_cap (run yfinance info) to find those "
            "below $5B. Run spin_profile for the full business description and parent context."
        ),
        "spins": unique_hits,
    }


def _cmd_spin_profile(filing_url: str) -> dict:
    """Extract key narrative from a Form 10 filing (business description, parent context)."""
    try:
        html = _sec_get(filing_url).text
    except Exception as exc:
        return {"error": f"Failed to fetch filing: {exc}"}

    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style"]):
        tag.decompose()
    text = "\n".join(ln.strip() for ln in soup.get_text(separator="\n").splitlines() if ln.strip())

    sections: dict[str, str] = {}
    _PATTERNS = [
        ("business_overview", re.compile(r"item\s+1[\.\s]*business\b", re.I)),
        ("risk_factors", re.compile(r"item\s+1a[\.\s]*risk\s+factors", re.I)),
        ("separation_overview", re.compile(r"(the\s+separation|the\s+spin.?off|our\s+company)", re.I)),
    ]
    ANY_ITEM = re.compile(r"^item\s+\d{1,2}[a-c]?[\.\s]", re.I | re.MULTILINE)

    for section_name, pattern in _PATTERNS:
        if section_name in sections:
            continue
        candidates = list(pattern.finditer(text))
        if not candidates:
            continue
        m = candidates[-1]
        heading_end = m.end()
        nl = text.find("\n", heading_end)
        content_start = (nl + 1) if 0 <= nl - heading_end <= 200 else heading_end
        next_heading = ANY_ITEM.search(text, heading_end + 10)
        section_end = next_heading.start() if next_heading else len(text)
        content = text[content_start:min(content_start + 8000, section_end)].strip()
        if content:
            sections[section_name] = content[:4000]

    return {"filing_url": filing_url, "sections": sections}


# ---------------------------------------------------------------------------
# Tool class
# ---------------------------------------------------------------------------

class SpinTrackerTool(Tool):
    """EDGAR Form 10/10-12B spin-off tracker for the Spin-Off & Special Situation funnel."""

    name = "spin_tracker"
    description = (
        "Track recent corporate spin-offs and carve-outs via EDGAR Form 10/10-12B registrations. "
        "Commands: "
        "'recent_spins' = list all Form 10/10-12B filings from the last N months — these are newly "
        "spun or carved-out entities that may have forced-selling dynamics and mispriced valuations; "
        "'spin_profile' = extract the business overview and separation rationale from a specific "
        "Form 10 filing URL. Used by the Spin-Off & Special Situation and Sum-of-Parts funnels. "
        "All data from SEC EDGAR (free)."
    )
    parameters = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "enum": ["recent_spins", "spin_profile"],
                "description": "Operation to perform.",
            },
            "months_back": {
                "type": "integer",
                "description": "Look-back in months for recent_spins. Default: 18 (per the Spin-Off funnel spec).",
                "minimum": 1,
                "maximum": 36,
            },
            "filing_url": {
                "type": "string",
                "description": "Direct URL to a Form 10 filing. Required for spin_profile.",
            },
        },
        "required": ["command"],
    }

    async def execute(self, **kwargs: Any) -> str:
        command = kwargs.get("command", "")
        logger.info(f"spin_tracker command={command}")

        if command == "recent_spins":
            months_back = int(kwargs.get("months_back", 18))
            result = await asyncio.to_thread(_cmd_recent_spins, months_back)

        elif command == "spin_profile":
            filing_url = (kwargs.get("filing_url") or "").strip()
            if not filing_url:
                return json.dumps({"error": "filing_url is required for spin_profile"})
            result = await asyncio.to_thread(_cmd_spin_profile, filing_url)

        else:
            result = {"error": f"Unknown command: {command!r}"}

        return json.dumps(sanitize_json(result), indent=2, ensure_ascii=False)
