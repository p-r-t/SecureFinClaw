"""Superinvestor 13F cloning tool."""

import json
import asyncio
from typing import Any
import xml.etree.ElementTree as ET
import httpx
from pydantic import ConfigDict
from loguru import logger

from finclaw.agent.tools.base import Tool
from finclaw.agent.financial_tools.utils import sanitize_json

SEC_HEADERS = {
    "User-Agent": "FinClaw/Explorer (contact@finclaw.io) AI Agent Tools"
}


class ClonerTool(Tool):
    """Parses SEC 13F-HR filings for Superinvestor ideas.

    Returns separate buckets for equity (SH), options (PUT/CALL), and bond (PRN)
    positions so the consumer can accurately clone only equity positions without
    accidentally treating derivatives or debt as stock holdings.
    """

    name = "get_13f_holdings"
    description = (
        "Fetches and parses the latest SEC 13F-HR filing for a given fund CIK to extract "
        "their portfolio holdings. This is used for cloning Superinvestor ideas. "
        "Returns separate lists for equity (SH), options (PUT/CALL), and bond (PRN) positions. "
        "Includes CUSIP for accurate cross-referencing and reliable delta tracking. "
        "Only use current_holdings (equity) for value-investing clone ideas."
    )
    parameters = {
        "type": "object",
        "properties": {
            "cik": {
                "type": "string",
                "description": "The SEC Central Index Key (CIK) of the fund (e.g. '0001067983')."
            },
            "compare_previous": {
                "type": "boolean",
                "description": "If true, compares current holdings with the previous 13F filing to identify deltas.",
                "default": False
            }
        },
        "required": ["cik"]
    }

    model_config = ConfigDict(arbitrary_types_allowed=True)

    async def _fetch_and_parse_13f(
        self, client: httpx.AsyncClient, cik_str: str, acc: str
    ) -> dict[str, list[dict]]:
        """Fetch and parse a 13F filing into typed position buckets.

        Returns a dict with three keys:
          equity:  SH-type positions (common stock, ETFs, ADRs — safe to clone)
          options: PUT or CALL positions (not equity)
          bonds:   PRN-type positions (bonds / convertible principal — not share count)

        Each position includes CUSIP for stable cross-filing identity.
        The ``put_call`` field on non-option rows will be an empty string.
        """
        cik_no_zeros = str(int(cik_str))
        dir_url = f"https://www.sec.gov/Archives/edgar/data/{cik_no_zeros}/{acc}/index.json"
        idx_resp = await client.get(dir_url, headers=SEC_HEADERS, timeout=10.0, follow_redirects=True)
        idx_resp.raise_for_status()
        idx_data = idx_resp.json()

        # Locate the infoTable XML file.
        xml_filename: str | None = None
        items = idx_data.get("directory", {}).get("item", [])
        xml_files = [i["name"] for i in items
                     if i["name"].lower().endswith(".xml") and i["name"] != "primary_doc.xml"]
        if not xml_files:
            # Fallback: any XML
            xml_files = [i["name"] for i in items if i["name"].lower().endswith(".xml")]

        if xml_files:
            for f in xml_files:
                if "infotable" in f.lower():
                    xml_filename = f
                    break
            if not xml_filename:
                # Pick the largest XML (most likely to be the info table)
                sized = {i["name"]: int(i.get("size", 0) or 0) for i in items if i["name"] in xml_files}
                xml_filename = max(sized, key=sized.get) if sized else xml_files[0]

        if not xml_filename:
            return {"equity": [], "options": [], "bonds": []}

        xml_url = f"https://www.sec.gov/Archives/edgar/data/{cik_no_zeros}/{acc}/{xml_filename}"
        xml_resp = await client.get(xml_url, headers=SEC_HEADERS, timeout=10.0, follow_redirects=True)
        xml_resp.raise_for_status()

        root = ET.fromstring(xml_resp.content)
        equity: list[dict] = []
        options: list[dict] = []
        bonds: list[dict] = []

        for info_table in root.findall(".//{*}infoTable"):
            issuer = (info_table.findtext("{*}nameOfIssuer") or "").strip()
            title = (info_table.findtext("{*}titleOfClass") or "").strip()
            cusip = (info_table.findtext("{*}cusip") or "").strip()
            value_raw = (info_table.findtext("{*}value") or "0").strip().replace(",", "")
            # putCall is only present for option positions; absent for equity/bonds.
            put_call = (info_table.findtext(".//{*}putCall") or "").strip().upper()

            shrs_node = info_table.find(".//{*}shrsOrPrnAmt")
            amount_raw = "0"
            amount_type = "SH"  # SH = shares; PRN = principal (bonds/convertibles)
            if shrs_node is not None:
                amount_raw = (shrs_node.findtext("{*}sshPrnamt") or "0").strip().replace(",", "")
                amount_type = (shrs_node.findtext("{*}sshPrnamtType") or "SH").strip().upper()

            try:
                value_usd_k = int(value_raw)
            except (ValueError, AttributeError):
                value_usd_k = 0

            try:
                amount = int(amount_raw)
            except (ValueError, AttributeError):
                amount = 0

            base: dict[str, Any] = {
                "issuer": issuer,
                "class": title,
                "cusip": cusip,
                "value_usd_thousands": value_usd_k,
            }

            if put_call in ("PUT", "CALL"):
                # Options: amount = number of option contracts, not underlying shares.
                options.append({**base, "put_call": put_call, "contracts": amount})
            elif amount_type == "PRN":
                # Bonds / convertibles: amount is face-value principal, not share count.
                bonds.append({**base, "principal_amount": amount})
            else:
                # Plain equity (SH): the only bucket suitable for value-investing cloning.
                equity.append({**base, "shares": amount})

        return {"equity": equity, "options": options, "bonds": bonds}

    async def execute(self, **kwargs: Any) -> str:
        cik = kwargs.get("cik")
        compare_prev = kwargs.get("compare_previous", False)
        if not cik:
            return json.dumps({"error": "CIK is required."})

        cik_str = str(cik).strip().zfill(10)

        try:
            async with httpx.AsyncClient() as client:
                subs_url = f"https://data.sec.gov/submissions/CIK{cik_str}.json"
                resp = await client.get(subs_url, headers=SEC_HEADERS, timeout=10.0)
                if resp.status_code != 200:
                    return json.dumps({"error": f"SEC API error: {resp.status_code}"})

                data = resp.json()
                filings = data.get("filings", {}).get("recent", {})
                forms = filings.get("form", [])
                accs = [a.replace("-", "") for a in filings.get("accessionNumber", [])]
                primary_docs = filings.get("primaryDocument", [])

                # Find current and previous 13F-HR (amendments included)
                indices = [i for i, f in enumerate(forms) if f in ("13F-HR", "13F-HR/A")]
                if not indices:
                    return json.dumps({"error": "No 13F-HR filings found."})

                current_idx = indices[0]
                current_acc = accs[current_idx]
                current_buckets = await self._fetch_and_parse_13f(client, cik_str, current_acc)

                result: dict[str, Any] = {
                    "fund_cik": cik_str,
                    "fund_name": data.get("name", ""),
                    "filing_url": (
                        f"https://www.sec.gov/Archives/edgar/data/{int(cik_str)}/"
                        f"{current_acc}/{primary_docs[current_idx]}"
                    ),
                    # Equity-only: the investable clone universe
                    "current_holdings": current_buckets["equity"][:50],
                    # Separated so LLM cannot accidentally conflate types
                    "options_positions": current_buckets["options"][:20],
                    "bond_positions": current_buckets["bonds"][:20],
                    "position_counts": {
                        "equity": len(current_buckets["equity"]),
                        "options": len(current_buckets["options"]),
                        "bonds": len(current_buckets["bonds"]),
                    },
                }

                if compare_prev and len(indices) > 1:
                    prev_acc = accs[indices[1]]
                    prev_buckets = await self._fetch_and_parse_13f(client, cik_str, prev_acc)

                    curr_equity = current_buckets["equity"]
                    prev_equity = prev_buckets["equity"]

                    # Use CUSIP as primary key for delta tracking; fall back to
                    # "issuer|class" for the rare case where CUSIP is absent.
                    def _pos_key(h: dict) -> str:
                        return h["cusip"] if h.get("cusip") else f"{h['issuer']}|{h['class']}"

                    curr_map = {_pos_key(h): h for h in curr_equity}
                    prev_map = {_pos_key(h): h for h in prev_equity}

                    new_positions: list[dict] = []
                    increased: list[dict] = []
                    decreased: list[dict] = []
                    exited: list[dict] = []

                    for key, holding in curr_map.items():
                        if key not in prev_map:
                            new_positions.append(holding)
                        else:
                            curr_shares = holding["shares"]
                            prev_shares = prev_map[key]["shares"]
                            if isinstance(curr_shares, int) and isinstance(prev_shares, int) and prev_shares > 0:
                                if curr_shares > prev_shares:
                                    pct = ((curr_shares - prev_shares) / prev_shares) * 100
                                    increased.append({
                                        "issuer": holding["issuer"],
                                        "cusip": holding["cusip"],
                                        "shares_added": curr_shares - prev_shares,
                                        "pct_change": round(pct, 1),
                                    })
                                elif curr_shares < prev_shares:
                                    pct = ((prev_shares - curr_shares) / prev_shares) * 100
                                    decreased.append({
                                        "issuer": holding["issuer"],
                                        "cusip": holding["cusip"],
                                        "shares_sold": prev_shares - curr_shares,
                                        "pct_change": round(pct, 1),
                                    })

                    for key, holding in prev_map.items():
                        if key not in curr_map:
                            exited.append({"issuer": holding["issuer"], "cusip": holding["cusip"]})

                    result["deltas"] = {
                        "new_positions": new_positions[:20],
                        "top_increases": sorted(increased, key=lambda x: x["pct_change"], reverse=True)[:10],
                        "top_decreases": sorted(decreased, key=lambda x: x["pct_change"], reverse=True)[:10],
                        "exited_positions": exited[:20],
                    }

                return json.dumps(sanitize_json(result), indent=2)

        except Exception as e:
            logger.exception("Failed to clone 13F")
            return json.dumps(sanitize_json({"error": f"Unexpected error: {str(e)}"}))
