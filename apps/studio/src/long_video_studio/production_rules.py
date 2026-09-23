"""Our own production rules. Other film repos are not installed."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from long_video_studio.domain import ShotSpec

DEFAULT_CAMERA = ShotSpec.model_fields["camera"].default


class NotReady(RuntimeError):
    """A clip was asked for before the locked facts exist."""


def require_locked_faces(project: Any) -> None:
    """A named person needs one approved photo before any clip."""
    missing = [
        subject.label
        for subject in project.world_bible.subjects
        if not subject.reference_asset_ids
    ]
    if missing:
        names = ", ".join(missing)
        raise NotReady(f"Lock a face photo before drawing: {names}")


def chain_last_frames(project: Any) -> None:
    """The next shot starts from the previous shot's last frame, unless you set a start frame."""
    ordered = sorted(project.shots, key=lambda shot: shot.index)
    for previous, shot in zip(ordered, ordered[1:]):
        if shot.start_frame_asset_id or shot.continuity_from_shot_id:
            continue
        shot.continuity_from_shot_id = previous.id


def handoff_record(project: Any) -> dict[str, Any]:
    """Stable ids for this render. The prompt is not the record."""
    ordered = sorted(project.shots, key=lambda shot: shot.index)
    shots = []
    for shot in ordered:
        shots.append(
            {
                "shot_id": shot.id,
                "starts_from_shot_id": shot.continuity_from_shot_id,
                "locked_reference_ids": list(shot.reference_asset_ids),
            }
        )
    return {"project_id": project.id, "shots": shots}


def write_handoff(project: Any, folder: Path) -> Path:
    path = folder / "handoff.json"
    path.write_text(json.dumps(handoff_record(project), indent=2), encoding="utf-8")
    return path


def _ordered(project: Any) -> list[Any]:
    return sorted(project.shots, key=lambda shot: shot.index)


def _character_ids(project: Any) -> list[str]:
    return [subject.subject_id for subject in project.world_bible.subjects]


def _locked_faces(project: Any, shot: Any) -> list[str]:
    ids = [asset_id for subject in project.world_bible.subjects for asset_id in subject.reference_asset_ids]
    ids.extend(shot.reference_asset_ids)
    return list(dict.fromkeys(ids))


def _location_note(project: Any) -> str:
    return "; ".join(note for note in project.world_bible.location_notes if note)


def film_dsl(project: Any) -> dict[str, Any]:
    """One film document. Shot layers match the CineCrew blueprint. Later slots stay empty."""
    scene_id = f"{project.id}:scene:1"
    character_ids = _character_ids(project)
    location = _location_note(project)
    shots = []
    for shot in _ordered(project):
        shots.append(
            {
                "shot_id": shot.id,
                "scene_id": scene_id,
                "character_ids": character_ids,
                "location_note": location,
                "camera": shot.camera,
                "locked_face_asset_ids": _locked_faces(project, shot),
                "starts_from_shot_id": shot.continuity_from_shot_id,
                "narrative_layer": {
                    "narrative_action": shot.prompt,
                    "emotional_beat": shot.purpose,
                },
                "staging_layer": {
                    "duration_seconds": shot.duration_seconds,
                    "camera": {"shot_scale": None, "angle": None, "movement": shot.camera},
                    "lighting": None,
                    "entities": [{"asset_id": asset_id} for asset_id in character_ids],
                },
                "render_layer": None,
                "assembly_layer": None,
                "lighting": None,
                "performance": None,
                "audio": None,
                "qa": None,
            }
        )
    return {
        "blueprint_id": project.id,
        "film_id": project.id,
        "act": None,
        "sequence": None,
        "scene_id": scene_id,
        "metadata": {
            "project_name": project.brief.title,
            "target_aspect_ratio": project.brief.aspect_ratio,
        },
        "global_style": project.world_bible.visual_style,
        "lighting": None,
        "performance": None,
        "audio": None,
        "qa": None,
        "shots": shots,
    }


def _camera_lock(camera: str) -> str:
    return "variable" if camera == DEFAULT_CAMERA else "override"


def generation_record(project: Any, model_name: str) -> dict[str, Any]:
    """Immutable inputs for this draw. The hash covers those inputs, not the pixels."""
    shots = []
    for shot in _ordered(project):
        reference_ids = _locked_faces(project, shot)
        shots.append(
            {
                "shot_id": shot.id,
                "model_name": model_name,
                "reference_ids": reference_ids,
                "camera": shot.camera,
                "lock_map": {
                    "face": "locked",
                    "reference_ids": "locked",
                    "camera": _camera_lock(shot.camera),
                },
            }
        )
    body = {"film_id": project.id, "model_name": model_name, "shots": shots}
    raw = json.dumps(body, sort_keys=True, separators=(",", ":"))
    body["input_hash"] = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return body


def render_model_name(
    *,
    fl2va_url: str | None,
    ref2va_url: str | None,
    image_edit_model: str | None,
) -> str:
    if fl2va_url:
        return "minimax-h3-fl2va"
    if ref2va_url:
        return "minimax-h3-ref2va"
    if image_edit_model:
        return image_edit_model
    return "unconfigured"


def write_film_dsl(project: Any, folder: Path) -> Path:
    path = folder / "filmdsl.json"
    path.write_text(json.dumps(film_dsl(project), indent=2), encoding="utf-8")
    return path


def write_generation(project: Any, folder: Path, model_name: str) -> Path:
    path = folder / "generation.json"
    path.write_text(json.dumps(generation_record(project, model_name), indent=2), encoding="utf-8")
    return path
