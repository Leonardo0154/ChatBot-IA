# ChatBot Contextual Response Plan

This note captures the agreed direction for refining the chatbot so every response stays aligned with the AAC-focused user stories.

## 1. Assignment/Gestión Context Injection
- When a user is in a guided session or pictogram game, persist `current_mode`, `objective`, `target_words`, and `author_notes` inside the in-memory `game_state`.
- Fetch summary metadata (title, task description, optional support hints) for the active assignment/guided session from `data/assignments.json` so the conversational prompt mentions the same objective the teacher defined.

## 2. Curated Support Packs
- Introduce `data/support_content.json` containing therapist-authored encouragement phrases, sensory-friendly explanations, and short hints keyed by assignment type and emotion.
- Provide helper loaders in `src/app/data_manager.py` to read/support safe defaults when the file is missing or partially defined.

## 3. Scripted Fallback Mode
- Add a configuration flag (initially derived from user role `child` or `student` age tier) that routes responses through deterministic templates when the student is inside a guided session.
- Templates explicitly reference pictograms ("Mira el pictograma de {word}") and use the curated phrases above to guarantee age-appropriate output even without transformer inference.

## 4. Progress-Aware Personalization
- Extend `data_manager` with `get_user_progress_summary(username)` that aggregates word usage counts and last-interaction timestamps from `data/logs/usage_logs.json`.
- Surface highlights (e.g., "Ya practicaste 'comer' 3 veces") in both scripted and transformer prompts.

## 5. Transformer Prompt Hygiene
- Remove the Wikipedia dependency from `chatbot_logic.py` and replace it with:
  - Assignment context snippet (task description + target words).
  - Support-pack hints for the relevant type (`assignment` vs `guided_session`).
  - Optional progress summary.
- Keep the T5 model for open-ended dialog outside structured sessions, but prefer scripted outputs when the student is mid-activity.

## 6. Testing & Documentation
- Add unit tests that cover: (a) support-pack loading defaults, (b) progress summary aggregation, (c) transformer prompt composition including assignment metadata, and (d) scripted fallback selection.
- Update README/docs to describe the new flow and how it supports HU1–HU10.
