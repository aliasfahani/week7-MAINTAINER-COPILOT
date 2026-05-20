# Decisions

## Day 1

- Chosen GitHub repo: TBD.
- Why this repo: TBD after inspecting labels and closed issue volume.
- Label mapping: GitHub issue labels are mapped into `bug`, `feature`, `docs`, and `question` through `data/processed/label_mapping.json`.
- Split policy: time-based split. The oldest 70% of mapped issues are train, the next 15% are validation, and the newest 15% are test.
- Initial model choice: DistilBERT or a similar small transformer so training remains practical for a Week 7 project.
- RAG plan: use project docs plus resolved issues and maintainer answers. Start with clean chunking and pgvector, then add hybrid retrieval and reranking later if time allows.
- Chatbot architecture: one tool-calling LLM. Tools may call classifier, NER, summarization, RAG, and memory, but there will be no multi-agent system.
