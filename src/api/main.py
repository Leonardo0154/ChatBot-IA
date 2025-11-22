from fastapi import FastAPI, Depends
from pydantic import BaseModel
from starlette.staticfiles import StaticFiles
from starlette.responses import RedirectResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import json
from datetime import datetime, date
from collections import Counter

from src.app import chatbot_logic
from src.model import nlp_utils
from . import auth
from ..security import schemas
from src.app import data_manager

app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, tags=["auth"])
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "../app/chatbot-frontend")), name="static")

class Sentence(BaseModel):
    text: str

class PictogramPath(BaseModel):
    path: str

class GuidedSessionWords(BaseModel):
    words: list[str]

class Note(BaseModel):
    text: str

class Assignment(BaseModel):
    title: str
    words: list[str]
    task: str

class AssignmentResult(BaseModel):
    assignment_id: str
    answers: list

@app.get("/")
async def read_root():
    return RedirectResponse(url="/static/index.html")

@app.get("/categories")
async def get_categories():
    categories = set()
    for pictogram in nlp_utils.pictograms:
        if pictogram.get('keywords'):
            for tag in pictogram.get('tags', []):
                categories.add(tag)
    return sorted(list(categories))

@app.get("/pictograms")
async def get_pictograms():
    return nlp_utils.pictograms

@app.post("/pictogram-to-text")
async def pictogram_to_text(pictogram_path: PictogramPath):
    word = nlp_utils.find_word_for_pictogram(pictogram_path.path, nlp_utils.pictograms)
    return {"word": word}

@app.get("/pictogram/{path:path}")
async def get_pictogram(path: str):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    pictogram_path = os.path.abspath(os.path.join(current_dir, '../../data/raw/ARASAAC_ES', path))
    if os.path.exists(pictogram_path):
        return FileResponse(pictogram_path)
    return {"error": "Pictogram not found"}

@app.post("/process")
async def process_sentence_endpoint(sentence: Sentence, current_user: schemas.User = Depends(auth.get_current_active_user)):
    chatbot_response = chatbot_logic.process_sentence(current_user.username, sentence.text)
    data_manager.log_interaction(current_user.username, sentence.text, chatbot_response)
    return {
        "sentence": sentence.text,
        "processed_sentence": chatbot_response
    }

@app.get("/users/me/", response_model=schemas.User)
async def read_users_me(current_user: schemas.User = Depends(auth.get_current_active_user)):
    return current_user

@app.get("/progress")
async def get_progress(current_user: schemas.User = Depends(auth.get_current_active_user)):
    if not os.path.exists(data_manager.LOG_FILE):
        return {"analytics": {}, "logs": []}
    with open(data_manager.LOG_FILE, 'r', encoding='utf-8') as f:
        all_logs = [json.loads(line) for line in f]
    user_logs = []
    if current_user.role == 'student':
        user_logs = [log for log in all_logs if log.get('username') == current_user.username]
    elif current_user.role in ['parent', 'teacher', 'therapist'] and current_user.students:
        user_logs = [log for log in all_logs if log.get('username') in current_user.students]
    else:
        user_logs = all_logs
    if not user_logs:
        return {"analytics": {}, "logs": []}
    num_interactions = len(user_logs)
    all_words = [item['word'] for log in user_logs for item in log['processed_sentence']]
    interactions_per_day = Counter(datetime.fromisoformat(log['timestamp']).date().isoformat() for log in user_logs)
    unique_words = set(all_words)
    avg_words_per_interaction = len(all_words) / num_interactions if num_interactions > 0 else 0
    all_categories = [tag for log in user_logs for item in log['processed_sentence'] if item.get('pictogram') for pictogram in nlp_utils.pictograms if pictogram.get('path') == item['pictogram'] for tag in pictogram.get('tags', [])]
    category_counts = Counter(all_categories)
    analytics = {
        "num_interactions": num_interactions,
        "num_unique_words": len(unique_words),
        "avg_words_per_interaction": round(avg_words_per_interaction, 2),
        "interactions_per_day": dict(interactions_per_day),
        "most_common_categories": category_counts.most_common(5)
    }
    return {"analytics": analytics, "logs": user_logs}

@app.post("/start-guided-session")
async def start_guided_session(session_words: GuidedSessionWords, current_user: schemas.User = Depends(auth.get_current_active_user)):
    chatbot_logic.start_guided_session(current_user.username, session_words.words)
    return {"message": "Guided session started successfully."}

@app.post("/logout")
async def logout(current_user: schemas.User = Depends(auth.get_current_active_user)):
    chatbot_logic.clear_user_game_state(current_user.username)
    return {"message": "Logged out successfully."}

@app.post("/notes")
async def create_note(note: Note, current_user: schemas.User = Depends(auth.get_current_active_user)):
    data_manager.save_note(current_user.username, note.text)
    return {"message": "Note saved successfully."}

@app.post("/assignments")
async def create_assignment(assignment: Assignment, current_user: schemas.User = Depends(auth.get_current_active_user)):
    data_manager.save_assignment(current_user.username, assignment.dict())
    return {"message": "Assignment saved successfully."}

@app.get("/assignments")
async def get_assignments(current_user: schemas.User = Depends(auth.get_current_active_user)):
    return data_manager.get_assignments()

@app.get("/assignment/{assignment_id}")
async def get_assignment(assignment_id: str, current_user: schemas.User = Depends(auth.get_current_active_user)):
    assignments = data_manager.get_assignments()
    for assignment in assignments:
        if assignment['timestamp'] == assignment_id:
            return assignment
    return {"error": "Assignment not found"}

@app.post("/assignment-results")
async def create_assignment_result(result: AssignmentResult, current_user: schemas.User = Depends(auth.get_current_active_user)):
    data_manager.save_assignment_result(current_user.username, result.dict())
    return {"message": "Assignment results saved successfully."}

@app.get("/notes")
async def get_notes(current_user: schemas.User = Depends(auth.get_current_active_user)):
    return data_manager.get_notes()

@app.get("/notifications")
async def get_notifications(current_user: schemas.User = Depends(auth.get_current_active_user)):
    if not os.path.exists(data_manager.LOG_FILE):
        return {"message": "No usage data available."}
    today = date.today()
    today_logs = []
    with open(data_manager.LOG_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            log = json.loads(line)
            if datetime.fromisoformat(log['timestamp']).date() == today:
                today_logs.append(log)
    if not today_logs:
        return {"message": "No usage data for today."}
    num_interactions = len(today_logs)
    all_words = [item['word'] for log in today_logs for item in log['processed_sentence']]
    word_counts = Counter(all_words)
    return {
        "date": today.isoformat(),
        "num_interactions": num_interactions,
        "most_common_words": word_counts.most_common(5),
        "first_interaction": today_logs[0]['timestamp'],
        "last_interaction": today_logs[-1]['timestamp']
    }