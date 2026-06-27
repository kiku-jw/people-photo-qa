# Visible-Cue Policy

Visible-cue fields are review aids. They describe what appears in the image under the captured lighting, pose, camera quality, and expression.

They must not be converted into claims about health, ethnicity, personality, morality, suitability, or identity.

## Allowed Cue Families

### Image Quality

- `quality_score`
- `quality_flags_json`
- blur, exposure, resolution, crop, and file-validity flags

### Presentation In The Image

- `perceived_freshness_in_image`
- `visible_freshness_proxy`
- `under_eye_shadowing_in_image`
- `under_eye_bag_prominence_in_image`
- `ocular_redness_in_image`
- `visible_blemish_like_elements`
- `visible_skin_evenness`

These fields may support a photo-quality review. They do not mean real health, sleep, diagnosis, or lifestyle.

### Expression And Camera Engagement

- `observable_expression`
- `image_expressiveness_proxy`
- `expression_readability_proxy`
- `gaze_directness_proxy`
- `camera_engagement_proxy`
- `approachability_impression_in_image`

These fields may describe the captured expression or image impression. They do not mean actual personality, confidence, honesty, sociability, anxiety, or aggression.

### Visual Brief Fit

- `visual_brief_fit`
- `geometric_symmetry_score`
- `soft_feature_index`
- `dataset_typicality_percentile`
- `appearance_descriptors_json`

These fields may support retrieval or visual organization inside a consented dataset. They must not be mapped to protected-trait labels or celebrity likeness.

## Required Naming Discipline

Keep `in_image`, `visible`, `visual`, `proxy`, or `impression` in field names where the value is not an objective image measurement.

Good:

- `visible_freshness_proxy`
- `image_expressiveness_proxy`
- `appearance_descriptors_json`

Bad:

- `real_health_score`
- `actual_extraversion`
- `ethnicity_from_face`
- `trustworthiness`
- `beauty_truth`

## Review Formula Guidance

If a downstream app needs a priority score, combine only consent-safe and image-scoped fields:

```text
review_priority =
  quality_score
  + visual_brief_fit
  + image_expressiveness_proxy
  + visible_freshness_proxy
  - review_flag_penalties
```

The formula must be configurable per project, visible to reviewers, and never the final decision-maker.

## UI Copy Rules

Avoid labels such as:

- "healthy"
- "unhealthy"
- "extroverted"
- "aggressive"
- "ethnic type"
- "beautiful"
- "trustworthy"

Use labels such as:

- "freshness impression in this image"
- "visible under-eye shadowing"
- "expression readability"
- "camera engagement"
- "visual brief fit"
- "needs human review"
