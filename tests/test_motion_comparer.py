import pytest

from motion_comparer import MotionComparer


def make_pose(**joints):
    """Build a keypoint dict in the shape the app produces: joint -> [x, y, z, visibility]."""
    return {name: list(coords) + [1.0] for name, coords in joints.items()}


def test_identical_poses_score_100():
    comparer = MotionComparer()
    pose = make_pose(LEFT_SHOULDER=(0.5, 0.4, 0.0), RIGHT_HIP=(0.4, 0.6, 0.1))

    score, feedback, deviations = comparer.calculate_similarity(pose, pose)

    assert score == pytest.approx(100.0)
    assert feedback == "Good alignment!"
    assert deviations == set()


def test_missing_pose_returns_zero():
    comparer = MotionComparer()
    pose = make_pose(NOSE=(0.5, 0.3, 0.0))

    assert comparer.calculate_similarity({}, pose) == (0.0, "No pose detected", set())
    assert comparer.calculate_similarity(pose, {}) == (0.0, "No pose detected", set())


def test_no_shared_joints_cannot_compare():
    comparer = MotionComparer()
    user = make_pose(LEFT_WRIST=(0.5, 0.3, 0.0))
    pro = make_pose(RIGHT_ANKLE=(0.5, 0.3, 0.0))

    assert comparer.calculate_similarity(user, pro) == (0.0, "Cannot compare poses", set())


def test_joint_beyond_threshold_is_flagged():
    comparer = MotionComparer(deviation_threshold=0.1)
    user = make_pose(LEFT_SHOULDER=(0.5, 0.4, 0.0), LEFT_WRIST=(0.9, 0.4, 0.0))
    pro = make_pose(LEFT_SHOULDER=(0.5, 0.4, 0.0), LEFT_WRIST=(0.5, 0.4, 0.0))

    score, feedback, deviations = comparer.calculate_similarity(user, pro)

    assert deviations == {"LEFT_WRIST"}
    assert "Left Wrist" in feedback
    assert score < 100.0


def test_score_never_goes_negative():
    comparer = MotionComparer()
    user = make_pose(NOSE=(10.0, 10.0, 10.0))
    pro = make_pose(NOSE=(0.0, 0.0, 0.0))

    score, _, _ = comparer.calculate_similarity(user, pro)

    assert score == 0.0
