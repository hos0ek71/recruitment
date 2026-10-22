from app.repositories.collection import content_hash, payload_changes


def test_hash_canonical_and_source_specific():
    assert content_hash("saramin", {"b": 2, "a": 1}) == content_hash("saramin", {"a": 1, "b": 2})
    assert content_hash("saramin", {"id": "1", "read-cnt": "1", "apply-cnt": "0"}) == content_hash(
        "saramin", {"id": "1", "read-cnt": "9", "apply-cnt": "3"}
    )
    assert content_hash("work24", {"read-cnt": "1"}) != content_hash("work24", {"read-cnt": "2"})


def test_payload_changes_deadline_career_and_missing():
    before = {
        "expiration-timestamp": "1",
        "position": {"experience-level": {"min": 0}},
        "removed": 1,
    }
    after = {"expiration-timestamp": "2", "position": {"experience-level": {"min": 2}}, "added": 3}
    assert payload_changes(before, after) == [
        ("/added", None, 3),
        ("/expiration-timestamp", "1", "2"),
        ("/position/experience-level/min", 0, 2),
        ("/removed", 1, None),
    ]
    assert before["position"]["experience-level"]["min"] == 0


def test_payload_changes_lists_types_and_pointer_escaping():
    assert payload_changes({"a/b~": [1], "flag": False}, {"a/b~": [1, 2], "flag": 0}) == [
        ("/a~1b~0", [1], [1, 2]),
        ("/flag", False, 0),
    ]
