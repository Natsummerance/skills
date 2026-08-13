# DeepSeek Balance API — contract & gotchas

Verified 2026-08 against the live endpoint.

## Endpoint
```
GET https://api.deepseek.com/user/balance
Authorization: Bearer <DEEPSEEK_API_KEY>
Accept: application/json
```
No query params. No official usage-detail/history API exists — only balance.
**Delta tracking between polls is the only way to measure spend.**

## Response shape
```json
{
  "is_available": true,
  "balance_infos": [
    {
      "currency": "CNY",
      "total_balance": "97.28",
      "granted_balance": "0.00",
      "topped_up_balance": "97.28"
    }
  ]
}
```
- `total_balance` = granted + topped_up; sum the one you care about
- Multiple `balance_infos` possible (multi-currency) → filter by `currency`
  before summing; don't sum across currencies
- Values are strings, not numbers — `float()` them

## Rate & behavior
- Low-rate endpoint; 5-minute polling is safe, don't hammer it
- Returns HTTP error codes on auth failure (401) — script should treat
  network/HTTP errors as transient and stay silent
- Top-ups appear as a positive jump in `total_balance`

## Key location
`DEEPSEEK_API_KEY` lives in `<HERMES_HOME>/.env`. Cron script env may not
carry it — the watchdog script falls back to parsing the `.env` file.
Never print the key value.
