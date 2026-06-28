"""High-level MVP workflow."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

from photoqa import __version__
from photoqa.backends import available_backend_names, backend_status, missing_backend_names
from photoqa.db import (
    connect,
    init_db,
    insert_audit,
    insert_cv_observation,
    insert_photo,
    insert_score,
    json_dumps,
    list_photos_for_analysis,
    report_rows,
    upsert_consent,
    upsert_subject,
)
from photoqa.imaging import basic_quality, inspect_image, iter_image_paths, sha256_file
from photoqa.scoring import SCORE_VERSION, derive_scores


ANALYSIS_VERSION = "pillow-basic-v1"

SCORE_FIELDNAMES = [
    "visual_age_band",
    "apparent_age_estimate",
    "apparent_age_confidence",
    "perceived_freshness_in_image",
    "under_eye_shadowing_in_image",
    "under_eye_bag_prominence_in_image",
    "ocular_redness_in_image",
    "visible_blemish_like_elements",
    "visible_skin_evenness",
    "visible_freshness_proxy",
    "visual_brief_fit",
    "geometric_symmetry_score",
    "dataset_typicality_percentile",
    "soft_feature_index",
    "approachability_impression_in_image",
    "image_expressiveness_proxy",
    "expression_readability_proxy",
    "gaze_directness_proxy",
    "camera_engagement_proxy",
    "appearance_descriptors_json",
    "overall_review_priority",
    "needs_human_review",
]

SCORE_1_TO_10_FIELDS = {
    "perceived_freshness_in_image",
    "under_eye_shadowing_in_image",
    "under_eye_bag_prominence_in_image",
    "ocular_redness_in_image",
    "visible_blemish_like_elements",
    "visible_skin_evenness",
    "visible_freshness_proxy",
    "visual_brief_fit",
    "geometric_symmetry_score",
    "dataset_typicality_percentile",
    "soft_feature_index",
    "approachability_impression_in_image",
    "image_expressiveness_proxy",
    "expression_readability_proxy",
    "gaze_directness_proxy",
    "camera_engagement_proxy",
}

PROHIBITED_REVIEW_KEYS = {
    "ethnicity",
    "ethnicity_from_face",
    "race",
    "race_from_face",
    "geotype",
    "geotype_from_face",
    "actual_health",
    "real_health_score",
    "health_index",
    "biological_age",
    "personality",
    "actual_extraversion",
    "actual_conscientiousness",
    "trustworthiness",
    "honesty",
    "hidden_aggression",
    "celebrity_similarity",
    "beauty_truth",
}


def stable_text_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def clean_subject_id(value: str) -> str:
    cleaned = []
    for character in value.strip():
        if character.isalnum() or character in {"-", "_"}:
            cleaned.append(character)
        else:
            cleaned.append("_")
    subject_id = "".join(cleaned).strip("_")
    if subject_id:
        return subject_id
    return "unknown_subject"


def subject_id_for_path(path: Path, root: Path, mode: str) -> str:
    if mode == "parent":
        return clean_subject_id(path.parent.name)
    if mode == "relative":
        relative = path.relative_to(root)
        return clean_subject_id(str(relative.with_suffix("")))
    return clean_subject_id(path.stem)


def consent_id_for(subject_id: str, source_hash: str) -> str:
    return f"consent_{subject_id}_{source_hash[:12]}"


def review_items_from_json(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict) and isinstance(value.get("reviews"), list):
        items = value["reviews"]
    elif isinstance(value, list):
        items = value
    elif isinstance(value, dict):
        items = [value]
    else:
        raise ValueError("review JSON must be an object, an array, or an object with a reviews array")

    reviews: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("each review must be a JSON object")
        reviews.append(item)
    return reviews


def as_optional_float(field: str, value: Any) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        raise ValueError(f"{field} must be a number, not a boolean")
    try:
        number = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{field} must be numeric") from error
    if field in SCORE_1_TO_10_FIELDS and not 0 <= number <= 10:
        raise ValueError(f"{field} must be between 0 and 10")
    if field == "overall_review_priority" and not 0 <= number <= 1:
        raise ValueError("overall_review_priority must be between 0 and 1")
    if field == "apparent_age_confidence" and not 0 <= number <= 1:
        raise ValueError("apparent_age_confidence must be between 0 and 1")
    return number


def collect_review_values(review: dict[str, Any]) -> dict[str, Any]:
    scores = review.get("scores", {})
    if scores is None:
        scores = {}
    if not isinstance(scores, dict):
        raise ValueError("scores must be an object when present")

    unsafe_keys = PROHIBITED_REVIEW_KEYS.intersection(review.keys()) | PROHIBITED_REVIEW_KEYS.intersection(scores.keys())
    if unsafe_keys:
        joined = ", ".join(sorted(unsafe_keys))
        raise ValueError(f"review contains prohibited keys: {joined}")

    unknown_score_keys = set(scores) - set(SCORE_FIELDNAMES)
    if unknown_score_keys:
        joined = ", ".join(sorted(unknown_score_keys))
        raise ValueError(f"review contains unknown score keys: {joined}")

    values: dict[str, Any] = {}
    for field in SCORE_FIELDNAMES:
        raw_value = scores[field] if field in scores else review.get(field)
        if field == "appearance_descriptors_json":
            if raw_value is None or raw_value == "":
                values[field] = None
            elif isinstance(raw_value, str):
                values[field] = raw_value
            else:
                values[field] = json_dumps(raw_value)
        elif field in {"visual_age_band"}:
            values[field] = None if raw_value is None else str(raw_value)
        elif field == "needs_human_review":
            values[field] = bool(raw_value) if raw_value is not None else False
        elif field in SCORE_1_TO_10_FIELDS or field in {
            "apparent_age_estimate",
            "apparent_age_confidence",
            "overall_review_priority",
        }:
            values[field] = as_optional_float(field, raw_value)
        else:
            values[field] = raw_value
    return values


def compute_review_priority(values: dict[str, Any], quality_score: float | None) -> float:
    if values.get("overall_review_priority") is not None:
        return round(float(values["overall_review_priority"]), 4)

    weighted_components: list[tuple[float, float]] = []
    if quality_score is not None:
        weighted_components.append((0.35, float(quality_score)))

    score_weights = {
        "visual_brief_fit": 0.20,
        "visible_freshness_proxy": 0.15,
        "image_expressiveness_proxy": 0.12,
        "expression_readability_proxy": 0.08,
        "gaze_directness_proxy": 0.05,
        "camera_engagement_proxy": 0.05,
    }
    for field, weight in score_weights.items():
        value = values.get(field)
        if value is not None:
            weighted_components.append((weight, float(value) / 10.0))

    if not weighted_components:
        return 0.0
    total_weight = sum(weight for weight, _ in weighted_components)
    return round(sum(weight * value for weight, value in weighted_components) / total_weight, 4)


def init_database(db_path: Path) -> None:
    conn = connect(db_path)
    try:
        init_db(conn)
        insert_audit(conn, "init_db", {"photoqa_version": __version__})
        conn.commit()
    finally:
        conn.close()


def ingest_directory(
    db_path: Path,
    photos_dir: Path,
    consent_source: str,
    subject_id_mode: str,
    allows_remote_vlm: bool,
) -> dict[str, int]:
    conn = connect(db_path)
    source_hash = stable_text_hash(consent_source)
    inserted = 0
    skipped = 0
    errors = 0
    try:
        init_db(conn)
        for path in iter_image_paths(photos_dir):
            file_hash = sha256_file(path)
            existing = conn.execute("select photo_id from photos where sha256 = ?", (file_hash,)).fetchone()
            if existing is not None:
                skipped += 1
                continue

            subject_id = subject_id_for_path(path, photos_dir, subject_id_mode)
            consent_id = consent_id_for(subject_id, source_hash)
            info = inspect_image(path)
            file_size = path.stat().st_size
            upsert_subject(conn, subject_id, subject_id)
            upsert_consent(conn, consent_id, subject_id, consent_source, source_hash, allows_remote_vlm)

            status = "ok" if info["ok"] else "error"
            if not info["ok"]:
                errors += 1
            photo_id = insert_photo(
                conn,
                subject_id,
                consent_id,
                path,
                file_hash,
                file_size,
                info["width"],
                info["height"],
                info["mode"],
                status,
                info["error"],
            )
            insert_audit(
                conn,
                "ingest_photo",
                {
                    "source_path": str(path),
                    "sha256": file_hash,
                    "status": status,
                },
                subject_id=subject_id,
                photo_id=photo_id,
            )
            inserted += 1
        conn.commit()
    finally:
        conn.close()
    return {"inserted": inserted, "skipped": skipped, "errors": errors}


def analyze_photos(db_path: Path, limit: int | None, force: bool) -> dict[str, int]:
    conn = connect(db_path)
    analyzed = 0
    try:
        init_db(conn)
        status = backend_status()
        available = available_backend_names()
        missing = missing_backend_names()
        rows = list_photos_for_analysis(conn, limit, force)
        pillow_version = status["pillow"]["version"] or "unknown"
        for row in rows:
            quality = basic_quality(row["width"], row["height"], row["mode"])
            payload = {
                "analysis_version": ANALYSIS_VERSION,
                "photoqa_version": __version__,
                "available_backends": available,
                "missing_backends": missing,
                "width": row["width"],
                "height": row["height"],
                "mode": row["mode"],
            }
            payload.update(quality["payload"])
            insert_cv_observation(
                conn,
                row["photo_id"],
                "pillow_basic",
                pillow_version,
                ANALYSIS_VERSION,
                payload,
                quality["quality_score"],
                quality["quality_flags"],
            )
            values, review_reasons = derive_scores(payload, quality["quality_score"], missing)
            insert_score(conn, row["photo_id"], SCORE_VERSION, values, review_reasons)
            insert_audit(
                conn,
                "analyze_photo",
                {
                    "analysis_version": ANALYSIS_VERSION,
                    "quality_score": quality["quality_score"],
                    "quality_flags": quality["quality_flags"],
                    "review_reasons": review_reasons,
                },
                subject_id=row["subject_id"],
                photo_id=row["photo_id"],
            )
            analyzed += 1
        conn.commit()
    finally:
        conn.close()
    return {"analyzed": analyzed}


def import_benchmark_reviews(db_path: Path, input_path: Path, score_version: str) -> dict[str, int]:
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    reviews = review_items_from_json(payload)
    conn = connect(db_path)
    imported = 0
    missing = 0
    try:
        init_db(conn)
        for review in reviews:
            subject_id = review.get("subject_id")
            if not subject_id:
                raise ValueError("each review must include subject_id")
            row = conn.execute(
                """
                select
                  p.photo_id,
                  p.subject_id,
                  latest.quality_score
                from photos p
                left join cv_observations latest
                  on latest.observation_id = (
                    select observation_id
                    from cv_observations
                    where photo_id = p.photo_id
                    order by created_at desc
                    limit 1
                  )
                where p.subject_id = ?
                order by p.created_at desc
                limit 1
                """,
                (str(subject_id),),
            ).fetchone()
            if row is None:
                missing += 1
                continue

            values = collect_review_values(review)
            values["overall_review_priority"] = compute_review_priority(values, row["quality_score"])

            review_reasons_raw = review.get("review_reasons", [])
            if review_reasons_raw is None:
                review_reasons_raw = []
            if not isinstance(review_reasons_raw, list):
                raise ValueError("review_reasons must be an array when present")
            review_reasons = [str(reason) for reason in review_reasons_raw]

            insert_score(conn, row["photo_id"], score_version, values, review_reasons)
            insert_audit(
                conn,
                "import_benchmark_review",
                {
                    "input_path": str(input_path),
                    "score_version": score_version,
                    "overall_review_priority": values["overall_review_priority"],
                },
                subject_id=row["subject_id"],
                photo_id=row["photo_id"],
            )
            imported += 1
        conn.commit()
    finally:
        conn.close()
    return {"imported": imported, "missing": missing}


def export_report(db_path: Path, out_path: Path, limit: int | None) -> int:
    conn = connect(db_path)
    try:
        rows = report_rows(conn, limit)
    finally:
        conn.close()

    fieldnames = [
        "photo_id",
        "subject_id",
        "source_path",
        "sha256",
        "width",
        "height",
        "quality_score",
        "quality_flags_json",
        "visual_age_band",
        "apparent_age_estimate",
        "apparent_age_confidence",
        "perceived_freshness_in_image",
        "under_eye_shadowing_in_image",
        "under_eye_bag_prominence_in_image",
        "ocular_redness_in_image",
        "visible_blemish_like_elements",
        "visible_skin_evenness",
        "visible_freshness_proxy",
        "visual_brief_fit",
        "geometric_symmetry_score",
        "dataset_typicality_percentile",
        "soft_feature_index",
        "approachability_impression_in_image",
        "image_expressiveness_proxy",
        "expression_readability_proxy",
        "gaze_directness_proxy",
        "camera_engagement_proxy",
        "appearance_descriptors_json",
        "overall_review_priority",
        "needs_human_review",
        "review_reasons_json",
    ]
    with out_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row[field] for field in fieldnames})
    return len(rows)


def schema_summary(db_path: Path) -> str:
    conn = connect(db_path)
    try:
        init_db(conn)
        tables = conn.execute(
            "select name from sqlite_master where type = 'table' order by name"
        ).fetchall()
    finally:
        conn.close()
    return json_dumps({"tables": [row["name"] for row in tables]})
