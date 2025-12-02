import json

from src.app import data_manager


def test_load_support_content_returns_defaults_when_missing(tmp_path, monkeypatch):
    fake_file = tmp_path / "support_content.json"
    monkeypatch.setattr(data_manager, "SUPPORT_CONTENT_FILE", str(fake_file))

    content = data_manager.load_support_content()

    assert "general" in content
    assert "prompt_prefix" in content["general"]
    assert content["general"]["prompt_prefix"].startswith("Eres un terapeuta")
    assert "related_vocab" in content
    assert "caballo" in content["related_vocab"]


def test_get_user_progress_summary_counts_words(tmp_path, monkeypatch):
    log_file = tmp_path / "usage_logs.json"
    interactions = [
        {
            "timestamp": "2025-01-01T10:00:00",
            "username": "student1",
            "processed_sentence": [{"word": "hola"}, {"word": "amigo"}]
        },
        {
            "timestamp": "2025-01-02T12:00:00",
            "username": "student1",
            "processed_sentence": [{"word": "hola"}]
        },
        {
            "timestamp": "2025-01-03T12:00:00",
            "username": "other",
            "processed_sentence": [{"word": "adios"}]
        }
    ]
    with log_file.open('w', encoding='utf-8') as f:
        for entry in interactions:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    monkeypatch.setattr(data_manager, "LOG_FILE", str(log_file))

    summary = data_manager.get_user_progress_summary("student1")

    assert summary['total_interactions'] == 2
    assert summary['most_common_words'][0][0] == 'hola'
    assert summary['most_common_words'][0][1] == 2
    assert summary['last_interaction'] == "2025-01-02T12:00:00"
