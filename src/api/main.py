from fastapi import FastAPI, Depends
from pydantic import BaseModel
from starlette.staticfiles import StaticFiles
from starlette.responses import RedirectResponse, FileResponse
import os
import json
from datetime import datetime, date
from collections import Counter

from src.app.chatbot_logic import process_sentence
from src.model import nlp_utils
from . import auth
from ..security import schemas
from src.app import data_manager

app = FastAPI()

# Include the authentication router
app.include_router(auth.router, tags=["auth"])

# Mount static files for the frontend
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "../app/chatbot-frontend")), name="static")

class Sentence(BaseModel):
    text: str

class PictogramPath(BaseModel):
    path: str

@app.get("/")
async def read_root():
    return RedirectResponse(url="/static/index.html")

@app.get("/categories")
async def get_categories():
    """
    Returns a list of unique pictogram categories.
    """
    categories = set()
    for pictogram in nlp_utils.pictograms:
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
    # Construct the absolute path to the pictogram
    current_dir = os.path.dirname(os.path.abspath(__file__))
    pictogram_path = os.path.abspath(os.path.join(current_dir, '../../data/raw/ARASAAC_ES', path))
    
    if os.path.exists(pictogram_path):
        return FileResponse(pictogram_path)
    return {"error": "Pictogram not found"}

@app.post("/process")
def process_sentence_endpoint(sentence: Sentence, current_user: schemas.User = Depends(auth.get_current_active_user)):
    
    chatbot_response = process_sentence(sentence.text)
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
    """
    Retrieves the usage logs and analytics for the current user, filtered by role.
    """
    if not os.path.exists(data_manager.LOG_FILE):
        return {"analytics": {}, "logs": []}
        
    with open(data_manager.LOG_FILE, 'r', encoding='utf-8') as f:
        all_logs = [json.loads(line) for line in f]

    if not all_logs:
        return {"analytics": {}, "logs": []}

    user_logs = []
    if current_user.role == 'student':
        user_logs = [log for log in all_logs if log.get('username') == current_user.username]
    elif current_user.role in ['parent', 'teacher'] and current_user.students:
        user_logs = [log for log in all_logs if log.get('username') in current_user.students]
    else:
        user_logs = all_logs # Admins/therapists can see all logs

    if not user_logs:
        return {"analytics": {}, "logs": []}

    num_interactions = len(user_logs)
    
    all_words = []
    all_categories = []
    interactions_per_day = Counter()

    for log in user_logs:
        log_date = datetime.fromisoformat(log['timestamp']).date().isoformat()
        interactions_per_day[log_date] += 1
        for item in log['processed_sentence']:
            all_words.append(item['word'])
            if item.get('pictogram'):
                pictogram_details = nlp_utils.find_pictogram(item['word'], nlp_utils.pictograms)
                if pictogram_details:
                    for tag in pictogram_details.get('tags', []):
                        all_categories.append(tag)

    unique_words = set(all_words)
    num_unique_words = len(unique_words)
    
    avg_words_per_interaction = len(all_words) / num_interactions if num_interactions > 0 else 0
    
    category_counts = Counter(all_categories)
    most_common_categories = category_counts.most_common(5)

    analytics = {
        "num_interactions": num_interactions,
        "num_unique_words": num_unique_words,
        "avg_words_per_interaction": round(avg_words_per_interaction, 2),
        "interactions_per_day": dict(interactions_per_day),
        "most_common_categories": most_common_categories
    }

    return {"analytics": analytics, "logs": user_logs}

class GuidedSessionWords(BaseModel):
    words: list[str]

@app.post("/start-guided-session")
async def start_guided_session(session_words: GuidedSessionWords, current_user: schemas.User = Depends(auth.get_current_active_user)):
    """
    Starts a guided session with a specific list of words.
    """
    chatbot_logic.start_guided_session(session_words.words)
    return {"message": "Guided session started successfully. The user can now start guessing the words in the chat."}

class Note(BaseModel):
    text: str

@app.post("/notes")
async def create_note(note: Note, current_user: schemas.User = Depends(auth.get_current_active_user)):
    """
    Creates a new note for the current user.
    """
    data_manager.save_note(current_user.username, note.text)
    return {"message": "Note saved successfully."}

@app.get("/notes")
async def get_notes(current_user: schemas.User = Depends(auth.get_current_active_user)):
    """
    Retrieves all notes.
    """
    return data_manager.get_notes()

@app.get("/notifications")
async def get_notifications(current_user: schemas.User = Depends(auth.get_current_active_user)):
    """
    Generates a summary of the day's usage for authenticated users.
    """
    if not os.path.exists(data_manager.LOG_FILE):
        return {"message": "No usage data available."}

    today = date.today()
    today_logs = []
    with open(data_manager.LOG_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            log = json.loads(line)
            log_date = datetime.fromisoformat(log['timestamp']).date()
            if log_date == today:
                today_logs.append(log)

    if not today_logs:
        return {"message": "No usage data for today."}

    num_interactions = len(today_logs)
    
    all_words = []
    for log in today_logs:
        all_words.extend(item['word'] for item in log['processed_sentence'])
    
    word_counts = Counter(all_words)
    most_common_words = word_counts.most_common(5)
    
    first_interaction = today_logs[0]['timestamp']
    last_interaction = today_logs[-1]['timestamp']

    return {
        "date": today.isoformat(),
        "num_interactions": num_interactions,
        "most_common_words": most_common_words,
        "first_interaction": first_interaction,
        "last_interaction": last_interaction
    }

