# Decisions

## Day 1

- Chosen GitHub repo: TBD.
- Why this repo: TBD after inspecting labels and closed issue volume.
- Label mapping: GitHub issue labels are mapped into `bug`, `feature`, `docs`, and `question` through `data/processed/label_mapping.json`.
- Split policy: time-based split. The oldest 70% of mapped issues are train, the next 15% are validation, and the newest 15% are test.
- Initial model choice: DistilBERT or a similar small transformer so training remains practical for a Week 7 project.
- RAG plan: use project docs plus resolved issues and maintainer answers. Start with clean chunking and pgvector, then add hybrid retrieval and reranking later if time allows.
- Chatbot architecture: one tool-calling LLM. Tools may call classifier, NER, summarization, RAG, and memory, but there will be no multi-agent system.

## Day 2

- Base classifier model: `distilbert-base-uncased`.
- Why this model: it is a small transformer with good Hugging Face support and is practical for a student laptop or small cloud instance.
- Classifier status: real fine-tuning and test evaluation scripts are implemented, but metrics remain TBD until real dataset splits are generated and training runs.
- Label mapping notes: mapping stays editable in `data/processed/label_mapping.json`; multi-label issues are warned about and collapsed to one label for this single-label classifier.
- Split policy: still time-based, with newest issues reserved for test.
- NER approach: Day 2 uses practical regex/rule-based extraction for files, versions, errors, function names, and code identifiers. This is intentionally simple and replaceable later.
- Summarization approach: Day 2 uses simple extractive summarization by keeping the first few meaningful sentences and capping length.
- API/model boundary: model inference lives in `model_server`; the main API calls it through `app/infra/model_client.py` and exposes service-level tool wrappers in `app/services/tool_service.py`.
- Known limitation: `/classify` returns a controlled 503 until `artifacts/classifier/` contains a trained model.
