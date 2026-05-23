# Security

Day 1 uses Vault dev mode only. Real secrets must not be committed.

The API reads development secrets from Vault through `app/infra/vault.py`. If Vault is unavailable, startup logs a clear warning so local development can continue while the missing dependency is visible.

## Day 4

- JWT signing key should come from Vault. A local fallback exists only so tests and demos can run before Vault is seeded.
- Passwords are hashed with PBKDF2; plaintext passwords are never stored.
- Admin routes use an explicit role check.
- Redaction removes common API keys, GitHub tokens, JWT-like strings, and password/token fields before logs or memory writes.
- Widget config uses an allowed-origin list. The Day 4 check is intentionally simple and should be paired with production CORS/CSP settings later.

## Day 5 Notes

- `.env` is ignored; only safe placeholders belong in `.env.example`.
- CI runs redaction tests.
- Public widget chat validates widget origin before calling chat.
- CORS is permissive for the local demo and should be narrowed before production.
