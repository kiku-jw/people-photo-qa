"""High-level MVP workflow."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

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
