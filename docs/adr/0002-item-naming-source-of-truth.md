# ADR 0002: Source of Truth for Item Naming

- Status: Accepted
- Date: 2026-03-02

## Context

NFC-e item names are often abbreviated and inconsistent. The product needs stable naming for storage, display, and later analytics.

## Decision

Use two naming layers in `items`:

- `raw_name`: exact product string extracted from the invoice (immutable invoice truth)
- `normalized_name`: deterministic normalized value derived from `raw_name` for grouping/search

AI-derived naming/enrichment must be stored in `item_enrichment` and must not overwrite invoice truth fields.

## Consequences

- Pros:
  - Preserves original invoice data for audit/debugging
  - Enables deterministic grouping without requiring AI
  - Keeps AI outputs optional and evolvable by stage/version
- Cons:
  - Some duplication between `raw_name` and `normalized_name`
  - Requires explicit logic for which field to use in each feature

## Alternatives Considered

- Single `name` field only: too weak for traceability and grouping
- AI canonical name directly in `items`: ties core storage to model behavior and version drift

