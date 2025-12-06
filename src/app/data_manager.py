import json
import os
from datetime import datetime
from collections import Counter
import copy

from src.app import support_pack_manager

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
    },
    "scenarios": [
        {
            "id": "rutina_salir_casa",
            "intents": ["rutina_escolar"],
            "triggers": [
                "antes de salir",
                "salir de casa",
                "antes de ir a la escuela"
            ],
            "response": "Antes de salir de casa repasemos estos pasos:",
            "steps": [
                "Guarda cuadernos y estuche dentro de la mochila.",
                "Coloca la botella de agua o lonchera en el bolsillo frontal.",
                "Respira profundo y elige el pictograma que muestra cómo te sientes."
            ],
            "follow_up": "Cuando termines me cuentas y celebramos tu rutina.",
            "pictogram_keyword": "mochila",
            "dynamic_steps": True,
            "tone": "calmo"
        },
        {
            "id": "terapia_practicar_sonido",
            "intents": ["terapia_habla"],
            "triggers": [
                "terapia del habla",
                "practicar sonido",
                "pronunciar",
                "sonido dificil"
            ],
            "response": "Practiquemos el sonido con calma:",
            "steps": [
                "Inhala por la nariz y cuenta tres.",
                "Mira el pictograma de la boca abierta para recordar la forma.",
                "Di el sonido tres veces y aplaude cuando lo logres."
            ],
            "follow_up": "Si te cansas, toma agua y seguimos cuando digas.",
            "pictogram_keyword": "hablar",
            "dynamic_steps": True,
            "tone": "calmo"
        },
        {
            "id": "juego_cooperativo_memoria",
            "intents": ["juego_cooperativo", "juego_pista"],
            "triggers": [
                "juego cooperativo",
                "juego de memoria",
                "jugar memoria"
            ],
            "response": "En el juego cooperativo recuerda:",
            "steps": [
                "Observa dos tarjetas y nombra lo que ves.",
                "Espera tu turno diciendo 'ahora tú'.",
                "Si te frustras, toca el pictograma de calma y respira."
            ],
            "follow_up": "Dime qué parejas encontraste para celebrarlo.",
            "pictogram_keyword": "jugar",
            "tone": "emocionado"
        },
        {
            "id": "autonomia_lavar_manos",
            "intents": ["autonomia_diaria"],
            "triggers": [
                "lavarme las manos",
                "higiene",
                "antes de comer"
            ],
            "response": "Lavemos las manos paso a paso:",
            "steps": [
                "Abre el grifo y moja las manos.",
                "Frota con jabón contando hasta diez.",
                "Enjuaga, seca y muestra el pictograma de manos limpias."
            ],
            "follow_up": "Cuando termines puedes elegir el pictograma de 'listo'.",
            "pictogram_keyword": "agua",
            "dynamic_steps": True,
            "tone": "calmo"
        },
        {
            "id": "concepto_color_cielo",
            "intents": ["factual_pregunta"],
            "triggers": [
                "color es el cielo",
                "color del cielo",
                "cielo de que color"
            ],
            "response": "Durante el día el cielo casi siempre es azul clarito con nubes blancas.",
            "follow_up": "Busca el pictograma de azul o de nube para mostrarlo.",
            "pictogram_keyword": "azul"
        }
    ]
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


def get_recent_interactions(username: str, limit: int = 20):
    if not os.path.exists(LOG_FILE):
        return []
    interactions = []
    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            try:
                log = json.loads(line)
            except json.JSONDecodeError:
                continue
            if log.get('username') == username:
                interactions.append(log)
    return interactions[-limit:]

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


def delete_assignment(assignment_id: str, author: str) -> bool:
    """Delete an assignment if it belongs to author; also remove its results."""
    assignments = get_assignments()
    remaining = [a for a in assignments if not (a.get('timestamp') == assignment_id and a.get('author') == author)]
    if len(remaining) == len(assignments):
        return False
    with open(ASSIGNMENTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(remaining, f, ensure_ascii=False, indent=4)

    # Remove related results
    results = get_assignment_results()
    filtered_results = [r for r in results if r.get('assignment_id') != assignment_id]
    with open(ASSIGNMENT_RESULTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(filtered_results, f, ensure_ascii=False, indent=4)
    return True


def get_assignment_results_for_author(author: str):
    """Return results for assignments created by the given author."""
    assignments = {a.get('timestamp'): a for a in get_assignments() if a.get('author') == author}
    results = get_assignment_results()
    return [r for r in results if r.get('assignment_id') in assignments]


def load_support_content():
    """Loads curated therapist/teacher support content."""
    support_data = copy.deepcopy(DEFAULT_SUPPORT_CONTENT)

    if os.path.exists(SUPPORT_CONTENT_FILE):
        try:
            with open(SUPPORT_CONTENT_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    for section, value in data.items():
                        if isinstance(value, dict):
                            support_data.setdefault(section, {}).update(value)
                        else:
                            support_data[section] = value
        except (json.JSONDecodeError, IOError):
            pass

    active_pack = support_pack_manager.get_active_content()
    if isinstance(active_pack, dict):
        for section, value in active_pack.items():
            if isinstance(value, dict):
                support_data.setdefault(section, {}).update(value)
            else:
                support_data[section] = value

    return support_data


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


def get_usage_logs_for_users(usernames, limit=50):
    """Return recent logs for a list of usernames (most recent last)."""
    if not os.path.exists(LOG_FILE):
        return []
    results = []
    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            try:
                log = json.loads(line)
            except json.JSONDecodeError:
                continue
            if log.get('username') in usernames:
                results.append(log)
    return results[-limit:]


def get_assignment_results_for_users(usernames):
    """Return assignment results filtered by usernames."""
    results = get_assignment_results()
    return [r for r in results if r.get('username') in usernames]

if __name__ == '__main__':
    # Example usage
    log_interaction("Hola", [{'word': 'Hola', 'pictogram': 'path/to/hola.png'}])
    save_note("test_user", "This is a test note.")
    print(f"Check the log file at: {LOG_FILE}")
    print(f"Check the notes file at: {NOTES_FILE}")
    print(get_notes())
