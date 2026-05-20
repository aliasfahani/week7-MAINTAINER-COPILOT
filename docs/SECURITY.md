# Security

Day 1 uses Vault dev mode only. Real secrets must not be committed.

The API reads development secrets from Vault through `app/infra/vault.py`. If Vault is unavailable, startup logs a clear warning so local development can continue while the missing dependency is visible.
