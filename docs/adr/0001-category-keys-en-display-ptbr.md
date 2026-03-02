# ADR 0001: Category Keys in English, Display Labels in Portuguese

- Status: Accepted
- Date: 2026-03-02

## Context

The product parses Brazilian NFC-e invoices. We need category names for storage, enrichment payloads, and UI display.

## Decision

Use:

- Internal category keys: English `snake_case` (for code, DB, and AI payloads)
- Display labels: Portuguese (pt-BR) for user-facing interfaces

## Consequences

- Pros:
  - Stable internal representation for engineering and integrations
  - Natural UX language for Brazilian users
  - Easier future localization
- Cons:
  - Requires a mapping layer (`key -> pt-BR label`) in UI/reporting

## Alternatives Considered

- Portuguese for everything: better local readability, worse long-term interoperability
- English for everything: simpler implementation, poorer local UX

