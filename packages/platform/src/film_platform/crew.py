"""The crew order. Each step has one job. Two of them are a person."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Step:
    id: str
    skill: str
    who: str


CREW: tuple[Step, ...] = (
    Step("read_script", "structure-screenplay", "machine"),
    Step("story", "shape-story-blueprint", "machine"),
    Step("assets", "design-production-assets", "machine"),
    Step("camera", "plan-camera-shots", "machine"),
    Step("you_lock", "human-gate", "you"),
    Step("order", "compile-generation-prompts", "machine"),
    Step("draw", "execute-media-generation", "machine"),
    Step("check_face", "character-continuity", "machine"),
    Step("check_cut", "review-and-assemble", "machine"),
    Step("you_keep", "human-gate", "you"),
)


def before_draw() -> tuple[Step, ...]:
    return tuple(step for step in CREW if step.id in {"read_script", "story", "assets", "camera", "you_lock", "order"})
