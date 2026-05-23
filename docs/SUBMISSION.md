# Submission

Project 7 - Ali Asfahani

Repo: https://github.com/aliasfahani/week7-MAINTAINER-COPILOT

Tag: v0.1.0-week7

Dataset: `pandas-dev/pandas` issues, N train / N val / N test = 1373 / 294 / 295

Classification - Fine-tuned: F1=TBD | LLM: F1=TBD

Deployment choice: FastAPI API + FastAPI model_server + Docker Compose - because it keeps app and ML inference separate and explainable.

Embedding model: sentence-transformers/all-MiniLM-L6-v2 supported, hash fallback default - chosen because MiniLM is small and pgvector-friendly while hash fallback keeps tests offline.

RAG - hit@5=TBD | MRR@10=TBD | Faithfulness=TBD | Answer relevancy=TBD

Long-term memory type: semantic

Tracing backend: structured logs with trace_id - chosen because it is simple and works without external services.

Widget bundle size: TBD KB gzipped

LLM: fallback mode documented; real provider/model TBD

README contains: ARCH.md, DECISIONS.md, RUNBOOK.md, EVALS.md, SECURITY.md
