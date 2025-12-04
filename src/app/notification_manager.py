import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, List

from src.app import data_manager

RULES_FILE = os.path.join('data', 'notification_rules.json')
ALERTS_FILE = os.path.join('data', 'notifications.json')


def _load(file_path: str) -> List[Dict]:
    if not os.path.exists(file_path):
        return []
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def _save(file_path: str, data: List[Dict]):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def list_rules() -> List[Dict]:
    return _load(RULES_FILE)


def create_rule(rule_type: str, created_by: str, config: Dict) -> Dict:
    rule = {
        'id': str(uuid.uuid4()),
        'type': rule_type,
        'config': config,
        'created_by': created_by,
        'created_at': datetime.utcnow().isoformat()
    }
    rules = list_rules()
    rules.append(rule)
    _save(RULES_FILE, rules)
    return rule


def delete_rule(rule_id: str):
    rules = [rule for rule in list_rules() if rule['id'] != rule_id]
    _save(RULES_FILE, rules)


def list_alerts() -> List[Dict]:
    return _load(ALERTS_FILE)


def _record_alert(alert: Dict):
    alerts = list_alerts()
    alerts.append(alert)
    _save(ALERTS_FILE, alerts)


def evaluate_rules() -> List[Dict]:
    alerts = []
    rules = list_rules()
    if not rules:
        return []
    if not os.path.exists(data_manager.LOG_FILE):
        entries = []
    else:
        with open(data_manager.LOG_FILE, 'r', encoding='utf-8') as f:
            entries = [json.loads(line) for line in f if line.strip()]
    for rule in rules:
        if rule['type'] == 'inactivity':
            alerts.extend(_check_inactivity(rule, entries))
        elif rule['type'] == 'word_target':
            alerts.extend(_check_word_target(rule, entries))
    for alert in alerts:
        _record_alert(alert)
    return alerts


def _check_inactivity(rule: Dict, entries: List[Dict]) -> List[Dict]:
    days = rule['config'].get('threshold_days', 3)
    students = rule['config'].get('students') or []
    cutoff = datetime.utcnow() - timedelta(days=days)
    alerts = []
    for student in students:
        last_log = next((entry for entry in sorted(entries, key=lambda x: x['timestamp'], reverse=True)
                         if entry.get('username') == student), None)
        if not last_log or datetime.fromisoformat(last_log['timestamp']) < cutoff:
            alerts.append({
                'id': str(uuid.uuid4()),
                'type': 'inactivity',
                'message': f"{student} no ha practicado en {days} días",
                'created_at': datetime.utcnow().isoformat(),
                'rule_id': rule['id'],
                'student': student
            })
    return alerts


def _check_word_target(rule: Dict, entries: List[Dict]) -> List[Dict]:
    target_word = rule['config'].get('word')
    threshold = rule['config'].get('threshold', 5)
    students = rule['config'].get('students') or []
    alerts = []
    for student in students:
        count = 0
        for entry in entries:
            if entry.get('username') != student:
                continue
            for token in entry.get('processed_sentence', []):
                if token.get('word', '').lower() == (target_word or '').lower():
                    count += 1
        if count >= threshold:
            alerts.append({
                'id': str(uuid.uuid4()),
                'type': 'word_target',
                'message': f"{student} alcanzó {count} usos de '{target_word}'",
                'created_at': datetime.utcnow().isoformat(),
                'rule_id': rule['id'],
                'student': student
            })
    return alerts
