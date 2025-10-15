import sys
from types import ModuleType, SimpleNamespace

try:  # pragma: no cover - allow running tests without Flask installed
    import flask  # type: ignore  # noqa: F401
except ModuleNotFoundError:  # pragma: no cover
    flask_stub = ModuleType("flask")

    class DummyFlask:
        def __init__(self, *args, **kwargs):
            self.config = {}

        def route(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator

    flask_stub.Flask = DummyFlask
    flask_stub.render_template = lambda *args, **kwargs: ""
    flask_stub.request = SimpleNamespace(form={}, args={})
    flask_stub.jsonify = lambda *args, **kwargs: {}
    flask_stub.redirect = lambda value, *args, **kwargs: value
    flask_stub.url_for = lambda *args, **kwargs: ""
    sys.modules["flask"] = flask_stub

import pm_dashboard


def test_normalize_card_id_handles_numeric_and_strings():
    assert pm_dashboard._normalize_card_id(7) == "007"
    assert pm_dashboard._normalize_card_id("42") == "042"
    assert pm_dashboard._normalize_card_id("0042") == "042"
    assert pm_dashboard._normalize_card_id("abc") == "abc"
    assert pm_dashboard._normalize_card_id("") is None
    assert pm_dashboard._normalize_card_id(None) is None


def test_build_dependency_view_filters_projects_and_flags_missing(monkeypatch):
    sample_cards = [
        {"_id_str": "023", "_linked_to_str": None, "project": "workspace_management", "title": "Workspace Parent"},
        {"_id_str": "027", "_linked_to_str": "023", "project": "workspace_management", "title": "Workspace Child"},
        {"_id_str": "031", "_linked_to_str": "999", "project": "workspace_management", "title": "Missing Link"},
        {"_id_str": "030", "_linked_to_str": None, "project": "other_project", "title": "Other Project"},
    ]
    monkeypatch.setattr(pm_dashboard, "_load_all_glyphcards", lambda: sample_cards)

    trees, missing_links, unattached = pm_dashboard._build_dependency_view(project_filter="workspace_management")

    root_ids = {tree["card_id"] for tree in trees}
    assert root_ids == {"023", "031"}

    parent_node = next(tree for tree in trees if tree["card_id"] == "023")
    child_ids = [child["card_id"] for child in parent_node["children"]]
    assert child_ids == ["027"]

    assert missing_links == [{"card": sample_cards[2], "missing_id": "999"}]
    assert unattached == []
