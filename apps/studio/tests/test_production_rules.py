from long_video_studio.domain import FilmProject, ProjectBrief, ShotSpec, SubjectCard, WorldBible
from long_video_studio.production_rules import (
    NotReady,
    chain_last_frames,
    film_dsl,
    generation_record,
    require_locked_faces,
)


def _project(subjects: list[SubjectCard]) -> FilmProject:
    return FilmProject(
        brief=ProjectBrief(prompt="A short test scene."),
        world_bible=WorldBible(logline="Test", visual_style="plain", subjects=subjects),
        shots=[
            ShotSpec(index=0, title="One", purpose="Open", duration_seconds=5, prompt="A person waits."),
            ShotSpec(index=1, title="Two", purpose="Next", duration_seconds=5, prompt="The same person turns."),
        ],
    )


def test_missing_face_blocks_draw():
    project = _project([SubjectCard(subject_id="char_1", label="Asha")])
    try:
        require_locked_faces(project)
    except NotReady as error:
        assert "Asha" in str(error)
    else:
        raise AssertionError("draw was allowed without a face photo")


def _locked_project() -> FilmProject:
    project = _project(
        [SubjectCard(subject_id="char_1", label="Asha", reference_asset_ids=["asset_face"])]
    )
    require_locked_faces(project)
    chain_last_frames(project)
    return project


def test_locked_face_and_last_frame_chain():
    project = _locked_project()
    assert project.shots[1].continuity_from_shot_id == project.shots[0].id


def test_film_dsl_keeps_one_document():
    project = _locked_project()
    document = film_dsl(project)
    assert document["film_id"] == project.id
    assert document["act"] is None
    assert document["qa"] is None
    assert document["shots"][0]["shot_id"] == project.shots[0].id
    assert document["shots"][0]["locked_face_asset_ids"] == ["asset_face"]
    assert document["shots"][0]["staging_layer"]["camera"]["movement"] == project.shots[0].camera
    assert document["shots"][1]["starts_from_shot_id"] == project.shots[0].id


def test_same_inputs_keep_the_same_hash():
    project = _locked_project()
    first = generation_record(project, "minimax-h3-fl2va")
    second = generation_record(project, "minimax-h3-fl2va")
    assert first["input_hash"] == second["input_hash"]
    assert first["shots"][0]["lock_map"]["face"] == "locked"


def test_camera_change_keeps_the_locked_face():
    project = _locked_project()
    before = generation_record(project, "minimax-h3-fl2va")
    project.shots[0].camera = "50mm"
    after = generation_record(project, "minimax-h3-fl2va")
    assert after["shots"][0]["reference_ids"] == before["shots"][0]["reference_ids"]
    assert after["shots"][0]["lock_map"]["camera"] == "override"
    assert after["input_hash"] != before["input_hash"]
