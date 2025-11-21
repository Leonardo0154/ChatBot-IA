from fastapi.testclient import TestClient
import sys
import os

# Add the project root to the sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.api.main import app

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
