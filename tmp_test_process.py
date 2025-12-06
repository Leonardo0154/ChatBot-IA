from fastapi.testclient import TestClient
from src.api.main import app
from src.api import auth
from src.security import schemas


def override_student_user():
    return schemas.User(username="student1", role="student", students=["student1"])

app.dependency_overrides[auth.get_current_active_user] = override_student_user

client = TestClient(app)
texts = ["agua", "57 veces con el asistente", "57vecesconelasistente", "como es un raton", "un raton"]
for t in texts:
    resp = client.post("/process", json={"text": t})
    print(t, resp.status_code)
    if resp.status_code == 200:
        print(resp.json())
    else:
        print(resp.text)
    print("---")
