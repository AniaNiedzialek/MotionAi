import os

import database
from database import MotionDatabase
from migration import DEFAULT_JSON_PATH, DEFAULT_MOTION_NAME, migrate_json_to_db


def test_default_db_lives_next_to_the_module(tmp_path, monkeypatch):
    """The database must not depend on the directory the app was launched from."""
    monkeypatch.chdir(tmp_path)
    assert os.path.isabs(database.DEFAULT_DB_PATH)
    assert os.path.dirname(database.DEFAULT_DB_PATH) == database.MODULE_DIR
    # the constructor must use that constant, not a path of its own
    assert MotionDatabase().db_path == database.DEFAULT_DB_PATH
    assert list(tmp_path.iterdir()) == []


def test_bundled_keypoints_are_present():
    assert os.path.exists(DEFAULT_JSON_PATH)


def test_seeding_populates_an_empty_database(tmp_path):
    db = MotionDatabase(str(tmp_path / "motion_data.db"))
    assert db.get_motions_list() == []

    motion_id = migrate_json_to_db(db)

    motions = db.get_motions_list()
    assert motion_id is not None
    assert len(motions) == 1
    assert motions[0]["name"] == DEFAULT_MOTION_NAME
    assert motions[0]["frame_count"] > 0
    assert len(db.get_motion(motion_id)) == motions[0]["frame_count"]


def test_seeding_twice_does_not_duplicate(tmp_path):
    db = MotionDatabase(str(tmp_path / "motion_data.db"))

    first_id = migrate_json_to_db(db)
    second_id = migrate_json_to_db(db)

    assert first_id == second_id
    assert len(db.get_motions_list()) == 1


def test_missing_keypoints_file_is_handled(tmp_path):
    db = MotionDatabase(str(tmp_path / "motion_data.db"))

    assert migrate_json_to_db(db, json_file=str(tmp_path / "nope.json")) is None
    assert db.get_motions_list() == []
