"""Build shot cards with the CineCrew plan writer. Does not render video."""

from __future__ import annotations

import sys
from pathlib import Path

from long_video_studio.domain import (
    ContinuityState,
    DialogueLine,
    FilmProject,
    ProjectBrief,
    ShotSpec,
    WorldBible,
)
from long_video_studio.h3_limits import H3_MAX_SHOT_SECONDS, H3_MIN_SHOT_SECONDS


class PlannerBridgeError(RuntimeError):
    """The plan writer could not produce a shot list."""


def _plan_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "packages" / "plan" / "src" / "pipeline.py"
        if candidate.is_file():
            return parent / "packages" / "plan"
    raise PlannerBridgeError("The plan writer folder packages/plan is missing.")


def write_plan(brief: ProjectBrief, project_id: str | None) -> FilmProject:
    plan_root = _plan_root()
    root = str(plan_root)
    if root not in sys.path:
        sys.path.insert(0, root)
    try:
        from src.pipeline import get_enabled_stages, run_pipeline
    except ImportError as error:
        raise PlannerBridgeError(
            "The plan writer is missing a Python package. Install packages/plan requirements."
        ) from error

    stages = get_enabled_stages()
    for stage in stages:
        if stage.get("id") == "production_operator":
            stage["execute"] = False

    run_root = plan_root / "data" / "runs" / "studio" / (project_id or "draft")
    context = run_pipeline(brief.prompt, stages=stages, run_root=run_root)
    return _to_project(
        brief,
        project_id,
        context.get("scene_blueprint"),
        context.get("asset_library"),
    )


def _clip(seconds: float | None) -> float:
    value = 5.0 if not seconds else float(seconds)
    return max(H3_MIN_SHOT_SECONDS, min(H3_MAX_SHOT_SECONDS, value))


def _clean(text: str) -> str:
    return text.replace("<d>", "").replace("</d>", "").strip()


def _to_project(brief: ProjectBrief, project_id: str | None, blueprint, library) -> FilmProject:
    names: list[str] = []
    for character in getattr(library, "characters", []) or []:
        name = getattr(character, "name", "") or getattr(character, "id", "")
        if name:
            names.append(str(name))

    shots: list[ShotSpec] = []
    for index, shot in enumerate(getattr(blueprint, "shots", []) or []):
        narrative = shot.narrative_layer
        staging = shot.staging_layer
        render = shot.render_layer
        action = _clean((narrative.narrative_action if narrative else "") or brief.prompt) or brief.prompt
        camera = "medium shot, stable cinematic camera"
        duration = 5.0
        constraints: list[str] = []
        if staging is not None:
            duration = _clip(staging.duration_seconds)
            parts = [staging.camera.shot_scale, staging.camera.angle, staging.camera.movement]
            joined = ", ".join(part for part in parts if part)
            if joined:
                camera = joined
            constraints = [item for item in (staging.consistency_constraints or []) if item]
        prompt = action
        if render is not None and render.video.resolved_i2v:
            prompt = _clean(render.video.resolved_i2v) or prompt
        dialogue: list[DialogueLine] = []
        spoken = narrative.dialogue if narrative else None
        if spoken and spoken.has_dialogue and spoken.text and _clean(spoken.text):
            dialogue.append(
                DialogueLine(
                    speaker=spoken.speaker_asset_id or "Speaker",
                    text=_clean(spoken.text),
                    language=brief.language or "zh-CN",
                )
            )
        shots.append(
            ShotSpec(
                index=index,
                title=str(shot.shot_id or f"Shot {index + 1}"),
                purpose=_clean(narrative.emotional_beat) if narrative and narrative.emotional_beat else "Scene",
                duration_seconds=duration,
                prompt=prompt[:4000],
                camera=camera,
                dialogue=dialogue,
                continuity_out=ContinuityState(
                    action=action[:500],
                    camera=camera,
                    handoff="; ".join(constraints)[:500],
                ),
            )
        )

    if not shots:
        raise PlannerBridgeError("The plan writer returned no shots.")

    style = getattr(blueprint, "global_style", None) or brief.style
    payload: dict = {
        "brief": brief,
        "world_bible": WorldBible(
            logline=(brief.title or brief.prompt)[:240],
            visual_style=style or brief.style,
            character_notes=names,
            continuity_rules=["Only the locked shot goes to the video machine."],
        ),
        "shots": shots,
        "status": "planned",
    }
    if project_id:
        payload["id"] = project_id
    return FilmProject(**payload)
