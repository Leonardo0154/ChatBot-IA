**Project Setup Guide: ChatBot-IA**

Este documento explica cómo configurar el proyecto `ChatBot-IA`, instalar dependencias y ejecutar la aplicación.

**Prerequisites**
- **Git:** Para clonar el repositorio.
- **Python:** Versión 3.10+ recomendada.
- **Git LFS (Large File Storage):** Para manejar archivos grandes.
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

**Step 6: Download spaCy NLP Model**
- **Comando:** `python -m spacy download es_core_news_sm`

**Step 7: Run the FastAPI Server**
- **Iniciar backend:** `uvicorn src.api.main:app --host 127.0.0.1 --port 8000`
- **URL de servicio:** `http://127.0.0.1:8000`

**Step 8: Access the Frontend**
- **Abrir en navegador:** `http://127.0.0.1:8000/static/index.html`

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

**Important Note on History Rewriting (`git lfs migrate`)**
 - **Advertencia:** Reescribir el historial (`git filter-repo`, `git lfs migrate`, BFG) cambia los commits existentes. Si lo aplicas, deberás forzar el push (`git push --force`) y avisar a colaboradores para que vuelvan a clonar.
 - **Alternativa:** Si no quieres reescribir historia, considera mover archivos grandes fuera del repo (storage externo) o usar Git LFS antes de subir.