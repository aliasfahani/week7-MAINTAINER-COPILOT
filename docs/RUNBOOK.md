# Runbook

## Day 1 Local Flow

1. Copy `.env.example` to `.env`.
2. Start services with `make up`.
3. Seed Vault with `make seed-vault`.
4. Run migrations with `make migrate`.
5. Check API health at `http://localhost:8000/health`.
6. Check model server health at `http://localhost:8001/health`.

## Day 4 Local Flow

Run migrations and seed an admin:

```bash
make migrate
make seed-admin
```

Default admin:

```text
admin@example.com / admin123
```

Run Streamlit:

```bash
make streamlit
```

Run the React widget dev server:

```bash
make widget-dev
```

Run the demo host page:

```bash
make host
```

Embed snippet:

```html
<script src="http://localhost:8000/widget.js" data-widget-id="demo-widget"></script>
```
