"""Web tools: web_search and web_fetch."""

import html
import ipaddress
import json
import os
import re
import socket
from typing import Any
from urllib.parse import urlparse

import httpx

from finclaw.agent.tools.base import Tool

# Shared constants
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7_2) AppleWebKit/537.36"
MAX_REDIRECTS = 5  # Limit redirects to prevent DoS attacks
BLOCKED_HOSTNAMES = {
    "localhost",
    "localhost.localdomain",
    "metadata.google.internal",
}


def _strip_tags(text: str) -> str:
    """Remove HTML tags and decode entities."""
    text = re.sub(r'<script[\s\S]*?</script>', '', text, flags=re.I)
    text = re.sub(r'<style[\s\S]*?</style>', '', text, flags=re.I)
    text = re.sub(r'<[^>]+>', '', text)
    return html.unescape(text).strip()


def _normalize(text: str) -> str:
    """Normalize whitespace."""
    text = re.sub(r'[ \t]+', ' ', text)
    return re.sub(r'\n{3,}', '\n\n', text).strip()


def _validate_url(url: str) -> tuple[bool, str]:
    """Validate URL: must be http(s) with valid domain."""
    try:
        p = urlparse(url)
        if p.scheme not in ('http', 'https'):
            return False, f"Only http/https allowed, got '{p.scheme or 'none'}'"
        if not p.netloc:
            return False, "Missing domain"
        if p.username or p.password:
            return False, "Credentials in URL are not allowed"
        if (p.hostname or "").lower() in BLOCKED_HOSTNAMES:
            return False, "Blocked hostname"
        return True, ""
    except Exception as e:
        return False, str(e)


def _is_blocked_ip(ip_str: str) -> bool:
    """Return True if IP belongs to private, local, or otherwise non-public range."""
    try:
        ip = ipaddress.ip_address(ip_str)
        return any(
            [
                ip.is_private,
                ip.is_loopback,
                ip.is_link_local,
                ip.is_reserved,
                ip.is_multicast,
                ip.is_unspecified,
            ]
        )
    except ValueError:
        return True


def _validate_public_host_sync(hostname: str | None) -> tuple[bool, str, str | None]:
    """Reject hostnames that resolve to local/private network addresses.

    Returns (ok, error_message, pinned_ip).  When *ok* is True the caller
    should use *pinned_ip* (if non-None) to connect instead of the hostname,
    preventing DNS-rebinding TOCTOU attacks (NemoClaw #1993).
    """
    if not hostname:
        return False, "Missing hostname", None
    host = hostname.strip().lower().rstrip(".")
    if not host:
        return False, "Missing hostname", None
    if host in BLOCKED_HOSTNAMES or host.endswith(".local"):
        return False, "Blocked hostname", None

    # If hostname is a literal IP address, validate directly.
    try:
        ipaddress.ip_address(host)
        if _is_blocked_ip(host):
            return False, "Blocked IP address", None
        return True, "", host
    except ValueError:
        pass

    try:
        infos = socket.getaddrinfo(host, None)
    except Exception as e:
        return False, f"DNS resolution failed: {e}", None

    if not infos:
        return False, "No DNS records", None

    pinned_ip: str | None = None
    for info in infos:
        sockaddr = info[4]
        if not sockaddr:
            continue
        ip_str = sockaddr[0]
        if _is_blocked_ip(ip_str):
            return False, f"Resolved to blocked IP: {ip_str}", None
        if pinned_ip is None:
            pinned_ip = ip_str
    return True, "", pinned_ip


class TavilySearchTool(Tool):
    """Search the web using Tavily Search API (optimized for AI agents)."""

    name = "web_search"
    description = (
        "Search the web. Returns titles, URLs, and snippets. "
        "Set topic to 'finance' for financial queries or 'news' for recent news."
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
            "count": {"type": "integer", "description": "Results (1-10)", "minimum": 1, "maximum": 10},
            "topic": {
                "type": "string",
                "enum": ["general", "news", "finance"],
                "description": "Search topic: 'general' (default), 'news', or 'finance'",
            },
        },
        "required": ["query"],
    }

    def __init__(self, api_key: str | None = None, max_results: int = 5):
        self.api_key = api_key or os.environ.get("TAVILY_API_KEY", "")
        self.max_results = max_results

    async def execute(
        self, query: str, count: int | None = None, topic: str = "general", **kwargs: Any
    ) -> str:
        if not self.api_key:
            return "Error: TAVILY_API_KEY not configured"

        try:
            n = min(max(count or self.max_results, 1), 10)
            payload = {
                "api_key": self.api_key,
                "query": query,
                "max_results": n,
                "search_depth": "basic",
                "topic": topic if topic in ("general", "news", "finance") else "general",
            }
            async with httpx.AsyncClient() as client:
                r = await client.post(
                    "https://api.tavily.com/search",
                    json=payload,
                    timeout=15.0,
                )
                r.raise_for_status()

            results = r.json().get("results", [])
            if not results:
                return f"No results for: {query}"

            lines = [f"Results for: {query}\n"]
            for i, item in enumerate(results[:n], 1):
                title = item.get("title", "")
                url = item.get("url", "")
                content = item.get("content", "")
                lines.append(f"{i}. {title}\n   {url}")
                if content:
                    lines.append(f"   {content}")
            return "\n".join(lines)
        except Exception as e:
            return f"Error: {e}"


class BraveSearchTool(Tool):
    """Search the web using Brave Search API (fallback)."""

    name = "web_search"
    description = "Search the web. Returns titles, URLs, and snippets."
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
            "count": {"type": "integer", "description": "Results (1-10)", "minimum": 1, "maximum": 10},
        },
        "required": ["query"],
    }

    def __init__(self, api_key: str | None = None, max_results: int = 5):
        self.api_key = api_key or os.environ.get("BRAVE_API_KEY", "")
        self.max_results = max_results

    async def execute(self, query: str, count: int | None = None, **kwargs: Any) -> str:
        if not self.api_key:
            return "Error: BRAVE_API_KEY not configured"

        try:
            n = min(max(count or self.max_results, 1), 10)
            async with httpx.AsyncClient() as client:
                r = await client.get(
                    "https://api.search.brave.com/res/v1/web/search",
                    params={"q": query, "count": n},
                    headers={"Accept": "application/json", "X-Subscription-Token": self.api_key},
                    timeout=10.0,
                )
                r.raise_for_status()

            results = r.json().get("web", {}).get("results", [])
            if not results:
                return f"No results for: {query}"

            lines = [f"Results for: {query}\n"]
            for i, item in enumerate(results[:n], 1):
                lines.append(f"{i}. {item.get('title', '')}\n   {item.get('url', '')}")
                if desc := item.get("description"):
                    lines.append(f"   {desc}")
            return "\n".join(lines)
        except Exception as e:
            return f"Error: {e}"


# Backwards-compatible alias
WebSearchTool = BraveSearchTool


class WebFetchTool(Tool):
    """Fetch and extract content from a URL using Readability."""
    
    name = "web_fetch"
    description = "Fetch URL and extract readable content (HTML → markdown/text)."
    parameters = {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "URL to fetch"},
            "extractMode": {"type": "string", "enum": ["markdown", "text"], "default": "markdown"},
            "maxChars": {"type": "integer", "minimum": 100}
        },
        "required": ["url"]
    }
    
    def __init__(self, max_chars: int = 50000):
        self.max_chars = max_chars
    
    async def execute(self, url: str, extractMode: str = "markdown", maxChars: int | None = None, **kwargs: Any) -> str:
        from readability import Document

        max_chars = maxChars or self.max_chars

        # Validate URL before fetching
        is_valid, error_msg = _validate_url(url)
        if not is_valid:
            return json.dumps({"error": f"URL validation failed: {error_msg}", "url": url})

        parsed = urlparse(url)
        host_ok, host_err, pinned_ip = _validate_public_host_sync(parsed.hostname)
        if not host_ok:
            return json.dumps({"error": f"URL host blocked: {host_err}", "url": url})

        # DNS-pinned URL: replace hostname with resolved IP to prevent DNS
        # rebinding between validation and the actual HTTP request (CWE-918,
        # inspired by NemoClaw #1993).  For HTTPS we keep the original hostname
        # so TLS certificate validation still works (the cert is bound to the
        # hostname, which itself prevents rebinding to a different server).
        fetch_url = url
        headers = {"User-Agent": USER_AGENT}
        if pinned_ip and parsed.scheme == "http" and parsed.hostname:
            fetch_url = url.replace(parsed.hostname, pinned_ip, 1)
            headers["Host"] = parsed.hostname

        try:
            async with httpx.AsyncClient(
                follow_redirects=True,
                max_redirects=MAX_REDIRECTS,
                timeout=30.0
            ) as client:
                r = await client.get(fetch_url, headers=headers)
                r.raise_for_status()

            final_parsed = urlparse(str(r.url))
            final_valid, final_error = _validate_url(str(r.url))
            if not final_valid:
                return json.dumps({"error": f"Final URL validation failed: {final_error}", "url": str(r.url)})

            final_host_ok, final_host_err, _ = _validate_public_host_sync(final_parsed.hostname)
            if not final_host_ok:
                return json.dumps({"error": f"Final URL host blocked: {final_host_err}", "url": str(r.url)})
            
            ctype = r.headers.get("content-type", "")
            
            # JSON
            if "application/json" in ctype:
                text, extractor = json.dumps(r.json(), indent=2), "json"
            # HTML
            elif "text/html" in ctype or r.text[:256].lower().startswith(("<!doctype", "<html")):
                doc = Document(r.text)
                content = self._to_markdown(doc.summary()) if extractMode == "markdown" else _strip_tags(doc.summary())
                text = f"# {doc.title()}\n\n{content}" if doc.title() else content
                extractor = "readability"
            else:
                text, extractor = r.text, "raw"
            
            truncated = len(text) > max_chars
            if truncated:
                text = text[:max_chars]
            
            return json.dumps({"url": url, "finalUrl": str(r.url), "status": r.status_code,
                              "extractor": extractor, "truncated": truncated, "length": len(text), "text": text})
        except Exception as e:
            return json.dumps({"error": str(e), "url": url})
    
    def _to_markdown(self, html: str) -> str:
        """Convert HTML to markdown."""
        # Convert links, headings, lists before stripping tags
        text = re.sub(r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>([\s\S]*?)</a>',
                      lambda m: f'[{_strip_tags(m[2])}]({m[1]})', html, flags=re.I)
        text = re.sub(r'<h([1-6])[^>]*>([\s\S]*?)</h\1>',
                      lambda m: f'\n{"#" * int(m[1])} {_strip_tags(m[2])}\n', text, flags=re.I)
        text = re.sub(r'<li[^>]*>([\s\S]*?)</li>', lambda m: f'\n- {_strip_tags(m[1])}', text, flags=re.I)
        text = re.sub(r'</(p|div|section|article)>', '\n\n', text, flags=re.I)
        text = re.sub(r'<(br|hr)\s*/?>', '\n', text, flags=re.I)
        return _normalize(_strip_tags(text))
