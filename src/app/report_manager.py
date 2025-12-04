import csv
import json
import os
import uuid
from collections import Counter
from datetime import datetime
from typing import Dict, List, Optional

from src.app import data_manager
from src.model import nlp_utils

REPORTS_DIR = os.path.join('data', 'reports')
REPORT_META = os.path.join(REPORTS_DIR, 'reports.json')


def _ensure_dir():
    os.makedirs(REPORTS_DIR, exist_ok=True)


def _load_meta() -> List[Dict]:
    if not os.path.exists(REPORT_META):
        return []
    with open(REPORT_META, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def _save_meta(items: List[Dict]):
    _ensure_dir()
    with open(REPORT_META, 'w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


def _filter_logs(student_ids: Optional[List[str]], start: Optional[str], end: Optional[str]) -> List[Dict]:
    if not os.path.exists(data_manager.LOG_FILE):
        return []
    with open(data_manager.LOG_FILE, 'r', encoding='utf-8') as f:
        logs = [json.loads(line) for line in f if line.strip()]
    if student_ids:
        logs = [log for log in logs if log.get('username') in student_ids]
    if start:
        start_dt = datetime.fromisoformat(start)
        logs = [log for log in logs if datetime.fromisoformat(log['timestamp']) >= start_dt]
    if end:
        end_dt = datetime.fromisoformat(end)
        logs = [log for log in logs if datetime.fromisoformat(log['timestamp']) <= end_dt]
    return logs


def generate_report(student_ids: Optional[List[str]] = None, start: Optional[str] = None, end: Optional[str] = None) -> Dict:
    logs = _filter_logs(student_ids, start, end)
    total = len(logs)
    words = [item['word'] for log in logs for item in log.get('processed_sentence', [])]
    pictos = [item['pictogram'] for log in logs for item in log.get('processed_sentence', []) if item.get('pictogram')]
    categories = Counter()
    for log in logs:
        for item in log.get('processed_sentence', []):
            path = item.get('pictogram')
            if path:
                pictogram = next((pic for pic in nlp_utils.pictograms if pic.get('path') == path), None)
                if pictogram:
                    for tag in pictogram.get('tags', []):
                        categories[tag] += 1
    summary = {
        'filters': {
            'students': student_ids,
            'start': start,
            'end': end
        },
        'total_interactions': total,
        'unique_words': len(set(words)),
        'top_words': Counter(words).most_common(10),
        'top_pictograms': Counter(pictos).most_common(10),
        'top_categories': categories.most_common(5)
    }
    return summary


def export_report(report: Dict, fmt: str = 'json') -> Dict:
    _ensure_dir()
    report_id = str(uuid.uuid4())
    filename = f"report_{report_id}.{ 'csv' if fmt == 'csv' else 'json'}"
    file_path = os.path.join(REPORTS_DIR, filename)
    if fmt == 'csv':
        rows = [
            ['Metric', 'Value'],
            ['Total Interactions', report['total_interactions']],
            ['Unique Words', report['unique_words']],
        ]
        rows.extend([[f"Top Word: {word}", freq] for word, freq in report['top_words']])
        rows.extend([[f"Top Pictogram: {path}", freq] for path, freq in report['top_pictograms']])
        with open(file_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(rows)
    else:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
    meta = _load_meta()
    meta.append({
        'id': report_id,
        'file': filename,
        'created_at': datetime.utcnow().isoformat(),
        'format': fmt,
        'filters': report.get('filters', {})
    })
    _save_meta(meta)
    return {'id': report_id, 'file': filename, 'path': file_path, 'format': fmt}


def list_reports() -> List[Dict]:
    return _load_meta()


def get_report_file(report_id: str) -> Optional[str]:
    meta = next((item for item in _load_meta() if item['id'] == report_id), None)
    if not meta:
        return None
    path = os.path.join(REPORTS_DIR, meta['file'])
    if os.path.exists(path):
        return path
    return None
