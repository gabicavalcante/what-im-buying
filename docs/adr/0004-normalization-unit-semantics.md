# ADR 0004: Simplified Normalization Contract and Unit Semantics

- Status: Accepted
- Date: 2026-03-03

## Context

AI normalization output has shown inconsistent unit values such as `un`, `unit`, `count`, and mixed casing.
The previous schema also had optional fields (`size_value`, `size_unit`, `pack_count`) that added noise in spike phase.

## Decision

Simplify normalization output to these fields only:

- `raw_name`
- `canonical_name`
- `brand`
- `unit_type`
- `confidence`
- `needs_review`

Transaction quantity stays in invoice `items` (`quantity`).
Invoice item unit also stays in `items.unit_type` parsed from NFC-e (`UN:` field in `tabResult`).

Normalize AI `unit_type` to canonical SEFAZ-like unit codes (uppercase), including:

- `KG`, `UN`, `LT`, `CX`, `PC`, `FR`, `BJ`, `TP`, `BR`, `CP`, `GF`, `PT`, `SH`, `CJ`, `VD`

Common aliases are coerced to canonical values:

- `unit`, `units`, `unidade`, `unidades`, `und` -> `UN`
- `lt`, `litro`, `litros` -> `LT`
- Unknown values -> `null` and `needs_review=true`

## Consequences

- Pros:
  - Smaller, clearer normalization payload
  - Stable unit values aligned with invoice usage
  - Better comparability and lower downstream ambiguity
  - Lower variance across AI runs
- Cons:
  - Removes package-size modeling for now (explicitly deferred)

## Alternatives Considered

- Keep package-size fields in spike phase: too noisy and low-value now
- Accept raw model units as-is: high inconsistency and harder analytics
