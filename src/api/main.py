from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from starlette.staticfiles import StaticFiles
from starlette.responses import RedirectResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import json
import copy
from datetime import datetime, date
from collections import Counter
from typing import List, Optional

from src.app import chatbot_logic
from src.app import audio_manager, support_pack_manager, report_manager
from src.app import notification_manager, sharing_manager, consent_manager

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
    assignment_id: str | None = None
    title: str | None = None
    task: str | None = None



class Note(BaseModel):

    text: str



class Assignment(BaseModel):

    title: str

    words: list[str]

    task: str
    type: str = 'assignment'  # can be 'assignment' or 'guided_session'



class AssignmentResult(BaseModel):

    assignment_id: str

    answers: list


class SupportPackPayload(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    content: dict


class ReportRequest(BaseModel):
    students: Optional[List[str]] = None
    start: Optional[str] = None
    end: Optional[str] = None
    format: str = 'json'


class NotificationRuleRequest(BaseModel):
    type: str
    config: dict


class SharedNoteRequest(BaseModel):
    student: str
    content: str
    shared_with: List[str]


class ConsentRequest(BaseModel):
    username: str
    guardian: str
    scope: List[str]



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

    chatbot_response = chatbot_logic.chatbot.process_sentence(current_user.username, sentence.text, current_user.role)

    data_manager.log_interaction(current_user.username, sentence.text, chatbot_response)

    return {

        "sentence": sentence.text,

        "processed_sentence": chatbot_response

    }


@app.post("/speech-to-text")
async def speech_to_text(language: str = Form('es'), label: str | None = Form(None), file: UploadFile = File(...), current_user: schemas.User = Depends(auth.get_current_active_user)):
    if current_user.role in ["child", "student"]:
        consent_manager.ensure_consent(current_user.username)
    saved = audio_manager.save_uploaded_audio(current_user.username, file, label)
    transcription = audio_manager.transcribe_audio(saved['stored_path'], language)
    response_meta = {k: v for k, v in saved.items() if k != 'stored_path'}
    consent_manager.log_audit('speech_to_text', current_user.username, metadata={'audio_id': saved['id']})
    return {"audio": response_meta, "transcription": transcription}


@app.get("/audio-uploads")
async def list_audio_uploads(current_user: schemas.User = Depends(auth.get_current_active_user)):
    uploads = audio_manager.list_audio_uploads()
    if current_user.role not in ["teacher", "therapist", "parent"]:
        uploads = [u for u in uploads if u['username'] == current_user.username]
    for upload in uploads:
        upload.pop('stored_path', None)
    return uploads


@app.post("/audio-cues")
async def create_audio_cue(title: str = Form(...), tags: str = Form(''), description: str | None = Form(None), file: UploadFile = File(...), current_user: schemas.User = Depends(auth.get_current_active_user)):
    if current_user.role not in ["teacher", "therapist"]:
        raise HTTPException(status_code=403, detail="Solo docentes o terapeutas pueden crear pistas de audio.")
    tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
    cue = audio_manager.register_audio_cue(title, tag_list, current_user.username, file, description)
    consent_manager.log_audit('create_audio_cue', current_user.username, metadata={'cue_id': cue['id']})
    cue.pop('stored_path', None)
    return cue


@app.get("/audio-cues")
async def list_audio_cues(current_user: schemas.User = Depends(auth.get_current_active_user)):
    cues = audio_manager.list_audio_cues()
    for cue in cues:
        cue.pop('stored_path', None)
    return cues


@app.get("/audio-cues/{cue_id}")
async def get_audio_cue(cue_id: str, current_user: schemas.User = Depends(auth.get_current_active_user)):
    cue = audio_manager.get_audio_cue(cue_id)
    if not cue:
        raise HTTPException(status_code=404, detail="Pista no encontrada")
    if not os.path.exists(cue['stored_path']):
        raise HTTPException(status_code=404, detail="Archivo de audio no disponible")
    return FileResponse(cue['stored_path'], media_type='audio/mpeg', filename=cue['filename'])



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

    assignment_meta = None
    if session_words.assignment_id:
        assignments = data_manager.get_assignments()
        match = next((a for a in assignments if a.get('timestamp') == session_words.assignment_id), None)
        if match:
            assignment_meta = {
                'type': match.get('type', 'guided_session'),
                'task': match.get('task'),
                'title': match.get('title'),
                'target_words': match.get('words')
            }
    if not assignment_meta and (session_words.title or session_words.task):
        assignment_meta = {
            'type': 'guided_session',
            'task': session_words.task,
            'title': session_words.title,
            'target_words': session_words.words
        }

    chatbot_logic.chatbot.start_guided_session(current_user.username, session_words.words, assignment_meta)

    return {"message": "Guided session started successfully."}



@app.post("/logout")

async def logout(current_user: schemas.User = Depends(auth.get_current_active_user)):

    chatbot_logic.chatbot.clear_user_game_state(current_user.username)

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

    if current_user.role not in ["student", "child"]:

        raise HTTPException(status_code=403, detail="Only students can submit assignment results.")

    assignments = data_manager.get_assignments()

    matching_assignment = next((assignment for assignment in assignments if assignment.get('timestamp') == result.assignment_id), None)

    if not matching_assignment:

        raise HTTPException(status_code=404, detail="Assignment not found.")

    data_manager.save_assignment_result(current_user.username, result.model_dump())

    return {"message": "Assignment results saved successfully."}



@app.get("/notes")

async def get_notes(current_user: schemas.User = Depends(auth.get_current_active_user)):

    return data_manager.get_notes()


def _pack_content_from_payload(payload: SupportPackPayload) -> dict:
    content = copy.deepcopy(payload.content)
    metadata = content.setdefault('metadata', {})
    if payload.title:
        metadata['title'] = payload.title
    if payload.description:
        metadata['description'] = payload.description
    return content


@app.get("/support-packs")
async def list_support_packs(current_user: schemas.User = Depends(auth.get_current_active_user)):
    return support_pack_manager.list_packs()


@app.post("/support-packs")
async def create_support_pack(payload: SupportPackPayload, current_user: schemas.User = Depends(auth.get_current_active_user)):
    if current_user.role not in ["teacher", "therapist"]:
        raise HTTPException(status_code=403, detail="Solo docentes o terapeutas pueden crear packs")
    content = _pack_content_from_payload(payload)
    pack = support_pack_manager.save_pack(current_user.username, content)
    consent_manager.log_audit('create_support_pack', current_user.username, metadata={'pack_id': pack['id']})
    return pack


@app.put("/support-packs/{pack_id}")
async def update_support_pack(pack_id: str, payload: SupportPackPayload, current_user: schemas.User = Depends(auth.get_current_active_user)):
    if current_user.role not in ["teacher", "therapist"]:
        raise HTTPException(status_code=403, detail="No autorizado")
    content = _pack_content_from_payload(payload)
    pack = support_pack_manager.save_pack(current_user.username, content, pack_id=pack_id)
    consent_manager.log_audit('update_support_pack', current_user.username, metadata={'pack_id': pack_id})
    return pack


@app.delete("/support-packs/{pack_id}")
async def delete_support_pack(pack_id: str, current_user: schemas.User = Depends(auth.get_current_active_user)):
    if current_user.role not in ["teacher", "therapist"]:
        raise HTTPException(status_code=403, detail="No autorizado")
    support_pack_manager.delete_pack(pack_id)
    consent_manager.log_audit('delete_support_pack', current_user.username, metadata={'pack_id': pack_id})
    return {"message": "Pack eliminado"}


@app.post("/support-packs/{pack_id}/activate")
async def activate_support_pack(pack_id: str, current_user: schemas.User = Depends(auth.get_current_active_user)):
    if current_user.role not in ["teacher", "therapist"]:
        raise HTTPException(status_code=403, detail="No autorizado")
    support_pack_manager.activate_pack(pack_id)
    chatbot_logic.chatbot.reload_support_content()
    consent_manager.log_audit('activate_support_pack', current_user.username, metadata={'pack_id': pack_id})
    return {"message": "Pack activado"}



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
@app.post("/shared-notes")
async def create_shared_note(payload: SharedNoteRequest, current_user: schemas.User = Depends(auth.get_current_active_user)):
    if current_user.role not in ['teacher', 'therapist', 'parent']:
        raise HTTPException(status_code=403, detail="No autorizado")
    note = sharing_manager.create_shared_note(current_user.username, payload.student, payload.content, payload.shared_with)
    consent_manager.log_audit('create_shared_note', current_user.username, metadata={'note_id': note['id']})
    return note


@app.get("/shared-notes")
async def get_shared_notes(current_user: schemas.User = Depends(auth.get_current_active_user)):
    return sharing_manager.list_shared_notes(current_user.username)


@app.post("/shared-notes/{note_id}/ack")
async def acknowledge_shared_note(note_id: str, current_user: schemas.User = Depends(auth.get_current_active_user)):
    sharing_manager.acknowledge_note(note_id, current_user.username)
    consent_manager.log_audit('ack_shared_note', current_user.username, metadata={'note_id': note_id})
    return {"message": "Nota marcada como leída"}


@app.delete("/shared-notes/{note_id}")
async def delete_shared_note(note_id: str, current_user: schemas.User = Depends(auth.get_current_active_user)):
    sharing_manager.delete_shared_note(note_id, current_user.username)
    consent_manager.log_audit('delete_shared_note', current_user.username, metadata={'note_id': note_id})
    return {"message": "Nota eliminada"}


def _filter_students_for_user(requested: Optional[List[str]], current_user: schemas.User) -> Optional[List[str]]:
    if current_user.role in ["student", "child"]:
        return [current_user.username]
    if current_user.role == 'parent':
        allowed = set(current_user.students or [])
        if not requested:
            return list(allowed)
        return [student for student in requested if student in allowed]
    if current_user.role in ['teacher', 'therapist'] and current_user.students:
        allowed = set(current_user.students)
        if requested:
            return [student for student in requested if student in allowed]
        return list(allowed)
    return requested


@app.post("/reports/generate")
async def generate_report(data: ReportRequest, current_user: schemas.User = Depends(auth.get_current_active_user)):
    students = _filter_students_for_user(data.students, current_user)
    report = report_manager.generate_report(students, data.start, data.end)
    consent_manager.log_audit('generate_report', current_user.username, metadata={'students': students})
    return report


@app.post("/reports/export")
async def export_report(data: ReportRequest, current_user: schemas.User = Depends(auth.get_current_active_user)):
    students = _filter_students_for_user(data.students, current_user)
    report = report_manager.generate_report(students, data.start, data.end)
    exported = report_manager.export_report(report, data.format)
    consent_manager.log_audit('export_report', current_user.username, metadata={'report_id': exported['id']})
    return exported


@app.get("/reports")
async def list_reports_meta(current_user: schemas.User = Depends(auth.get_current_active_user)):
    return report_manager.list_reports()


@app.get("/reports/{report_id}")
async def download_report(report_id: str, current_user: schemas.User = Depends(auth.get_current_active_user)):
    path = report_manager.get_report_file(report_id)
    if not path:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    return FileResponse(path, filename=os.path.basename(path))


# Notification & alerts

@app.get("/notification-rules")
async def list_notification_rules(current_user: schemas.User = Depends(auth.get_current_active_user)):
    if current_user.role not in ['teacher', 'therapist', 'parent']:
        raise HTTPException(status_code=403, detail="No autorizado")
    return notification_manager.list_rules()


@app.post("/notification-rules")
async def create_notification_rule(rule: NotificationRuleRequest, current_user: schemas.User = Depends(auth.get_current_active_user)):
    if current_user.role not in ['teacher', 'therapist', 'parent']:
        raise HTTPException(status_code=403, detail="No autorizado")
    created = notification_manager.create_rule(rule.type, current_user.username, rule.config)
    consent_manager.log_audit('create_notification_rule', current_user.username, metadata={'rule_id': created['id']})
    return created


@app.delete("/notification-rules/{rule_id}")
async def delete_notification_rule(rule_id: str, current_user: schemas.User = Depends(auth.get_current_active_user)):
    if current_user.role not in ['teacher', 'therapist', 'parent']:
        raise HTTPException(status_code=403, detail="No autorizado")
    notification_manager.delete_rule(rule_id)
    consent_manager.log_audit('delete_notification_rule', current_user.username, metadata={'rule_id': rule_id})
    return {"message": "Regla eliminada"}


@app.post("/alerts/run")
async def run_alerts(current_user: schemas.User = Depends(auth.get_current_active_user)):
    if current_user.role not in ['teacher', 'therapist', 'parent']:
        raise HTTPException(status_code=403, detail="No autorizado")
    alerts = notification_manager.evaluate_rules()
    return {"alerts": alerts}


@app.get("/alerts")
async def list_alerts(current_user: schemas.User = Depends(auth.get_current_active_user)):
    if current_user.role not in ['teacher', 'therapist', 'parent']:
        raise HTTPException(status_code=403, detail="No autorizado")
    return notification_manager.list_alerts()


@app.post("/consents")
async def record_consent(request: ConsentRequest, current_user: schemas.User = Depends(auth.get_current_active_user)):
    if current_user.role not in ['parent', 'teacher', 'therapist']:
        raise HTTPException(status_code=403, detail="No autorizado para registrar consentimientos")
    consent = consent_manager.record_consent(request.username, request.guardian, request.scope)
    consent_manager.log_audit('record_consent', current_user.username, metadata={'username': request.username})
    return consent


@app.get("/consents/{username}")
async def get_consent(username: str, current_user: schemas.User = Depends(auth.get_current_active_user)):
    if current_user.role not in ['parent', 'teacher', 'therapist'] and current_user.username != username:
        raise HTTPException(status_code=403, detail="No autorizado")
    consent = consent_manager.get_consent(username)
    if not consent:
        raise HTTPException(status_code=404, detail="Consentimiento no encontrado")
    return consent


@app.post("/data/export")
async def export_user_data(username: str, current_user: schemas.User = Depends(auth.get_current_active_user)):
    if current_user.role not in ['parent', 'teacher', 'therapist'] and current_user.username != username:
        raise HTTPException(status_code=403, detail="No autorizado")
    path = consent_manager.export_user_data(username)
    consent_manager.log_audit('export_user_data', current_user.username, metadata={'username': username})
    return FileResponse(path, filename=os.path.basename(path))


@app.delete("/data/{username}")
async def delete_user_data(username: str, current_user: schemas.User = Depends(auth.get_current_active_user)):
    if current_user.role not in ['parent', 'teacher', 'therapist'] and current_user.username != username:
        raise HTTPException(status_code=403, detail="No autorizado")
    consent_manager.delete_user_data(username)
    return {"message": "Datos eliminados"}
