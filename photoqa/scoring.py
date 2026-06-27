"""Safe derived scoring for the MVP."""

from __future__ import annotations

from typing import Any


SCORE_VERSION = "mvp-safe-v1"


def derive_scores(cv_payload: dict[str, Any], quality_score: float | None, missing_backends: list[str]) -> tuple[dict[str, Any], list[str]]:
    reasons: list[str] = []
    score = 0.0 if quality_score is None else quality_score

    if score < 0.55:
        reasons.append("basic_image_quality_low")

    heavy_missing = [name for name in missing_backends if name in {"opencv", "mediapipe", "insightface", "deepface"}]
    if heavy_missing:
        reasons.append("heavy_cv_backends_missing")

    if not cv_payload.get("usable_for_basic_review", False):
        reasons.append("not_usable_for_basic_review")

    values: dict[str, Any] = {
        "visual_age_band": None,
        "apparent_age_estimate": None,
        "apparent_age_confidence": None,
        "perceived_freshness_in_image": None,
        "under_eye_shadowing_in_image": None,
        "under_eye_bag_prominence_in_image": None,
        "ocular_redness_in_image": None,
        "visible_blemish_like_elements": None,
        "visible_skin_evenness": None,
        "visible_freshness_proxy": None,
        "visual_brief_fit": None,
        "geometric_symmetry_score": None,
        "dataset_typicality_percentile": None,
        "soft_feature_index": None,
        "approachability_impression_in_image": None,
        "image_expressiveness_proxy": None,
        "expression_readability_proxy": None,
        "gaze_directness_proxy": None,
        "camera_engagement_proxy": None,
        "appearance_descriptors_json": None,
        "overall_review_priority": round(score, 4),
        "needs_human_review": bool(reasons),
    }
    return values, reasons
