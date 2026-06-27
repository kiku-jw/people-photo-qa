# Design Notes

This page records the product boundary that made the MVP publishable.

## Useful And Safe

- Deterministic image QA before expensive model review.
- Hash and consent ledgers for reproducible processing.
- Local-first analysis by default.
- Explicit nulls and abstentions when evidence is missing.
- Human-readable review flags instead of hidden rankings.
- Optional VLM review only for small, consented, human-requested batches.

## Risky And Out Of Scope

- Inferring ethnicity, race, national origin, or geotype from face images.
- Inferring actual health, diagnosis, biological age, fatigue, or lifestyle from face images.
- Inferring real personality, Big Five traits, honesty, aggression, reliability, intelligence, or moral character from face images.
- Using public-person or celebrity likeness as a machine target.
- Ranking people by skin lightness or presenting attractiveness as an objective score.
- Publishing tools that automate collection from closed/private directories.

## Implementation Principles

1. Keep outputs image-scoped: `visible`, `in_image`, `proxy`, `impression`, or `visual`.
2. Prefer local CV backends over remote VLM calls.
3. Cache model responses by input fingerprint.
4. Keep human review final.
5. Keep consent and audit records first-class.
6. Make unsafe outputs impossible through schema, prompt, docs, and UI labels.
