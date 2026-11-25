# Security Architecture — CardGuard AI

## 1. Payment Card Data Protection (No Raw PANs)
- CardGuard AI **never stores raw 13–19 digit Primary Account Numbers (PANs)**.
- Uploaded CSVs containing `card_number`, `pan`, `cc_num`, `credit_card`, or raw 13–19 digit values are automatically tokenized via `HMAC-SHA256` (`tok_<16-hex>`) using `API_KEY_SECRET`, retaining only `card_last4` for analyst display (`•••• 1234`).

## 2. CSV Upload Validation & Resource Limits
- Strictly enforces `.csv` extension, non-empty payload, `MAX_UPLOAD_MB` byte limit (default 10 MB), and `MAX_UPLOAD_ROWS` row limit (default 50,000).
- Requires valid positive numeric `amount` values and safely coerces/bounds optional fields.

## 3. Authentication & Secrets
- All secrets (`API_KEY_SECRET`, `DATABASE_URL`) are loaded from environment variables (`.env` is gitignored).
- Protected mutating endpoints enforce `X-API-Key` / `Authorization: Bearer` validation via constant-time `secrets.compare_digest` when `REQUIRE_AUTH=true`.

## 4. Safe Logging & Error Handling
- `RedactingFilter` in `app/core/logging.py` strips PAN-like digit sequences and credential headers from logs.
- Unhandled server exceptions return generic `500` JSON errors without stack traces or internal state leaks.
