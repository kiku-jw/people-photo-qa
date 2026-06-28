# People Photo QA

Local-first tooling for consented portrait photo datasets. The MVP inventories image folders, records consent metadata, computes basic image quality checks, stores abstention-friendly score rows in SQLite, and exports a review CSV.

The public scope is deliberately narrow: this is a photo QA and visible-cue annotation tool, not a system for deciding who a person is, how healthy they are, what ethnicity they have, or what their personality is.

## Quick Start

```bash
python3 -m photoqa init-db --db photoqa.sqlite
python3 -m photoqa ingest --db photoqa.sqlite --photos-dir /path/to/photos --consent-source "signed_consent_v1"
python3 -m photoqa analyze --db photoqa.sqlite
python3 -m photoqa import-review --db photoqa.sqlite --input review.json
python3 -m photoqa export-report --db photoqa.sqlite --out report.csv
```

When installed as a package, the CLI entrypoint is:

```bash
photoqa --help
```

Run the local smoke tests:

```bash
python3 -m unittest
```

## What It Does

- Creates a SQLite schema for subjects, consent records, photos, deterministic CV observations, derived review fields, optional VLM reviews, human reviews, and audit logs.
- Recursively ingests `.jpg`, `.jpeg`, `.png`, `.webp`, `.bmp`, and `.tif` files.
- Records SHA-256 hash, file size, dimensions, color mode, ingest status, and consent source hash.
- Computes basic image quality flags with Pillow.
- Exports CSV rows that can be reviewed, filtered, and audited by a human.
- Leaves optional hooks for OpenCV, MediaPipe, InsightFace, DeepFace, and VLM review without requiring them for the MVP.

## Safety Boundary

This repo should not infer or score these from photos:

- ethnicity, race, national origin, religion, sexuality, politics, caste, or similar protected traits
- actual health, diagnosis, biological age, fatigue, sleep history, substance use, or medical status
- real Big Five traits, introversion/extraversion, honesty, trustworthiness, aggression, intelligence, or moral character
- identity similarity to a named public person or celebrity
- attractiveness based on skin lightness

Allowed outputs must stay image-scoped: quality, pose, visibility, apparent visual cues, uncertainty, and human-review flags. See [Model policy](docs/model-policy.md).

## Visible-Cue Fields

The schema includes nullable fields for future richer review:

- `perceived_freshness_in_image`
- `visible_freshness_proxy`
- `under_eye_shadowing_in_image`
- `under_eye_bag_prominence_in_image`
- `visible_blemish_like_elements`
- `visible_skin_evenness`
- `visual_brief_fit`
- `geometric_symmetry_score`
- `image_expressiveness_proxy`
- `expression_readability_proxy`
- `gaze_directness_proxy`
- `camera_engagement_proxy`

The current MVP does not fill these with model claims. It stores `null` until a validated local CV or explicitly enabled VLM backend is added. That is intentional: missing evidence should remain missing evidence.

## Import Benchmark Reviews

Use `import-review` to load a human-reviewed or VLM-reviewed visible-cue benchmark JSON into the latest reportable scores:

```bash
python3 -m photoqa import-review --db photoqa.sqlite --input review.json
python3 -m photoqa export-report --db photoqa.sqlite --out report.csv
```

Minimal JSON shape:

```json
{
  "reviews": [
    {
      "subject_id": "person_001",
      "scores": {
        "visible_freshness_proxy": 8.5,
        "visual_brief_fit": 8.0,
        "image_expressiveness_proxy": 6.5,
        "expression_readability_proxy": 8.0,
        "gaze_directness_proxy": 8.0,
        "camera_engagement_proxy": 7.0,
        "appearance_descriptors_json": {
          "pose": ["frontal"],
          "lighting": ["even"]
        }
      },
      "review_reasons": ["manual_visible_cue_benchmark"]
    }
  ]
}
```

The importer rejects known unsafe keys such as `ethnicity_from_face`, `real_health_score`, `actual_extraversion`, `trustworthiness`, and `celebrity_similarity`.

## Optional Backends

Install heavier backends only after checking Python version support and model licenses:

- `opencv-python`: blur, exposure, crop, and preprocessing checks.
- `mediapipe`: landmarks, blendshapes, pose and geometry descriptors.
- `insightface`: face detection/alignment and embeddings for dedup/retrieval, subject to pretrained model license review.
- `deepface`: research baseline only; do not treat attribute outputs as final evidence.
- `openai`: optional VLM client for reviewed top-K or ambiguous images through OpenAI-compatible APIs.

Use Python 3.11 or 3.12 for the full CV stack if wheels lag newer Python versions.

## Docs

- [Architecture](docs/architecture.md)
- [Database schema](docs/database-schema.md)
- [Model policy](docs/model-policy.md)
- [Visible-cue policy](docs/visible-cue-policy.md)
- [Publication review](docs/publication-review.md)
- [VLM prompt](prompts/vlm-photo-reviewer.md)

## Status

MVP. Local ingest, basic analysis, and CSV export are implemented and tested. Remote VLM review and heavy CV backends are not enabled by default.

## License

MIT. See [LICENSE](LICENSE).
