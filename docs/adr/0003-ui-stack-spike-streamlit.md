# ADR 0003: UI Stack Decision for Spike Phase

- Status: Accepted
- Date: 2026-03-02

## Context

The product is in spike mode and needs a fast way to inspect invoices, items, and enrichments with minimal engineering overhead.

## Decision

Use Streamlit as the UI stack for the spike phase.

- Build and maintain a minimal viewer in Streamlit
- Reuse current SQLite storage and existing Python modules
- Defer migration to Django until product scope stabilizes

## Consequences

- Pros:
  - Fast implementation and iteration speed
  - Minimal architecture changes while validating product direction
  - Good enough for internal/operator workflows
- Cons:
  - Limited control for complex app patterns
  - Not ideal for long-term multi-user production architecture

## Migration Trigger

Re-evaluate Django (or another full framework) when at least one of these becomes true:

- Need authentication/authorization and multi-user workflows
- Need robust CRUD/admin workflows beyond simple inspection
- Need stronger domain model constraints and long-term maintainability

## Alternatives Considered

- Django now: better long-term structure, too heavy for current spike scope
- No UI: slows feedback loops and data validation

