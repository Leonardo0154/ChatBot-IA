from fastapi.testclient import TestClient
import sys
import os

# Add the project root to the sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.api.main import app
from src.api import auth
from src.security import schemas
from src.app import data_manager


def override_student_user():
    return schemas.User(username="student1", role="student", students=["student1"])


app.dependency_overrides[auth.get_current_active_user] = override_student_user

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    # The root now redirects, so we expect a 200 OK and the content of index.html
    assert "text/html" in response.headers["content-type"]

def test_get_pictograms():
    response = client.get("/pictograms")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_process_sentence():
    response = client.post("/process", json={"text": "hola"})
    assert response.status_code == 200
    data = response.json()
    assert "processed_sentence" in data
    assert isinstance(data["processed_sentence"], list)

def test_pictogram_to_text():
    # First, get a valid pictogram path from the gallery
    response = client.get("/pictograms")
    assert response.status_code == 200
    pictograms = response.json()
    if pictograms:
        pictogram_path = pictograms[0].get("path")
        if pictogram_path:
            response = client.post("/pictogram-to-text", json={"path": pictogram_path})
            assert response.status_code == 200
            data = response.json()
            assert "word" in data
            assert isinstance(data["word"], str)


def test_assignment_results_reject_non_student(monkeypatch):
    def override_teacher_user():
        return schemas.User(username="teacher1", role="teacher", students=["student1"])

    app.dependency_overrides[auth.get_current_active_user] = override_teacher_user

    monkeypatch.setattr(data_manager, "get_assignments", lambda: [{"timestamp": "test-assignment"}])

    response = client.post("/assignment-results", json={"assignment_id": "test-assignment", "answers": []})
    assert response.status_code == 403

    app.dependency_overrides[auth.get_current_active_user] = override_student_user


def test_assignment_results_accepts_student(monkeypatch):
    monkeypatch.setattr(
        data_manager,
        "get_assignments",
        lambda: [{
            "timestamp": "assignment-123",
            "author": "teacher1",
            "title": "Test",
            "task": "Say the word",
            "words": ["hola"],
            "type": "assignment"
        }]
    )

    saved_payload = {}

    def fake_save(username, payload):
        saved_payload["username"] = username
        saved_payload["payload"] = payload

    monkeypatch.setattr(data_manager, "save_assignment_result", fake_save)

    response = client.post("/assignment-results", json={
        "assignment_id": "assignment-123",
        "answers": [{"word": "hola", "answer": "hola"}]
    })

    assert response.status_code == 200
    assert saved_payload["username"] == "student1"
    assert saved_payload["payload"]["assignment_id"] == "assignment-123"
