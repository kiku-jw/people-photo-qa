# Database Schema

The MVP uses SQLite. A later SaaS can migrate the same tables to Postgres.

## Core Tables

### `subjects`

One row per person in the consented photo dataset.

- `subject_id` text primary key
- `display_name` text nullable
- `created_at` text
- `notes` text nullable

### `consents`

Consent records tied to subjects and processing purposes.

- `consent_id` text primary key
- `subject_id` text
- `source` text
- `source_hash` text
- `allows_automated_processing` integer
- `allows_ai_review` integer
- `allows_face_embeddings` integer
- `allows_remote_vlm` integer
- `expires_at` text nullable
- `revoked_at` text nullable
- `created_at` text

### `photos`

One row per image file.

- `photo_id` text primary key
- `subject_id` text
- `consent_id` text
- `source_path` text
- `sha256` text unique
- `file_size_bytes` integer
- `width` integer nullable
- `height` integer nullable
- `mode` text nullable
- `created_at` text
- `ingest_status` text
- `ingest_error` text nullable

## Analysis Tables

### `cv_observations`

Raw or semi-raw deterministic observations.

- `observation_id` text primary key
- `photo_id` text
- `backend` text
- `backend_version` text
- `analysis_version` text
- `payload_json` text
- `quality_score` real nullable
- `quality_flags_json` text
- `created_at` text

### `scores`

Allowed product-facing scores and abstentions.

- `score_id` text primary key
- `photo_id` text
- `score_version` text
- `visual_age_band` text nullable
- `apparent_age_estimate` real nullable
- `apparent_age_confidence` real nullable
- `perceived_freshness_in_image` real nullable
- `under_eye_shadowing_in_image` real nullable
- `under_eye_bag_prominence_in_image` real nullable
- `ocular_redness_in_image` real nullable
- `visible_blemish_like_elements` real nullable
- `visible_skin_evenness` real nullable
- `visible_freshness_proxy` real nullable
- `visual_brief_fit` real nullable
- `geometric_symmetry_score` real nullable
- `dataset_typicality_percentile` real nullable
- `soft_feature_index` real nullable
- `approachability_impression_in_image` real nullable
- `image_expressiveness_proxy` real nullable
- `expression_readability_proxy` real nullable
- `gaze_directness_proxy` real nullable
- `camera_engagement_proxy` real nullable
- `appearance_descriptors_json` text nullable
- `overall_review_priority` real nullable
- `needs_human_review` integer
- `review_reasons_json` text
- `created_at` text

### `vlm_reviews`

Structured VLM outputs. This table should stay empty until remote review is explicitly enabled.

- `vlm_review_id` text primary key
- `photo_id` text
- `prompt_version` text
- `model` text
- `input_fingerprint` text
- `output_json` text
- `usage_json` text nullable
- `policy_flags_json` text
- `created_at` text

### `human_reviews`

Manual review and overrides.

- `human_review_id` text primary key
- `photo_id` text
- `reviewer_id` text
- `decision` text
- `notes` text nullable
- `override_json` text nullable
- `created_at` text

### `audit_log`

Append-only processing events.

- `audit_id` text primary key
- `event_type` text
- `subject_id` text nullable
- `photo_id` text nullable
- `payload_json` text
- `created_at` text

## Optional Self-Declared Metadata

Sensitive identity fields must be self-declared, optional, separately consented, and never inferred from photos. Recommended future table:

### `self_declared_attributes`

- `attribute_id` text primary key
- `subject_id` text
- `field_name` text
- `field_value` text
- `visibility` text
- `consent_id` text
- `created_at` text
- `updated_at` text nullable
- `deleted_at` text nullable

No fallback guessing is allowed when a field is absent.
