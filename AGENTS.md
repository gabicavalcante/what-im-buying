# AGENTS.md

This document defines engineering standards and collaboration rules for contributors and coding agents working in this repository.

## Scope and Priorities

- Scope: `what-im-buying` (NFC-e parsing, enrichment, categorization, and local viewer).
- Current product phase: spike/validation.
- Priority order:
1. Correctness and traceability of invoice/enrichment data.
2. Simple, testable, incremental changes.
3. Clear contracts for AI input/output.
4. Readable code with minimal incidental complexity.

## Code Style and Python Standards

- Follow PEP 8, PEP 20, PEP 585, and local linting rules (`.flake8` when present).
- Use explicit type hints for public functions and non-trivial internal functions.
- Prefer built-in generic types:
  - `list[str]`, `dict[str, int]`, `set[str]`
  - Avoid `List`, `Dict`, `Set` from `typing` for new code.
- Do not add `from __future__ import annotations` in new or edited files.
- Keep code declarative and direct; avoid unnecessary abstractions.
- Avoid deep nesting. Prefer guard clauses and early returns.

## Comments and Docstrings

- Avoid redundant comments.
- Add comments only for non-obvious behavior, edge cases, or constraints.
- Focus comments on **why**, not **what**.
- Docstrings are optional and should only be added when they provide extra context:
  - non-obvious behavior
  - side effects
  - constraints and assumptions

## Logging and Observability

- Use module-level loggers (`LOGGER = logging.getLogger(__name__)`) in code paths with branching/guard clauses.
- When returning early from guard clauses, log with `LOGGER.info` and useful context:
  - invoice IDs
  - item IDs
  - relevant payload identifiers (never secrets)
- Use `LOGGER.exception` for unexpected exceptions that are handled/re-raised.

## Architecture Rules (Current State)

- Keep modules focused by responsibility:
  - parsing in parser modules
  - persistence in storage modules
  - AI contracts/transforms in AI modules
  - presentation in CLI/UI modules
- Prefer small, function-based units over premature class hierarchies.
- Keep side effects localized; pass explicit data structures between layers.
- Avoid introducing architectural layers that are not yet used in practice.

## Architecture Direction (Future)

- Target architecture can evolve toward explicit use-case/service boundaries once scope stabilizes.
- Until then, prioritize clarity, testability, and low-complexity module boundaries.

## Data Modeling and Persistence

- Core invoice/item fields are source-of-truth data.
- Enrichment outputs are persisted as JSON in `item_enrichment.output_json`.
- Enrichment payload shapes must be represented by dataclasses in `models.py`.
- At persistence boundaries, serialize dataclasses explicitly (e.g., `asdict`).
- Internal category key is English (`snake_case`); UI labels are pt-BR via mapping.

## AI and Prompt Guidelines

- All AI commands must enforce a strict JSON output contract.
- Prompts must specify:
  - required schema
  - allowed enum values (e.g., category keys)
  - confidence range and uncertainty behavior
- Validate and coerce AI output before persistence.
- If AI output is malformed, fail with explicit error instead of silently guessing.
- Never store secrets in prompts or logs.

## Testing Expectations

- Add or update tests for each behavior change.
- Prefer focused tests close to changed behavior.
- For spike features, at minimum include:
  - parsing correctness checks
  - enrichment serialization/persistence checks
  - category or normalization contract checks
- Keep tests deterministic; avoid external network calls in unit tests.

## UI/Streamlit Rules

- UI should be inspection-first: simple tables, filters, and summaries.
- Avoid duplicating equivalent data in multiple tables.
- Compute localized labels in UI from stable internal keys.
- Keep formatting user-friendly (e.g., BRL currency `R$`).

## Workflow and Change Management

- Make small, reversible changes.
- Keep commits scoped and descriptive (`type(scope): summary`).
- Update docs/README when CLI or behavior changes.
- Record important architecture/product decisions in `docs/decision-log.md` and ADRs in `docs/adr/`.

## Security and Privacy

- Do not commit `.env`, credentials, or sensitive tokens.
- Treat invoice data as sensitive; avoid exposing personal identifiers in logs.
- Prefer local processing and least-privilege handling.

## Repository Structure Reference

- See `README.md` for current execution flow and commands.
- Main modules:
  - parser: `src/what_im_buying/parser.py`
  - storage: `src/what_im_buying/storage.py`
  - AI: `src/what_im_buying/ai.py`
  - categories: `src/what_im_buying/categories.py`
  - CLI: `src/what_im_buying/cli.py`
  - viewer: `src/what_im_buying/viewer.py`
