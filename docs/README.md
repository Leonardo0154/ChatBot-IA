# ChatBot-IA Project Documentation

## Project Overview
This project aims to develop a conversational assistant for children with communication difficulties, integrating Natural Language Processing (NLP) and pictograms. It is a project for the course 1ASI0404 - Inteligencia Artificial 2025-20.

## Setup

### Prerequisites
Before setting up the project, ensure you have the following installed:
*   `unzip`: For extracting compressed datasets.
*   `python3-venv`: For creating isolated Python environments.
*   `pip`: Python package installer.
*   `docker`: For running the containerized application.

If you are on a Debian/Ubuntu system, you can install these by running:
```bash
sudo apt update
sudo apt install -y unzip python3.12-venv python3-pip docker.io
```

### Project Installation
1.  **Clone the repository:**
    ```bash
    git clone <repository_url> # Replace with actual repository URL
    cd ChatBot-IA # Or your project root
    ```
2.  **Unzip Raw Data (if available):**
    **Note: The provided `.zip` files are currently empty.** If you have valid datasets, place them in `data/raw/` and unzip them:
    ```bash
    unzip 'data/raw/Aguirre.zip' -d 'data/raw/'
    unzip 'data/raw/BecaCesNo.zip' -d 'data/raw/'
    ```
3.  **Create and Activate Virtual Environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
4.  **Install Python Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
5.  **Download spaCy Models:**
    ```bash
    python -m spacy download es_core_news_sm
    ```

## Running the Application

### Using Docker (Recommended)
This is the easiest way to run the backend API.
1.  **Build the Docker image:**
    ```bash
    docker build -t chatbot-ia .
    ```
2.  **Run the Docker container:**
    ```bash
    docker run -p 8000:8000 chatbot-ia
    ```
    The API will be accessible at `http://127.0.0.1:8000`.

### Running Manually

1.  **Run the API (Backend):**
    *   Activate your virtual environment: `source venv/bin/activate`
    *   Navigate to the API directory: `cd src/api`
    *   Start the Uvicorn server: `uvicorn main:app --reload`
    The API will be accessible at `http://127.0.0.1:8000`.

2.  **Run the Chatbot (Frontend):**
    *   Open the `src/app/chatbot-frontend/index.html` file in your web browser.

## Testing
The project includes unit tests for the core logic. To run the tests:
1.  **Activate your virtual environment:**
    ```bash
    source venv/bin/activate
    ```
2.  **Run the unittest module from the project root:**
    ```bash
    python -m unittest discover tests
    ```

## Project Structure
```
.
├── ChatBot-IA/
│   └── (chatbot-specific files)
├── data/
│   ├── processed/
│   └── raw/
│       ├── Aguirre.zip (empty)
│       ├── arasaac_pictograms_es.json
│       └── BecaCesNo.zip (empty)
├── docs/
│   └── README.md (This file)
├── notebooks/
│   └── 01-model-selection-and-experimentation.ipynb
├── src/
│   ├── api/
│   │   └── main.py
│   ├── app/
│   │   ├── chatbot-frontend/
│   │   │   ├── index.html
│   │   │   ├── script.js
│   │   │   └── style.css
│   │   └── chatbot_logic.py
│   ├── model/
│   │   └── nlp_utils.py
│   └── scripts/
│       └── process_data.py
├── tests/
│   └── test_chatbot_logic.py
├── Dockerfile
├── requirements.txt
└── spacy_models.txt
```

## Milestones and Progress

*   **Milestone 1 (Dataset + Base Model):**
    *   `arasaac_pictograms_es.json` identified as pictogram source.
    *   `Aguirre.zip` and `BecaCesNo.zip` are empty. **Project is BLOCKED on obtaining valid text datasets.**
    *   Base NLP model selected (`spaCy`) and documented.
    *   Data processing script created.
    *   **Status:** Partially completed (BLOCKED).

*   **Milestone 2 (Chatbot Prototype):**
    *   FastAPI backend API created and functional.
    *   NLP model and pictogram logic integrated into the API.
    *   Rule-based chatbot logic implemented.
    *   **Status:** Completed.

*   **Milestone 3 (GUI Integrada):**
    *   Basic web-based frontend created (HTML, CSS, JS).
    *   Frontend is connected to the backend API.
    *   **Status:** Completed.

*   **Milestone 4 (Entrega Final):**
    *   Project documentation initiated and updated.
    *   Unit tests for core logic implemented.
    *   Containerization with Docker set up.
    *   **Status:** In Progress. The final "refinement" and "testing" steps require real data.

