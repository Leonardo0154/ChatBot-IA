# Guía técnica (para equipos externos)

Resumen en español de arquitectura, módulos y endpoints para que otro equipo pueda mantener o extender ChatBot-IA.

## Visión general
- **Backend:** FastAPI en `src/`, sirve API REST + estáticos de la SPA construida (`Frontend/chatbot-frontend/dist`) bajo `/static`.
- **Frontend:** SPA Vue 3 + Vite en `Frontend/chatbot-frontend`.
- **Datos:** JSON en `data/` (asignaciones, notas, logs, modelos spaCy). Pictogramas de ARASAAC en `data/raw/ARASAAC_ES`.
- **Modelos NLP:** spaCy (intención/emoción) y T5 finetuneado para texto generativo.

## Estructura de backend (src/)
- `src/api/main.py`: monta FastAPI, rutas, CORS, estáticos (`/static`).
- `src/security/`:
  - `security.py`: OAuth2 password, generación/validación de tokens.
  - `schemas.py`: modelos Pydantic (User, Token, Assignment, etc.).
  - `database.py`: persistencia simple basada en JSON.
- `src/app/`:
  - `chatbot_logic.py`: pipeline conversacional (contexto, T5, spaCy, plantillas guiadas, pistas con pictos).
  - `data_manager.py`: carga/guarda JSON (asignaciones, resultados, soporte, logs).
  - `audio_manager.py`: subida/guardado de audios para STT/TTS.
  - `support_pack_manager.py`: CRUD de paquetes de soporte/plantillas.
  - `report_manager.py`: generación/exportación de reportes.
  - `notification_manager.py`, `sharing_manager.py`, `consent_manager.py`: reglas de alertas, notas compartidas, consentimiento y privacidad.
- `src/model/`:
  - `intent_classifier.py` y `emotion_classifier.py`: textcat spaCy.
  - `picto_encoder.py`, `nlp_utils.py`: utilidades de vocabulario/pictogramas.
- `src/scripts/process_data.py`: preparación de datos de pictos (ARASAAC → JSON procesado).

## Estructura de frontend (Frontend/chatbot-frontend)
- `src/views/`: vistas principales (login, registro, chat, asignaciones, sesiones guiadas, memoria, etc.).
  - `ChatbotView.vue`: chat, STT local, TTS, galería/sugerencias de pictos.
  - `AssignmentsView.vue` / `AssignmentDetailView.vue`: listado y ejecución (adivinanzas muestran solo el pictograma, no la respuesta).
- `src/services/api.js`: cliente Axios hacia el backend (usa `VITE_API_BASE_URL`).
- `public/` + `src/assets/`: estáticos y recursos.

## Flujo de pictogramas
- Fuente ARASAAC en `data/raw/ARASAAC_ES`; procesado en JSON con palabras clave.
- Backend expone `GET /pictograms` y `GET /pictograms/{path}` (sirve imagen).
- `/process` retorna `processed_sentence` con `{ word, pictogram/path }`; frontend deduplica y muestra pictos junto al texto.
- En asignaciones, solo se muestra el pictograma y se oculta la palabra esperada (sin exponerla en UI ni en atributos `alt`).

## Endpoints clave (Swagger: `/docs`, OpenAPI JSON: `/openapi.json`)
- **Auth y usuarios:**
  - `POST /token` → login OAuth2 (usar `Authorization: Bearer <token>` en llamadas siguientes).
  - `POST /users/` → crear usuario (roles: `child`, `student`, `parent`, `teacher`, `therapist`).
  - `GET /users/me` → perfil actual.
- **Chat y NLP:**
  - `POST /process` → procesa texto, devuelve `processed_sentence`, `intent`, `emotion`, `suggested_pictograms`.
  - `POST /speech-to-text` → subir audio y recibir transcripción (si está habilitado).
- **Pictogramas:**
  - `GET /pictograms` → listado con palabras clave.
  - `GET /pictograms/{path}` → imagen concreta.
- **Asignaciones y sesiones guiadas:**
  - `GET /assignments`, `GET /assignments/{id}` → obtener tareas/sesiones.
  - `POST /assignment-results` → registrar respuestas de estudiante.
  - `POST /guided-session/start` → lanzar sesión guiada a partir de asignación.
- **Soporte y packs:**
  - `GET/POST /support-packs` y `POST /support-packs/{id}/activate` → plantillas de apoyo.
  - `GET/POST /shared-notes` → notas colaborativas.
- **Reportes/alertas:**
  - `POST /reports/generate`, `GET /reports/export` → informes JSON/CSV.
  - `GET/POST /notification-rules`, `GET/POST /alerts` → reglas y alertas.

## Roles y permisos (resumen)
- `child`/`student`: pueden ejecutar asignaciones, usar chat/STT; no crean tareas.
- `teacher`/`therapist`/`parent`: crean asignaciones/sesiones, revisan resultados y notas; no ejecutan como estudiantes.
- El backend valida en endpoints sensibles (ej. `POST /assignment-results` solo para roles de estudiante).

## Consideraciones de seguridad y UX
- No revelar respuestas en UI (asignaciones). Pictos sí, palabras no.
- Usar HTTPS para micrófono/TTS en navegador.
- Logs y datos en `data/` pueden contener información sensible; limpiar con `scripts/reset_data.ps1` antes de publicar.

## Cómo extender
- **Nuevas intenciones/emociones:** reentrenar spaCy en `src/model/intent_textcat` / `emotion_textcat` y ajustar `nlp_utils.py`.
- **Nuevos escenarios guiados:** añadir plantillas en `data/support_content.json` o vía endpoints de `support_packs`.
- **Nuevos juegos/vistas frontend:** crear vistas en `src/views/` y rutas en `src/router/` consumiendo los mismos endpoints.

## Build y despliegue (resumen)
- Backend: `uvicorn src.api.main:app --host 0.0.0.0 --port 8000` (usar venv y `pip install -r requirements.txt`).
- Frontend: `npm install && npm run build` en `Frontend/chatbot-frontend`; el backend sirve `dist` en `/static`.
- Documentación de API disponible siempre en `/docs` (Swagger) y `/openapi.json`.
