---
name: summarize
description: >
  Summarize, extract, or transcribe content from URLs, articles, PDFs, local files, and YouTube
  videos using the `summarize` CLI. Use this skill when the user shares a link and asks "what's
  this about?", "summarize this", "TL;DR this article", "transcribe this YouTube video", or
  provides a local file path to summarize. Also triggers for "use summarize.sh". Handles paywalled
  sites (via Firecrawl) and YouTube transcripts (via Apify or native extraction).
homepage: https://summarize.sh
metadata: {"finclaw":{"emoji":"🧾","requires":{"bins":["summarize"]},"install":[{"id":"brew","kind":"brew","formula":"steipete/tap/summarize","bins":["summarize"],"label":"Install summarize (brew)"}]}}
---

# Summarize

Fast CLI to summarize URLs, local files, and YouTube links.

## Quick Start

```bash
# Summarize a URL
summarize "https://example.com/article"

# Summarize a local file (PDF, text, markdown, etc.)
summarize "/path/to/file.pdf"

# Summarize a YouTube video (transcript extraction)
summarize "https://youtu.be/dQw4w9WgXcQ" --youtube auto
```

## Length Control

```bash
--length short       # ~100 words
--length medium      # ~300 words (default)
--length long        # ~600 words
--length xl          # ~1000 words
--length 500         # exact character target
```

Use `short` for quick overviews. Use `xl` or `xxl` for detailed technical content.

## YouTube: Summary vs Transcript

```bash
# Best-effort transcript extraction (no yt-dlp needed)
summarize "https://youtu.be/VIDEO_ID" --youtube auto --extract-only
```

If the transcript is very long, return a `medium` summary first, then ask the user which
section or time range to expand. Never dump a raw transcript into the chat.

## Handling Paywalled / Bot-Blocked Sites

```bash
# Try Firecrawl as fallback extractor
summarize "https://ft.com/article" --firecrawl auto
```

Requires `FIRECRAWL_API_KEY`. If not set, mention this to the user.

## Model Selection

The default model is `google/gemini-3-flash-preview`. Override:

```bash
summarize "url" --model anthropic/claude-opus-4-5
summarize "url" --model openai/gpt-5.2
```

Match the model to the API key available in the environment:
- `GEMINI_API_KEY` → Google models
- `ANTHROPIC_API_KEY` → `anthropic/claude-*`
- `OPENAI_API_KEY` → `openai/*`

## Other Useful Flags

| Flag | Purpose |
|------|---------|
| `--extract-only` | Return raw text without LLM processing (URLs only) |
| `--json` | Machine-readable output |
| `--max-output-tokens N` | Cap output length |
| `--youtube auto` | Enable Apify YouTube fallback (needs `APIFY_API_TOKEN`) |

## Config File

```json
// ~/.summarize/config.json
{ "model": "openai/gpt-5.2" }
```
