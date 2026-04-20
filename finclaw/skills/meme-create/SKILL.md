---
name: meme-create
description: >
  Deploy a meme coin on pump.fun (Solana). Use this skill ONLY when the user explicitly wants
  to deploy, launch, create, or mint a meme token — not for browsing, searching, or brainstorming.
  Collect the required fields (name, symbol, description, image_path) before calling the meme tool.
  Do NOT trigger for passive meme coin questions or price checks.
---

# Meme Coin Creation

## Step 1 — Collect Required Fields

All four fields are required before calling `meme`. Collect any that are missing:

| Field | Example | Rules |
|-------|---------|-------|
| `name` | Moon Cat | Full token name |
| `symbol` | MCAT | Uppercase, max 10 chars, no spaces |
| `description` | A lunar explorer cat on Solana | 1–2 sentences, plain text |
| `image_path` | /Users/alice/mooncat.png | Absolute path to PNG/JPG/GIF on user's machine |

Optional (only ask if user mentions them):
- `twitter` — full URL to Twitter/X account
- `telegram` — full URL to Telegram group
- `website` — project website URL
- `buy_amount` — initial SOL buy-in (default: `0.01`)

If the user has no image, ask them to provide one before proceeding — `image_path` is mandatory.
Do not generate or fabricate image paths.

## Step 2 — Confirm Before Deploying

Summarise and ask for explicit confirmation:

> "Ready to deploy **Moon Cat (MCAT)** on pump.fun with a 0.01 SOL initial buy.
> Description: *A lunar explorer cat meme coin on Solana.*
> Logo: `/Users/alice/mooncat.png`
> Shall I proceed? This action is irreversible."

Only proceed after the user confirms.

## Step 3 — Call the Meme Tool

Pack all confirmed fields into a single query string:

```
meme(query="Create token: name='Moon Cat', symbol='MCAT', description='A lunar explorer cat meme coin on Solana', image_path='/Users/alice/mooncat.png', platform='pump.fun'")
```

With optional social links:
```
meme(query="Create token: name='Moon Cat', symbol='MCAT', description='A lunar explorer cat', image_path='/path/to/img.png', platform='pump.fun', twitter='https://x.com/mooncat', telegram='https://t.me/mooncat', buy_amount=0.05")
```

The inner agent handles environment checks (`check_env`) and deployment — do not add those steps.

## Step 4 — After Deployment

A successful result includes:

| Field | Description |
|-------|-------------|
| `mint` | Token contract address (Solana) |
| `pump_fun_url` | `https://pump.fun/<mint>` — share with community |
| `solscan_url` | Transaction link — proof of deployment |

Share both links with the user. Remind them that pump.fun tokens are highly speculative.

## Important Constraints

- **Platform:** pump.fun (Solana) only. BSC not available.
- **Irreversible:** Once deployed, the token cannot be undone.
- **Image required:** pump.fun rejects token creation without an image.
- **Symbol uniqueness:** pump.fun does not enforce unique symbols — duplicates are possible.
