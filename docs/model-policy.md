# Model Policy

This project is for consented photo QA and visible image-cue annotation. Automated outputs must describe the image, not make claims about the person.

## Allowed Automatic Outputs

Allowed when the photo passes quality gates and the output includes uncertainty:

- `image_quality`
- `face_count`
- `yaw_deg`, `pitch_deg`, `roll_deg`
- `frontal_score`
- `eye_visibility`
- `gaze_label` as a composition descriptor
- `landmark_ratios`
- `geometric_symmetry_score`
- `dataset_typicality_percentile` for a clearly defined, consented dataset
- `appearance_color_profile`
- `visible_skin_descriptors`
- `observable_expression`
- `visual_age_band`
- `apparent_age_estimate`
- `apparent_age_confidence`
- `perceived_freshness_in_image`
- `under_eye_shadowing_in_image`
- `under_eye_bag_prominence_in_image`
- `ocular_redness_in_image`
- `visible_blemish_like_elements`
- `visible_skin_evenness`
- `visible_freshness_proxy`
- `visual_brief_fit`
- `soft_feature_index`
- `approachability_impression_in_image`
- `image_expressiveness_proxy`
- `expression_readability_proxy`
- `gaze_directness_proxy`
- `camera_engagement_proxy`
- `appearance_descriptors_json`

These are image-scoped descriptors or review aids. They are not factual judgments about the person.

## Human-Rater Calibration Required

These fields should only be used after human-rater calibration and should not be hard filters:

- `visual_age_band`
- `apparent_age_estimate`
- `apparent_age_confidence`
- `approachability_impression_in_image`
- `image_expressiveness_proxy`
- `visual_brief_fit`
- `soft_feature_index`
- `photo_presentation_quality`

Apparent-age outputs are not substitutes for direct labels for a different
retrieval objective. A task-specific visual brief must be evaluated against
human judgments of that brief, not against a generic age bucket or another
convenient proxy.

## Prohibited Automatic Outputs

Never infer or score these from photos:

- ethnicity, race, national origin, geotype, regional origin, religion, sexuality, politics, caste, or similar protected traits
- actual health, diagnosis, hormonal status, dehydration, disease, clinical fatigue, sleep debt, substance use, or medical status
- biological age, physiological age, mortality risk, longevity, or biomarker status
- actual Big Five traits, conscientiousness, introversion/extraversion as personality truth, reliability, or work ethic
- honesty, trustworthiness, criminality, aggression, danger, intelligence, deception, intent, or moral character
- attractiveness based on skin lightness
- similarity to a named public person by face embedding

## Public Reference Rule

Do not use a named public person as a machine target.

Allowed:

- abstract visual-brief descriptors
- style and lighting references that do not identify a person
- manually written moodboard text with no identity target

Not allowed:

- embedding distance to a public person
- nearest-celebrity matching
- "looks like X" machine targets
- optimizing a report by likeness to a public person

## Naming Rules

Use names that disclose uncertainty and scope:

- Use `apparent_age_estimate`, not `biological_age`.
- Use `perceived_freshness_in_image`, not `health_index`.
- Use `visible_freshness_proxy`, not `real_health_score`.
- Use `visible_skin_descriptors`, not `skin_health`.
- Use `image_expressiveness_proxy`, not `extraversion_score`.
- Use `expression_readability_proxy`, not `personality_openness`.
- Use `appearance_descriptors_json`, not `ethnicity_from_face` or `geotype_from_face`.
- Use `photo_presentation_quality`, not `conscientiousness`.
- Use `visual_brief_fit`, not `beauty_truth`.

## Remote VLM Rules

Before sending a photo to a remote VLM:

1. Confirm consent allows AI review and remote model processing.
2. Confirm the photo passes basic quality gates.
3. Send the smallest crop that preserves the review target.
4. Include CV facts and prohibited-inference rules in the prompt.
5. Require strict JSON output.
6. Cache the response by input fingerprint.
7. Send only human-requested, top-K, or ambiguous cases.

The VLM must abstain if evidence is weak.
