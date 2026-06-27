# Publication Review

Date: 2026-06-27

Status: public-safe direction, pending owner/legal review before publishing.

Selected defaults:

- Public project name: People Photo QA.
- Python package name: `people-photo-qa`.
- Python import and CLI name: `photoqa`.
- License: MIT.

## Kept

- Local ingest and SQLite storage.
- Consent source tracking and file hashes.
- Basic Pillow image QA.
- CSV export for human review.
- Optional hooks for CV/VLM backends.
- Explicit policy against protected-trait, health, personality, and identity-likeness inference.

## Removed From Public Surface

- Closed-directory export workflow.
- Private collection notes and saved-session assumptions.
- Casting-specific shortlist language.
- Named-public-person aesthetic targets.
- Health/personality fact language.
- Ethnicity/geotype inference language.

## Remaining Publication Checklist

- Review dependency licenses for any optional pretrained models before enabling them.
- Keep `.agent/`, `.omx/`, `.playwright-cli/`, exports, databases, CSV reports, cookies, and raw photos out of git.
- Run tests and `git diff --check`.
- Have counsel review the README and model policy if this is used in hiring, casting, admissions, finance, healthcare, or any other regulated decision flow.

## External Risk References

These are not legal sign-off. They explain why the public version avoids biometric identity claims, protected-trait inference, and automated employment-style decisions.

- FTC: [Policy Statement on Biometric Information and Section 5 of the FTC Act](https://www.ftc.gov/legal-library/browse/policy-statement-federal-trade-commission-biometric-information-section-5-federal-trade-commission)
- EEOC: [Artificial Intelligence and Algorithmic Fairness Initiative](https://www.eeoc.gov/newsroom/eeoc-launches-initiative-artificial-intelligence-and-algorithmic-fairness)
- EEOC: [Artificial Intelligence and the ADA](https://www.eeoc.gov/eeoc-disability-related-resources/artificial-intelligence-and-ada)
- EU: [Regulation (EU) 2024/1689, Artificial Intelligence Act](https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=OJ:L_202401689)

## Recommended Public Positioning

Use:

> Local-first QA and visible-cue annotation for consented portrait photo datasets.

Avoid:

- automated ranking of people
- health or personality scoring
- ethnicity/geotype detection
- celebrity similarity matching
- beauty scoring
- sourcing or scraping photo databases
