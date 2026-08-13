---
name: llm-api-cost-monitoring
description: "Use when monitoring LLM API spend via cron watchdogs."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [cost, monitoring, deepseek, watchdog, cron, budget, spend]
    related_skills: [hermes-agent]
---

# LLM API Cost Monitoring

Monitor LLM provider API spend and alert the user when consumption crosses a
threshold (e.g. every ¥1) — with **ZERO LLM token cost**. Built and verified
for DeepSeek; the pattern adapts to any provider exposing a balance/usage endpoint.

## When to use
- User asks for notifications when provider spend crosses a threshold ("每消耗一块钱就通知我")
- Building cost/usage watchdogs for any API with a balance/usage endpoint
- Raising/lowering/debugging an existing spend alert

## Core pattern: `no_agent` cron watchdog
1. Write a standalone script (no LLM involved) that:
   - Queries the provider balance endpoint with a Bearer key
   - Compares against last-known balance from a state JSON
   - Accumulates positive deltas (consumption); top-up (negative delta) resets
   - **Prints** a notification only when accrued ≥ threshold, else prints NOTHING
2. Deploy as cron with `no_agent=True`:
   - Empty stdout → cron delivers nothing (silent tick)
   - Non-empty stdout → delivered verbatim to the target chat
   - The tick costs zero tokens — the alert system never becomes a cost itself

## Deployment steps
1. Write script to `HERMES_HOME/scripts/<name>.py` (UTF-8 safe: `sys.stdout.reconfigure(encoding="utf-8")`)
2. **Test manually BEFORE creating the cron** (see Verification)
3. Create job: `cronjob(action=create, no_agent=true, schedule="every 5m", script="<name>.py", name="...", deliver="origin")` — omit deliver to auto-route to the creating chat
4. Trigger once via `cronjob(action=run, job_id=...)` and confirm `last_status: ok` / `execution_success: true`

## Threshold accumulator logic (the crux)
- First run: record baseline only, no alert
- `delta = last_balance - current_balance` (positive = spend)
- `acc += delta`; top-up (negative delta) → `acc = 0`
- `acc >= threshold` → print alert with spent amount + current balance, reset `acc`, persist
- Transient API/network errors → exit 0 silently (never spam the user on blips)

## v2 dual-alert design (2026-08-13, for fast-burning models like deepseek-v4-pro)
Slow threshold-only alerts are TOO LATE when a model burns ¥1 in minutes. v2 adds a **rate alert**:
- `RATE_LIMIT` (0.3 元) on the per-tick delta → immediate "消耗过快" warning
- `RATE_COOLDOWN` (1800s) so a sustained burn alerts every 30 min instead of every 2 min
- Recommended cadence: cron every 2m (balance endpoint tolerates it), THRESHOLD 0.5 元
- Rate alert message includes ¥/hour projection: `delta * (3600 / poll_interval_seconds)`
- Both alerts increment `notices`; rate alert state key is `rate_alert_at` (epoch seconds)
- Falsify-test both paths: set `last_balance = real + 0.4` (rate path) and `accrued = 0.6` (threshold path), verify messages, then re-baseline with a real run

## Verification (do all before declaring done)
1. Run 1: state file created with real balance, silent exit
2. Run 2: balance unchanged → silent
3. Falsify: set `last_balance` in state JSON to `current + threshold + 0.5`, run → alert printed, `accrued` back to 0, `notices` incremented
4. `cronjob(action=run)` → scheduler path works

## Pitfalls
- **Cron env may lack the API key**: read env var, fall back to parsing `HERMES_HOME/.env` with regex `^DEEPSEEK_API_KEY\s*=\s*["']?([^"'\s]+)` — never print the value
- **Never echo secrets**: when locating keys in shell, grep NAMES only (`grep -oE '^[A-Z_]*DEEPSEEK[A-Z_]*=' file`)
- **Multi-currency**: providers return several `balance_infos`; filter by currency (CNY/RMB) before summing `total_balance`
- **Polling frequency**: balance endpoints are low-rate; every 5m is fine, don't hammer
- **State file location**: `HERMES_HOME/cron/<name>_state.json` (same dir as other cron state; survives restarts)
- **Top-up mid-run** resets the accumulator — that's intended behavior, don't "fix" it

## Support files
- `scripts/deepseek_cost_watch.py` — working, verified DeepSeek monitor (copy & adapt for other providers)
- `references/deepseek-balance-api.md` — DeepSeek balance endpoint contract & gotchas
