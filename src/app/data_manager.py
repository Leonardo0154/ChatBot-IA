import json
import os
from datetime import datetime
from collections import Counter
import copy

LOG_FILE = 'data/logs/usage_logs.json'
NOTES_FILE = 'data/notes.json'
ASSIGNMENTS_FILE = 'data/assignments.json'
ASSIGNMENT_RESULTS_FILE = 'data/assignment_results.json'
SUPPORT_CONTENT_FILE = 'data/support_content.json'

DEFAULT_SUPPORT_CONTENT = {
    "general": {
        "prompt_prefix": "Eres un terapeuta del habla que conversa con un niño utilizando pictogramas.",
        "fallback": "Estoy aquí para ayudarte a practicar con tus pictogramas.",
        "greetings": [
            "¡Hola! ¿Listo para practicar tus palabras favoritas?",
            "¡Qué bueno verte! Vamos a comunicarnos con pictogramas."
        ],
        "greeting_triggers": ["hola", "buenos días", "buenas tardes"],
        "encouragement": [
            "Excelente esfuerzo, sigamos practicando.",
            "¡Muy bien! Cada pictograma te hace más fuerte."
        ],
        "related_templates": [
            "Cuando practicas {word}, también podemos hablar de {associations}.",
            "Piensa en {word} junto a {associations} para ampliar tus pictogramas."
        ]
    },
    "assignment": {
        "intro_templates": [
            "Estamos trabajando en: {task}.",
            "Hoy practicamos las palabras: {words}."
        ],
        "hint_templates": [
            "Observa el pictograma de {word} y descríbelo con calma.",
            "Piensa en cuándo usas la palabra {word} en tu día." 
        ]
    },
    "guided_session": {
        "success": [
            "¡Genial! Ahora veremos la siguiente palabra.",
            "Excelente pronunciación, continúa con la próxima tarjeta." 
        ],
        "hint": "La palabra comienza con {clue}.",
        "intro": "Esta sesión guiada se enfoca en {word}."
    },
    "related_vocab": {
        "caballo": ["heno", "galopar", "herradura", "establo"],
        "elefante": ["trompa", "manada", "agua"],
        "rinoceronte": ["cuerno", "savana", "pesado"],
        "sapo": ["charco", "verde", "croar"],
        "ardilla": ["arbol", "nuez", "cola"],
        "perro": ["correa", "ladrido", "pelota"],
        "gato": ["maullar", "bigotes", "suave"],
        "pajaro": ["alas", "volar", "nido"],
        "pez": ["agua", "nadar", "pecera"],
        "oso": ["invierno", "abrazo", "grande"],
        "leon": ["melena", "selva", "rugido"],
        "manzana": ["roja", "crujiente", "merienda", "jugo"],
        "banana": ["amarilla", "dulce", "pelar"],
        "pan": ["tostada", "mantequilla", "horno"],
        "leche": ["vaso", "desayuno", "calcio"],
        "agua": ["vaso", "sed", "fresca"],
        "galleta": ["dulce", "caja", "merienda"],
        "arroz": ["plato", "blanco", "cena"],
        "sopa": ["caliente", "cuchara", "tazon"],
        "pizza": ["queso", "rebanada", "horno"],
        "audifonos": ["musica", "oidos", "escuchar"],
        "telefono": ["llamada", "mensaje", "pantalla"],
        "tablet": ["tocar", "aplicacion", "juego"],
        "anillo": ["mano", "brilla", "regalo"],
        "libro": ["leer", "paginas", "historia"],
        "cuaderno": ["notas", "tareas", "lineas"],
        "lapiz": ["escribir", "borrar", "afilado"],
        "mochila": ["escuela", "cargar", "bolsillo"],
        "pelota": ["rebotar", "juego", "cancha"],
        "parque": ["columpio", "resbaladilla", "amigos"],
        "casa": ["familia", "sala", "hogar"],
        "escuela": ["maestra", "clase", "recreo"],
        "hospital": ["doctor", "ambulancia", "cuidar"],
        "ambulancia": ["sirena", "emergencia", "hospital"],
        "autobus": ["ruta", "asientos", "chofer"],
        "auto": ["ruedas", "cinturon", "viaje"],
        "bicicleta": ["pedalear", "casco", "parque"],
        "avion": ["alas", "nubes", "viajar"],
        "tren": ["viaje", "vagon", "anden"],
        "semaforo": ["luz", "cruzar", "seguridad"],
        "pictograma": ["secuencia", "tablero", "expresar"],
        "mama": ["abrazo", "cariño", "casa"],
        "papa": ["fuerte", "guiar", "jugar"],
        "hermano": ["compartir", "jugar", "familia"],
        "hermana": ["risas", "apoyo", "familia"],
        "abuelo": ["historias", "paciencia", "cafe"],
        "abuela": ["cocina", "abrazo", "consejo"],
        "amigo": ["juego", "confianza", "risas"],
        "feliz": ["sonrisa", "abrazo", "cancion"],
        "triste": ["llorar", "consuelo", "respirar"],
        "enojado": ["respirar", "contar", "calma"],
        "calmado": ["respirar", "susurro", "descanso"],
        "miedo": ["apoyo", "mano", "luz"],
        "cansado": ["descanso", "dormir", "silencio"],
        "dormir": ["sabanas", "sueños", "noche"],
        "comer": ["tenedor", "plato", "familia"],
        "cepillar": ["dientes", "pasta", "baño"],
        "banar": ["agua", "jabon", "toalla"],
        "jugar": ["turnos", "reglas", "risas"],
        "correr": ["rapido", "aire", "ejercicio"],
        "saltar": ["trampolin", "piernas", "energia"],
        "cantar": ["melodia", "voz", "ritmo"],
        "bailar": ["musica", "pasos", "ritmo"],
        "colores": ["rojo", "azul", "amarillo"],
        "rojo": ["fuego", "corazon", "stop"],
        "azul": ["cielo", "agua", "calma"],
        "verde": ["hojas", "esperanza", "semaforo"],
        "amarillo": ["sol", "sonrisa", "luz"],
        "numero": ["contar", "sumar", "juego"],
        "uno": ["primero", "dedo", "inicio"],
        "dos": ["pareja", "ojos", "manos"],
        "tres": ["pasos", "amigos", "trio"],
        "rabano": ["huerto", "ensalada", "crujiente"],
        "extraterrestre": ["planetas", "nave", "amistad"]
    }
}

def log_interaction(username, sentence, processed_sentence):
    """Logs the user's sentence and the processed pictograms to a JSON file."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'username': username,
        'sentence': sentence,
        'processed_sentence': processed_sentence
    }
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
    except IOError as e:
        print(f"Error writing to log file: {e}")

def get_notes():
    """Retrieves all notes from the notes file."""
    if not os.path.exists(NOTES_FILE):
        return []
    with open(NOTES_FILE, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_note(author, text):
    """Saves a new note to the notes file."""
    os.makedirs(os.path.dirname(NOTES_FILE), exist_ok=True)
    notes = get_notes()
    new_note = {
        'timestamp': datetime.now().isoformat(),
        'author': author,
        'text': text
    }
    notes.append(new_note)
    with open(NOTES_FILE, 'w', encoding='utf-8') as f:
        json.dump(notes, f, ensure_ascii=False, indent=4)

def get_assignments():
    """Retrieves all assignments from the assignments file."""
    if not os.path.exists(ASSIGNMENTS_FILE):
        return []
    with open(ASSIGNMENTS_FILE, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_assignment(author, assignment_data):
    """Saves a new assignment to the assignments file."""
    os.makedirs(os.path.dirname(ASSIGNMENTS_FILE), exist_ok=True)
    assignments = get_assignments()
    new_assignment = {
        'timestamp': datetime.now().isoformat(),
        'author': author,
        **assignment_data
    }
    assignments.append(new_assignment)
    with open(ASSIGNMENTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(assignments, f, ensure_ascii=False, indent=4)

def get_assignment_results():
    """Retrieves all assignment results from the results file."""
    if not os.path.exists(ASSIGNMENT_RESULTS_FILE):
        return []
    with open(ASSIGNMENT_RESULTS_FILE, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_assignment_result(username, result_data):
    """Saves a new assignment result to the results file."""
    os.makedirs(os.path.dirname(ASSIGNMENT_RESULTS_FILE), exist_ok=True)
    results = get_assignment_results()
    new_result = {
        'timestamp': datetime.now().isoformat(),
        'username': username,
        **result_data
    }
    results.append(new_result)
    with open(ASSIGNMENT_RESULTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)


def load_support_content():
    """Loads curated therapist/teacher support content."""
    if not os.path.exists(SUPPORT_CONTENT_FILE):
        return DEFAULT_SUPPORT_CONTENT

    try:
        with open(SUPPORT_CONTENT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict):
                merged = copy.deepcopy(DEFAULT_SUPPORT_CONTENT)
                for section, value in data.items():
                    if isinstance(value, dict):
                        merged.setdefault(section, {}).update(value)
                    else:
                        merged[section] = value
                return merged
    except (json.JSONDecodeError, IOError):
        pass
    return DEFAULT_SUPPORT_CONTENT


def get_user_progress_summary(username):
    """Aggregates simple progress stats for a user to personalize responses."""
    if not os.path.exists(LOG_FILE):
        return {
            'total_interactions': 0,
            'most_common_words': [],
            'last_interaction': None
        }

    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        logs = [json.loads(line) for line in f if line.strip()]

    user_logs = [log for log in logs if log.get('username') == username]
    if not user_logs:
        return {
            'total_interactions': 0,
            'most_common_words': [],
            'last_interaction': None
        }

    all_words = [
        item.get('word')
        for log in user_logs
        for item in log.get('processed_sentence', [])
        if item.get('word')
    ]
    word_counts = Counter(all_words)
    most_common = word_counts.most_common(3)
    last_interaction = max(log.get('timestamp') for log in user_logs)

    return {
        'total_interactions': len(user_logs),
        'most_common_words': most_common,
        'last_interaction': last_interaction
    }

if __name__ == '__main__':
    # Example usage
    log_interaction("Hola", [{'word': 'Hola', 'pictogram': 'path/to/hola.png'}])
    save_note("test_user", "This is a test note.")
    print(f"Check the log file at: {LOG_FILE}")
    print(f"Check the notes file at: {NOTES_FILE}")
    print(get_notes())
