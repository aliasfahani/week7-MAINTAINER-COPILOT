# Runbook

## Day 1 Local Flow

1. Copy `.env.example` to `.env`.
2. Start services with `make up`.
3. Seed Vault with `make seed-vault`.
4. Run migrations with `make migrate`.
5. Check API health at `http://localhost:8000/health`.
6. Check model server health at `http://localhost:8001/health`.
