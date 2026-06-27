"""SQLite storage for the MVP."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


SCHEMA = [
    """
    create table if not exists subjects (
      subject_id text primary key,
      display_name text,
      created_at text not null,
      notes text
    )
    """,
    """
    create table if not exists consents (
      consent_id text primary key,
      subject_id text not null,
      source text not null,
      source_hash text not null,
      allows_automated_processing integer not null,
      allows_ai_review integer not null,
      allows_face_embeddings integer not null,
      allows_remote_vlm integer not null,
      expires_at text,
      revoked_at text,
      created_at text not null,
      foreign key(subject_id) references subjects(subject_id)
    )
    """,
    """
    create table if not exists photos (
      photo_id text primary key,
      subject_id text not null,
      consent_id text not null,
      source_path text not null,
      sha256 text not null unique,
      file_size_bytes integer not null,
      width integer,
      height integer,
      mode text,
      created_at text not null,
      ingest_status text not null,
      ingest_error text,
      foreign key(subject_id) references subjects(subject_id),
      foreign key(consent_id) references consents(consent_id)
    )
    """,
    """
    create table if not exists cv_observations (
      observation_id text primary key,
      photo_id text not null,
      backend text not null,
      backend_version text not null,
      analysis_version text not null,
      payload_json text not null,
      quality_score real,
      quality_flags_json text not null,
      created_at text not null,
      foreign key(photo_id) references photos(photo_id)
    )
    """,
    """
    create table if not exists scores (
      score_id text primary key,
      photo_id text not null,
      score_version text not null,
      visual_age_band text,
      apparent_age_estimate real,
      apparent_age_confidence real,
      perceived_freshness_in_image real,
      under_eye_shadowing_in_image real,
      under_eye_bag_prominence_in_image real,
      ocular_redness_in_image real,
      visible_blemish_like_elements real,
      visible_skin_evenness real,
      visible_freshness_proxy real,
      visual_brief_fit real,
      geometric_symmetry_score real,
      dataset_typicality_percentile real,
      soft_feature_index real,
      approachability_impression_in_image real,
      image_expressiveness_proxy real,
      expression_readability_proxy real,
      gaze_directness_proxy real,
      camera_engagement_proxy real,
      appearance_descriptors_json text,
      overall_review_priority real,
      needs_human_review integer not null,
      review_reasons_json text not null,
      created_at text not null,
      foreign key(photo_id) references photos(photo_id)
    )
    """,
    """
    create table if not exists vlm_reviews (
      vlm_review_id text primary key,
      photo_id text not null,
      prompt_version text not null,
      model text not null,
      input_fingerprint text not null,
      output_json text not null,
      usage_json text,
      policy_flags_json text not null,
      created_at text not null,
      foreign key(photo_id) references photos(photo_id)
    )
    """,
    """
    create table if not exists human_reviews (
      human_review_id text primary key,
      photo_id text not null,
      reviewer_id text not null,
      decision text not null,
      notes text,
      override_json text,
      created_at text not null,
      foreign key(photo_id) references photos(photo_id)
    )
    """,
    """
    create table if not exists audit_log (
      audit_id text primary key,
      event_type text not null,
      subject_id text,
      photo_id text,
      payload_json text not null,
      created_at text not null
    )
    """,
    "create index if not exists idx_photos_subject on photos(subject_id)",
    "create index if not exists idx_cv_photo on cv_observations(photo_id)",
    "create index if not exists idx_scores_photo on scores(photo_id)",
]


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


def json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("pragma foreign_keys = on")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    for statement in SCHEMA:
        conn.execute(statement)
    conn.commit()


def insert_audit(
    conn: sqlite3.Connection,
    event_type: str,
    payload: dict[str, Any],
    subject_id: str | None = None,
    photo_id: str | None = None,
) -> None:
    conn.execute(
        """
        insert into audit_log (
          audit_id, event_type, subject_id, photo_id, payload_json, created_at
        ) values (?, ?, ?, ?, ?, ?)
        """,
        (new_id("audit"), event_type, subject_id, photo_id, json_dumps(payload), now_iso()),
    )


def upsert_subject(conn: sqlite3.Connection, subject_id: str, display_name: str | None) -> None:
    conn.execute(
        """
        insert into subjects(subject_id, display_name, created_at, notes)
        values (?, ?, ?, null)
        on conflict(subject_id) do nothing
        """,
        (subject_id, display_name, now_iso()),
    )


def upsert_consent(
    conn: sqlite3.Connection,
    consent_id: str,
    subject_id: str,
    source: str,
    source_hash: str,
    allows_remote_vlm: bool,
) -> None:
    conn.execute(
        """
        insert into consents(
          consent_id, subject_id, source, source_hash,
          allows_automated_processing, allows_ai_review, allows_face_embeddings,
          allows_remote_vlm, expires_at, revoked_at, created_at
        ) values (?, ?, ?, ?, 1, 1, 1, ?, null, null, ?)
        on conflict(consent_id) do nothing
        """,
        (consent_id, subject_id, source, source_hash, int(allows_remote_vlm), now_iso()),
    )


def find_photo_by_hash(conn: sqlite3.Connection, sha256: str) -> sqlite3.Row | None:
    cursor = conn.execute("select * from photos where sha256 = ?", (sha256,))
    return cursor.fetchone()


def insert_photo(
    conn: sqlite3.Connection,
    subject_id: str,
    consent_id: str,
    source_path: Path,
    sha256: str,
    file_size_bytes: int,
    width: int | None,
    height: int | None,
    mode: str | None,
    ingest_status: str,
    ingest_error: str | None,
) -> str:
    photo_id = new_id("photo")
    conn.execute(
        """
        insert into photos(
          photo_id, subject_id, consent_id, source_path, sha256, file_size_bytes,
          width, height, mode, created_at, ingest_status, ingest_error
        ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            photo_id,
            subject_id,
            consent_id,
            str(source_path),
            sha256,
            file_size_bytes,
            width,
            height,
            mode,
            now_iso(),
            ingest_status,
            ingest_error,
        ),
    )
    return photo_id


def list_photos_for_analysis(
    conn: sqlite3.Connection,
    limit: int | None,
    force: bool,
) -> list[sqlite3.Row]:
    query = """
        select p.*
        from photos p
        where p.ingest_status = 'ok'
    """
    values: list[Any] = []
    if not force:
        query += """
          and not exists (
            select 1 from cv_observations c
            where c.photo_id = p.photo_id and c.backend = 'pillow_basic'
          )
        """
    query += " order by p.created_at asc"
    if limit is not None:
        query += " limit ?"
        values.append(limit)
    cursor = conn.execute(query, values)
    return list(cursor.fetchall())


def insert_cv_observation(
    conn: sqlite3.Connection,
    photo_id: str,
    backend: str,
    backend_version: str,
    analysis_version: str,
    payload: dict[str, Any],
    quality_score: float | None,
    quality_flags: list[str],
) -> str:
    observation_id = new_id("obs")
    conn.execute(
        """
        insert into cv_observations(
          observation_id, photo_id, backend, backend_version, analysis_version,
          payload_json, quality_score, quality_flags_json, created_at
        ) values (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            observation_id,
            photo_id,
            backend,
            backend_version,
            analysis_version,
            json_dumps(payload),
            quality_score,
            json_dumps(quality_flags),
            now_iso(),
        ),
    )
    return observation_id


def insert_score(
    conn: sqlite3.Connection,
    photo_id: str,
    score_version: str,
    values: dict[str, Any],
    review_reasons: list[str],
) -> str:
    score_id = new_id("score")
    conn.execute(
        """
        insert into scores(
          score_id, photo_id, score_version, visual_age_band, apparent_age_estimate,
          apparent_age_confidence, perceived_freshness_in_image,
          under_eye_shadowing_in_image, under_eye_bag_prominence_in_image,
          ocular_redness_in_image, visible_blemish_like_elements,
          visible_skin_evenness, visible_freshness_proxy,
          visual_brief_fit, geometric_symmetry_score,
          dataset_typicality_percentile, soft_feature_index,
          approachability_impression_in_image, image_expressiveness_proxy,
          expression_readability_proxy, gaze_directness_proxy, camera_engagement_proxy,
          appearance_descriptors_json,
          overall_review_priority, needs_human_review, review_reasons_json,
          created_at
        ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            score_id,
            photo_id,
            score_version,
            values.get("visual_age_band"),
            values.get("apparent_age_estimate"),
            values.get("apparent_age_confidence"),
            values.get("perceived_freshness_in_image"),
            values.get("under_eye_shadowing_in_image"),
            values.get("under_eye_bag_prominence_in_image"),
            values.get("ocular_redness_in_image"),
            values.get("visible_blemish_like_elements"),
            values.get("visible_skin_evenness"),
            values.get("visible_freshness_proxy"),
            values.get("visual_brief_fit"),
            values.get("geometric_symmetry_score"),
            values.get("dataset_typicality_percentile"),
            values.get("soft_feature_index"),
            values.get("approachability_impression_in_image"),
            values.get("image_expressiveness_proxy"),
            values.get("expression_readability_proxy"),
            values.get("gaze_directness_proxy"),
            values.get("camera_engagement_proxy"),
            values.get("appearance_descriptors_json"),
            values.get("overall_review_priority"),
            int(bool(values.get("needs_human_review"))),
            json_dumps(review_reasons),
            now_iso(),
        ),
    )
    return score_id


def report_rows(conn: sqlite3.Connection, limit: int | None) -> list[sqlite3.Row]:
    query = """
        select
          p.photo_id,
          p.subject_id,
          p.source_path,
          p.sha256,
          p.width,
          p.height,
          latest.quality_score,
          latest.quality_flags_json,
          s.visual_age_band,
          s.apparent_age_estimate,
          s.apparent_age_confidence,
          s.perceived_freshness_in_image,
          s.under_eye_shadowing_in_image,
          s.under_eye_bag_prominence_in_image,
          s.ocular_redness_in_image,
          s.visible_blemish_like_elements,
          s.visible_skin_evenness,
          s.visible_freshness_proxy,
          s.visual_brief_fit,
          s.geometric_symmetry_score,
          s.dataset_typicality_percentile,
          s.soft_feature_index,
          s.approachability_impression_in_image,
          s.image_expressiveness_proxy,
          s.expression_readability_proxy,
          s.gaze_directness_proxy,
          s.camera_engagement_proxy,
          s.appearance_descriptors_json,
          s.overall_review_priority,
          s.needs_human_review,
          s.review_reasons_json
        from photos p
        left join cv_observations latest
          on latest.observation_id = (
            select observation_id
            from cv_observations
            where photo_id = p.photo_id
            order by created_at desc
            limit 1
          )
        left join scores s
          on s.score_id = (
            select score_id
            from scores
            where photo_id = p.photo_id
            order by created_at desc
            limit 1
          )
        order by s.overall_review_priority desc, latest.quality_score desc, p.created_at asc
    """
    values: list[Any] = []
    if limit is not None:
        query += " limit ?"
        values.append(limit)
    cursor = conn.execute(query, values)
    return list(cursor.fetchall())
