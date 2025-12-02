# ChatBot-IA - Asistente con Pictogramas

##  Descripción
Asistente conversacional para niños con dificultades de comunicación, integrando Natural Language Processing (NLP) y pictogramas. Este es un proyecto para el curso 1ASI0404 - Inteligencia Artificial 2025-20.

## Documentación Completa
Para obtener información detallada sobre la configuración del proyecto, la arquitectura, cómo ejecutar la aplicación y el progreso actual, por favor consulta la documentación principal en el siguiente enlace:

### **[Ver Documentación Completa](../docs/README.md)**

---

###  Objetivos Generales
- Desarrollar un modelo NLP para frases simples.
- Implementar un módulo de pictogramas (texto ↔ imagen).
- Crear una interfaz gráfica de usuario (GUI) accesible.
- Alinear el proyecto con los Objetivos de Desarrollo Sostenible (ODS) 4, 9 y 10.

###  Asignaciones y Sesiones Guiadas
- **Tipos de asignación:** Al crear tareas desde la interfaz web se puede elegir el campo `type` entre `assignment` y `guided_session`. Ambas se almacenan en `data/assignments.json`, lo que permite a docentes y terapeutas (Historias 6 y 9) reutilizar el mismo flujo para actividades libres o sesiones guiadas.
- **Creación solo para adultos:** Las vistas de docentes, padres y terapeutas solo muestran las actividades que ellos generaron y permiten gestionar el contenido sin ejecutarlo, acorde al foco de seguimiento en Historias 4, 6 y 8.
- **Ejecución solo por estudiantes:** El backend valida que únicamente roles `student` o `child` puedan enviar resultados (`POST /assignment-results`), garantizando que los progresos respondan a la práctica real del niño (Historias 1–3).
- **Experiencia del alumno:** Cuando un estudiante abre una tarea o sesión guiada se muestra la vista interactiva con validaciones y registro automático de respuestas, lo que contribuye a los objetivos de aprendizaje lúdico (Historia 3).

###  Flujo del Chatbot AAC
- **Contexto de asignaciones:** `src/app/chatbot_logic.py` ahora incorpora metadatos de juegos, sesiones guiadas y progreso histórico al armar cada prompt para el modelo T5. Esto mantiene alineada la conversación con los objetivos definidos por docentes y terapeutas (HU6, HU8, HU9).
- **Biblioteca de apoyo curado:** El archivo `data/support_content.json` centraliza saludos, mensajes motivacionales y plantillas de pistas para ser reutilizadas en guías estructuradas. Si el archivo no existe, `data_manager.load_support_content()` aplica una versión por defecto segura.
- **Respuestas guiadas para niños:** Cuando el rol es `child`/`student` y está dentro de un juego o sesión guiada, el bot prioriza salidas determinísticas (pistas, celebraciones y recordatorios de pictogramas) antes de recurrir al modelo generativo, cumpliendo con HU1–HU3.
- **Personalización por progreso:** El método `get_user_progress_summary()` agrega estadísticas desde `data/logs/usage_logs.json` para mencionar palabras más practicadas y la última interacción, reforzando los criterios de seguimiento y monitoreo (HU4, HU5, HU7).
- **Red semántica guiada:** La sección `related_vocab` dentro de `data/support_content.json` define asociaciones seguras (p. ej., `caballo` → “heno”, “herradura”). Si no existe una entrada curada, el bot toma las palabras clave del pictograma de ARASAAC para construir la pista. Así, cuando el estudiante ingresa una sola palabra, obtiene una frase completa con conexiones útiles en lugar de tokens sueltos.

###  Equipo
- **PO**: Leonardo Gamboa
- **Scrum Master**: Enzo Medina
- **Data Engineers**: Raul Gutierrez
- **Data Scientists**: Austin Flores y Jairo Huasaja
- **Data Analyst**: Diego Flores
- **Developers**: Sebastian Cuadrado
- **UI/UX**: Piero COntreras
- **QA**: Aaron Felices
