# Decision Log

| Date | Decision | Why | Impact | Owner | Revisit When |
|---|---|---|---|---|---|
| 2026-03-02 | Use English keys for internal categories and Portuguese labels for display | Keep code/data stable while making UI natural for Brazilian users | DB/enrichment payloads use stable English `snake_case`; Streamlit/UI shows pt-BR labels | Team | If product expands to multi-language UI or external category integrations |
| 2026-03-02 | Item naming source of truth: `raw_name` (invoice truth) + `normalized_name` (deterministic normalization); AI naming stays in `item_enrichment` | Preserve auditability while enabling grouping/search independent from AI | Core `items` remains stable; AI outputs are append-only enrichments | Team | If deterministic normalization proves insufficient for matching quality |
| 2026-03-02 | UI stack for spike phase is Streamlit; Django deferred | Optimize for speed while scope is still exploratory | Fast local viewer; migration criteria documented for future framework change | Team | If multi-user auth/complex workflows become required |
