---
name: cron
description: >
  Schedule repeating reminders or autonomous recurring tasks (e.g. "check AAPL every hour",
  "remind me to take a break every 20 minutes", "run a portfolio summary every morning at 8am").
  Use this skill when the user asks to schedule, repeat, automate, remind, or set an alarm for
  anything time-based. Supports one-time ("at") and recurring ("every") schedules.
---

# Cron

Use the `cron` tool to schedule reminders or recurring agent tasks.

## Two Job Types

| Type | Behaviour |
|------|-----------|
| `reminder` | Sends the `message` text directly to the user as-is. |
| `task` | Treats `message` as a task — the agent re-runs it each time and sends the result. |

Always default to `type="task"` when the user says "check X", "run X", or "do X" on a schedule.
Use `type="reminder"` only when they want a simple text nudge (e.g. "remind me to drink water").

## Schedule Parameters (pick one)

| Field | Example | When to use |
|-------|---------|-------------|
| `every_seconds` | `1200` | Repeating intervals |
| `cron_expr` | `"0 8 * * *"` | Specific times, weekdays |
| `at` | ISO datetime string | One-time, fires once then auto-deletes |

**Timezone:** `cron_expr` runs in the server's local timezone. If the user specifies a timezone,
note it in the message text (e.g. "9am ET") — the cron expression should be adjusted accordingly.
Use the current time shown in the system prompt to compute the correct offset.

## Common Expressions

| User says | Parameters |
|-----------|------------|
| every 20 minutes | `every_seconds: 1200` |
| every hour | `every_seconds: 3600` |
| every day at 8am | `cron_expr: "0 8 * * *"` |
| weekdays at 5pm | `cron_expr: "0 17 * * 1-5"` |
| at a specific time | `at: <ISO datetime — compute from current time in system prompt>` |
| every 15 min during market hours | `cron_expr: "*/15 9-16 * * 1-5"` |

## Actions

```
cron(action="add",    message="...", every_seconds=600, type="task")
cron(action="add",    message="Drink water!", every_seconds=1200, type="reminder")
cron(action="add",    message="...", cron_expr="0 9 * * 1-5", type="task")
cron(action="add",    message="...", at="<ISO datetime>")   # one-time
cron(action="list")
cron(action="remove", job_id="abc123")
```

## After Scheduling

Always confirm back to the user:
> "✅ Scheduled: I'll check AAPL's price every hour and let you know."

Include the job ID from the response so they can remove it later.
