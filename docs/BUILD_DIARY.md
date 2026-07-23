# Build Diary

## 2026-07-23 — Direct evaluation for visual retrieval

### Status

- artifact type: engineering note
- public-safe gate: passed; no images, reports, identities, or private dataset details
- review status: ready

### Checklist

- [x] Questions
- [x] Research / Evidence
- [x] Related Assets
- [x] Brief
- [x] Draft
- [x] Critique
- [x] Packaging
- [x] Publish Prep

### Questions

- angle: evaluate the actual retrieval objective instead of a convenient proxy
- audience: developers building human-reviewed visual organization tools
- takeaway: direct labels and top-of-list metrics are required before release
- exclusions: private examples, source collection, identity targets, and raw images

### Evidence

- the existing schema already separates visible-cue scores and review reasons
- the review importer supports human-calibrated benchmark rows
- the model policy already requires uncertainty and human review
- no private benchmark results are used as public evidence

### Related Assets

- `docs/model-policy.md`
- `docs/visible-cue-policy.md`
- `photoqa import-review`

### Brief

- explain direct target labels
- separate visual fit from measurement reliability
- use retrieval metrics and a holdout set
- keep local processing and abstention as defaults

### Draft And Review

- draft: `docs/visual-retrieval-evaluation.md`
- privacy review: passed
- unsupported performance claims: none
- packaging: linked from the README documentation index
