**Project Setup Guide: ChatBot-IA**

Este documento explica cómo configurar el proyecto `ChatBot-IA`, instalar dependencias y ejecutar la aplicación.

**Prerequisitos**
- **Git**: Para clonar el repositorio.
- **Python**: Versión 3.10+ recomendada.
- **Node.js + npm**: Necesario para el frontend Vite/Vue. Usa Node 18+ (LTS) para evitar errores de dependencias.
- **Git LFS (Large File Storage)**: Para manejar archivos grandes.
    - **Instalación:**
        - **Debian/Ubuntu (WSL/Linux):** `sudo apt-get install git-lfs`
        - **macOS (Homebrew):** `brew install git-lfs`
        - **Windows:** Descargar desde `https://git-lfs.com/` o instalar con Git for Windows.
    - **Post-instalación (ejecutar una vez):** `git lfs install`

**Step 1: Clone the Repository**
- **Clone:** `git clone https://github.com/Leonardo0154/ChatBot-IA.git`
- **Enter repo:** `cd ChatBot-IA`

**Step 2: Pull Git LFS Objects**
- **Comando:** `git lfs pull`
- **Nota:** Si clonaste antes de que se migrara el historial a LFS, puede que necesites re-clonar o rebasear la rama local.

**Step 3: Configure Git Line Endings (Recommended)**
- **Linux/WSL/macOS:** `git config --global core.autocrlf input`
- **Windows:** `git config --global core.autocrlf true`

**Step 4: Create and Activate a Python Virtual Environment**
- **Create venv:** `python -m venv venv`
- **Activate:**
    - **Linux/macOS (Bash/Zsh):** `source venv/bin/activate`
    - **Windows (CMD):** `.\venv\Scripts\activate.bat`
    - **Windows (PowerShell):** `.\venv\Scripts\Activate.ps1`

**Step 5: Install Python Dependencies**
- **Instalar:** `pip install -r requirements.txt`
- **Nota:** `torch` puede tardar; si falla en Windows, instala la rueda CPU como se indica en el README raíz.

**Step 6: (Opcional) Descargar manualmente el modelo spaCy**
- Solo si el paso anterior no lo instala automáticamente: `python -m spacy download es_core_news_sm`

**Step 7: Run the FastAPI Server**
- **Iniciar backend:** `uvicorn src.api.main:app --host 127.0.0.1 --port 8000`
- **URL de servicio:** `http://127.0.0.1:8000`

**Step 8: Setup and Run the Frontend (Vite + Vue 3)**
- **Variables:** `cd Frontend/chatbot-frontend` y `cp .env.example .env` (ajusta `VITE_API_BASE_URL` si la API no está en `http://localhost:8000`).
- **Instalar deps:** `npm install`
- **Desarrollo:** `npm run dev` (abre el enlace que muestra Vite, p. ej. `http://localhost:5173`).
- **Producción:** `npm run build` para generar `dist/`. El backend sirve `dist` automáticamente bajo `/static` al levantar Uvicorn, por lo que el frontend queda disponible en `http://localhost:8000/`.

**Step 9: Create User Accounts (First Time Setup)**
- **Nota:** Para funciones como seguimiento de progreso y sesiones, crea usuarios con `curl`, Postman o Insomnia mientras el servidor está corriendo.
- **Ejemplos `curl`:**
    - **Student:**
        `curl -X POST "http://127.0.0.1:8000/users/" -H "Content-Type: application/json" -d '{"username": "student1", "password": "password", "role": "child"}'`
    - **Teacher (asociado a student1):**
        `curl -X POST "http://127.0.0.1:8000/users/" -H "Content-Type: application/json" -d '{"username": "teacher1", "password": "password", "role": "teacher", "students": ["student1"]}'`
    - **Parent (asociado a student1):**
        `curl -X POST "http://127.0.0.1:8000/users/" -H "Content-Type: application/json" -d '{"username": "parent1", "password": "password", "role": "parent", "students": ["student1"]}'`
    - **Therapist:**
        `curl -X POST "http://127.0.0.1:8000/users/" -H "Content-Type: application/json" -d '{"username": "therapist1", "password": "password", "role": "therapist", "students": ["student1"]}'`

### Chatbot Architecture

The chatbot uses a hybrid approach to generate intelligent and conversational responses.

- **Pre-trained Language Model:** The core of the chatbot is a pre-trained T5 model (`mrm8488/spanish-t5-small-sqac-for-qa`) that has been fine-tuned for Spanish question answering. This model is used to generate text responses to user queries.
- **Context + Support Packs:** Before hitting the model, `Chatbot._build_assignment_context()` merges assignment metadata, per-student progress summaries (`get_user_progress_summary`) and curated templates from `data/support_content.json`. The support packs contain deterministic prompts for greetings, hints, and scripted cues aligned with the AAC user stories.
- **"Smart" Pictogram Integration:** After the T5 model generates a response, the `spaCy` library is used to perform Natural Language Processing (NLP) on the text. The chatbot identifies the key concepts (nouns and verbs) in the response and replaces them with pictograms. This provides a rich and intuitive user experience that enhances understanding.
- **Scripted fallback for children:** When a `child`/`student` is inside a game or guided session, `_maybe_scripted_response()` tries to respond using the curated templates (success phrases, extra hints, mention of pictograms). Only if no template matches do we invoke the T5 pipeline, keeping the answers friendly and safe.
- **Word association cues:** The `related_vocab` section of `support_content.json` stores therapist-approved associations (e.g., `caballo` → “heno”, “herradura”). If a word is not present, `_related_vocab_response()` falls back to the extra keywords that come with the ARASAAC pictogram so single-word inputs still yield friendly hints instead of repeated tokens.
- **Game and Session Logic:** The chatbot also includes logic for interactive games and guided sessions, which are managed within the `Chatbot` class. Guided sessions reuse the assignment infrastructure so therapists and parents can monitor progress without executing tasks themselves.

### Backend TB2 Features

### NLP contextual y dinámico
- **Clasificador de intenciones (`src/model/intent_classifier.py`)**: modelo `textcat` de spaCy con diez etiquetas (rutina_escolar, terapia_habla, juego_cooperativo, factual_pregunta, consentimiento, etc.). Permite enrutar los escenarios correctos aunque la frase llegue parafraseada.
- **Clasificador emocional (`src/model/emotion_classifier.py`)**: identifica si el niño está triste, ansioso, enojado, orgulloso, calmo o neutral. El tono alimenta las respuestas empáticas y los prompts de T5 cuando se generan pasos dinámicos.
- **Plantillas dinámicas**: los escenarios marcados con `dynamic_steps` invocan el modelo T5 para producir tres pasos cortos con el tono detectado (“Escenario: autonomia_lavar_manos, tono: calmo…”). La estructura sigue siendo segura, pero el contenido se adapta a la consulta del niño.
- **Resúmenes automáticos**: `data_manager.get_recent_interactions()` resume los pictogramas practicados y los incluye en sesiones de terapia del habla para cumplir con el requisito de “resumen + reformulación”.
- **Extracción semántica en juegos**: `_semantic_card_match` recorre `related_vocab` para detectar palabras clave (melena → león, pedalear → bicicleta) incluso si el niño describe la carta sin decir su nombre.
- **Consentimiento registrado**: cuando se detecta la intención `consentimiento`, `chatbot_logic` registra la solicitud en `data/logs/audit_logs.json` y personaliza la respuesta con la acción solicitada (“puedo descansar…”, “me dejas llamar…”).

### Escenarios educativos y plantillas recomendadas
Cada escenario se implementa como un `support_pack` diferente para que el equipo active o desactive contenidos sin reiniciar el backend. Se sugiere la siguiente estructura básica para cada plantilla dentro del pack:

```json
{
    "id": "plantilla_id",
    "trigger": "palabra_clave o intent",
    "response": "Frase accesible con pictogramas {{picto}}",
    "mode": "guided|free|game",
    "emotion": "calm|excited|neutral"
}
```

#### 1. Rutina escolar guiada
- **Objetivo:** Preparar al estudiante para la jornada (antes, durante y después de clase) reforzando materiales, emociones y pasos esperados.
- **Contenido sugerido:** saludos (“Buenos días, revisemos tu mochila”), listas cortas de tareas (“1. Guarda el cuaderno. 2. Lleva tus colores”), escalas emocionales con pictogramas simples.
- **Triggers útiles:** `"trigger": "mochila"`, `"trigger": "como me siento"`, `"trigger": "lista de clase"`.
- **KPIs asociados:** registro de asignaciones completadas y alertas de inactividad para detectar días sin rutina.
- **NLP aplicado:** cuando el clasificador detecta `rutina_escolar`, T5 genera los pasos en tono `calmo` aunque el niño pregunte “¿qué debo llevar para ciencias?” sin mencionar “rutina”.

#### 2. Sesiones de terapia del habla
- **Objetivo:** Practicar fonemas y turn-taking con apoyo visual mientras se reduce la carga cognitiva.
- **Contenido sugerido:** pasos “Respira profundo”, “Mira el pictograma de la boca abierta”, “Repite pa-pa-pa”, descansos programados (“Toma agua, avísame cuando quieras seguir”).
- **Extras técnicos:** se pueden mezclar cues de audio para que el niño escuche el sonido objetivo y plantillas que recuerdan usar el micro para repetir.
- **Registro:** usa `/shared-notes` para que terapeuta y familia documenten mejoras por sesión.
- **NLP aplicado:** `_summarize_recent_practice` toma las últimas palabras pronunciadas desde `usage_logs.json` y el clasificador `terapia_habla` fuerza la regeneración dinámica de los pasos de práctica.

#### 3. Juego cooperativo o familiar
- **Objetivo:** Fomentar habilidades socioemocionales durante juegos como memoria, adivinanzas o historias compartidas.
- **Contenido sugerido:** preguntas abiertas moderadas (“¿Qué harías si tu amigo está triste?”), recordatorios de turnos (“Ahora te toca mirar dos cartas”) y mensajes calmantes si hay frustración.
- **Integración:** `mode="game"` ayuda a `chatbot_logic` a priorizar respuestas determinísticas antes del modelo T5.
- **Alertas:** regla de vocabulario puede avisar cuando el niño desbloquea nuevas palabras del juego.
- **NLP aplicado:** `_semantic_card_match` usa `related_vocab` para mapear descripciones (“tiene melena y ruge”) a un pictograma (`león`), permitiendo validar adivinanzas aunque la palabra no sea literal.

#### 4. Autonomía diaria
- **Objetivo:** Guiar actividades de vida diaria (higiene, alimentación, vestirse) entregando instrucciones paso a paso.
- **Contenido sugerido:** plantillas secuenciales (“Abre el grifo”, “Frota tus manos”, “Seca con la toalla”), frases de refuerzo positivo y alternativas cuando falta un objeto (“Si no encuentras el cepillo azul, usa el verde y dime cómo se siente”).
- **Vinculación con módulos:** combina reportes (para ver frecuencia de rutinas) con notificaciones (“alerta si pasan 3 días sin registrar higiene matutina”).
- **NLP aplicado:** intención `autonomia_diaria` + clasificador emocional → los pasos dinámicos pueden sonar calmados, animados o de refuerzo dependiendo de lo que el niño exprese (“estoy nervioso”, “me siento orgulloso”).

#### 5. Escenarios personalizados
- **Cómo crearlos:** duplicar un pack existente via `POST /support-packs`, ajustar `triggers` y `response`, y activarlo con `POST /support-packs/{id}/activate`.
- **Recomendación:** mantén comentarios (`notes`) dentro del JSON para documentar ante el equipo docente qué objetivo curricular cubre cada plantilla.

Estos escenarios cumplen el objetivo analítico del proyecto (comprender lenguaje simple y asociarlo con pictogramas) mientras proveen rutas claras para la intervención pedagógica y terapéutica.

**Important Note on History Rewriting (`git lfs migrate`)**
 - **Advertencia:** Reescribir el historial (`git filter-repo`, `git lfs migrate`, BFG) cambia los commits existentes. Si lo aplicas, deberás forzar el push (`git push --force`) y avisar a colaboradores para que vuelvan a clonar.
 - **Alternativa:** Si no quieres reescribir historia, considera mover archivos grandes fuera del repo (storage externo) o usar Git LFS antes de subir.