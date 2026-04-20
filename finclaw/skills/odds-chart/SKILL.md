---
name: odds-chart
description: >
  Plot a probability-over-time chart for a Polymarket prediction market. Use when the user asks
  to chart, graph, visualize, or see how odds/probability have changed over time for a prediction
  market event. Only supports Polymarket (not Kalshi — no public price history). Requires
  matplotlib to be installed in the Python environment.
---

# Prediction Market Chart

Only Polymarket supports public price history (CLOB timeseries). Kalshi does not.

---

## Step 1 — Get History Data

Call the prediction market tool if you don't already have a cache file:

```
prediction_market(query="Get market history for <event name or slug>")
```

The output will end with:
```
(Full raw data: /path/to/workspace/cache/prediction_market_YYYYMMDD_HHMMSS_XXXXXX.json)
```

Copy this path exactly.

---

## Step 2 — Read the Cache File

```
read_file("/path/to/cache/prediction_market_....json")
```

| Command used | Points array path |
|---|---|
| `market_history` | `result["history"]["points"]` |
| `top_mover` | `result["history"]["points"]` |
| `history` (standalone) | `result["points"]` |

Each point: `{"timestamp": "2026-02-01T12:00:00Z", "probability": 0.6523}`

Also extract:
- **Title**: `result["detail"]["title"]` or user's query text
- **Summary**: `result["summary"]` → has `start.probability`, `end.probability`, `change_pct`

---

## Step 3 — Write and Execute the Plot Script

Create the directory and write the script in one step:

```
exec("mkdir -p {workspace}/charts")
```

Write `{workspace}/charts/plot_pm.py`:

```python
import json, sys
from datetime import datetime, timezone
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

CACHE_FILE = "{CACHE_FILE_PATH}"
OUTPUT_FILE = "{OUTPUT_PATH}"
TITLE = "{MARKET_TITLE}"

with open(CACHE_FILE) as f:
    raw = json.load(f)

hist = raw.get("history") or raw
points = hist.get("points", [])
if not points:
    print("No data points found"); sys.exit(1)

def _parse_ts(val):
    if isinstance(val, (int, float)):
        unix = val / 1000 if val > 1e10 else val
        return datetime.fromtimestamp(unix, tz=timezone.utc)
    s = str(val).strip()
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        unix = float(s)
        unix = unix / 1000 if unix > 1e10 else unix
        return datetime.fromtimestamp(unix, tz=timezone.utc)

timestamps = [_parse_ts(p["timestamp"]) for p in points]
probs = [round(float(p["probability"]) * 100, 2) for p in points]

fig, ax = plt.subplots(figsize=(12, 5))
fig.patch.set_facecolor("#0f1117")
ax.set_facecolor("#0f1117")

ax.plot(timestamps, probs, color="#00d4aa", linewidth=1.8, zorder=3)
ax.fill_between(timestamps, probs, alpha=0.12, color="#00d4aa")

# Annotate key points
ax.annotate(f"{probs[0]:.1f}%", xy=(timestamps[0], probs[0]),
            xytext=(6, 4), textcoords="offset points", color="#00d4aa", fontsize=9)
ax.annotate(f"{probs[-1]:.1f}%", xy=(timestamps[-1], probs[-1]),
            xytext=(-30, 4), textcoords="offset points", color="#00d4aa", fontsize=9)

# Mark peak and trough if range > 10%
if max(probs) - min(probs) > 10:
    peak_i = probs.index(max(probs))
    ax.annotate(f"↑{max(probs):.1f}%", xy=(timestamps[peak_i], max(probs)),
                xytext=(0, 8), textcoords="offset points", color="#ffcc44", fontsize=8,
                ha="center")

ax.set_ylim(max(0, min(probs) - 5), min(100, max(probs) + 8))
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.0f}%"))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
fig.autofmt_xdate(rotation=30, ha="right")

ax.set_title(TITLE, color="white", fontsize=13, pad=12, wrap=True)
ax.set_ylabel("Yes Probability", color="#aaaaaa", fontsize=10)
ax.tick_params(colors="#888888")
for spine in ax.spines.values():
    spine.set_edgecolor("#2a2a2a")
ax.grid(axis="y", color="#1e1e1e", linewidth=0.8)

plt.tight_layout()
plt.savefig(OUTPUT_FILE, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
plt.close()
print(f"Chart saved: {OUTPUT_FILE}")
```

**Substitutions:**
- `{CACHE_FILE_PATH}` → exact cache path from Step 1
- `{OUTPUT_PATH}` → `{workspace}/charts/pm_{slug}_{YYYYMMDD}.png`
- `{MARKET_TITLE}` → event title string (escape quotes with `\"` if needed)

Execute:
```
exec("python3 {workspace}/charts/plot_pm.py")
```

---

## Step 4 — Report

Tell the user:
1. The saved path (full absolute path so they can open it)
2. A one-line trend summary using the `summary` object:
   > _"Probability climbed from 34% to 61% over the past week, peaking at 68% on Feb 24."_

---

## Notes

- **Peak annotation:** Only shown when the probability range exceeds 10% — avoids cluttering
  flat charts.
- **Downsampled data:** If `downsampled: true` in the cache, 30 evenly-spaced points are
  sufficient. Full resolution isn't needed.
- **Multi-outcome markets:** `market_history` charts the first sub-market's Yes token. For a
  different outcome, use the standalone `history` command with a specific `token_id`.
- **matplotlib not installed?** → `exec("pip install matplotlib")`
