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

###  Capacidades Multimodales y Gestión
- **Audio/STT respaldado por backend:** `/speech-to-text` permite subir audios (voz del niño) para registrarlos y transcribirlos con Whisper (o modo stub). Todas las cargas quedan en `data/audio/` junto con metadatos auditables.
- **Biblioteca de cues auditivos:** Docentes y terapeutas pueden subir pistas motivacionales desde `/audio-cues` y reproducirlas mediante el backend (útil cuando el navegador no soporta TTS local).
- **Support packs versionados:** Las plantillas de apoyo ya no son estáticas; `support_pack_manager` ofrece CRUD + activación (`/support-packs/...`) para packs personalizados por curso o sesión guiada.
- **Reportes descargables:** `/reports/generate|export` consolida métricas por estudiante, fecha y objetivo con exportes JSON/CSV que alimentan el informe TB2 y las reuniones con padres.
- **Alertas configurables:** `/notification-rules` y `/alerts` permiten definir reglas (p. ej., inactividad, metas de vocabulario) con registro de acciones y resultados en `data/notifications.json`.
- **Notas compartidas y permisos:** `/shared-notes` gestiona notas colaborativas con bitácora de lectura y control de acceso para coordinación entre docente, terapeuta y familia (HU10).
- **Privacidad y consentimiento:** `consent_manager` registra permisos (`/consents`), habilita exportación/borrado de datos (`/data/export`, `/data/{username}`) y genera auditorías en `data/logs/audit_logs.json`.
- **Clasificador de intenciones + emociones:** Dos modelos ligeros de spaCy etiquetan cada frase (rutina, terapia, juego, factual, consentimiento, etc.) y su tono emocional. Con esos labels el chatbot selecciona el pack correcto aunque el niño parafrasee y aplica respuestas empáticas.
- **Plantillas dinámicas con T5:** Cuando un escenario marca `dynamic_steps`, el modelo T5 rellena los “slots” de la plantilla (tres pasos, tono personalizado) a partir de la intención detectada y de lo expresado por el niño.
- **Resúmenes y auditoría automática:** Los últimos pictogramas practicados se extraen de `usage_logs.json` para personalizar las sesiones de terapia y las solicitudes de permiso se registran en `data/logs/audit_logs.json` cuando el niño pide autorización.

###  Escenarios educativos concretos
 - **Rutina escolar guiada:** Packs con saludos pre y post clase, recordatorios de materiales y escalas emocionales. El clasificador `rutina_escolar` permite que frases abiertas (“¿qué llevo hoy a lengua?”) disparen esta secuencia aún si no mencionan la palabra “rutina”.
 - **Sesiones de terapia del habla:** Plantillas por fonema o sonido conflictivo. El bot resume los sonidos practicados (extraídos de `usage_logs.json`) y, si la intención `terapia_habla` está presente, T5 regenera los tres pasos con el tono emocional detectado.
 - **Juego cooperativo/familiar:** Mensajes que refuerzan turnos, cooperación y regulación. Si el niño describe una carta (“animal grande con melena”), la extracción semántica usa `related_vocab` para inferir “león” y responder con pistas más precisas.
 - **Autonomía diaria:** Secuencias para higiene, alimentación y vestimenta. Cuando se detecta `autonomia_diaria`, los pasos dinámicos se reescriben en un tono calmo o entusiasta según la emoción detectada y se sugieren pictogramas alternativos si falta un objeto real.

Cada escenario se carga como un `support_pack` independiente para que docentes/terapeutas activen combinaciones según el plan individual. El chatbot recarga las plantillas en caliente, de modo que basta con actualizar el JSON del pack o usar los endpoints CRUD para iterar durante la intervención.

###  Equipo
- **PO**: Leonardo Gamboa
- **Scrum Master**: Enzo Medina
- **Data Engineers**: Raul Gutierrez
- **Data Scientists**: Austin Flores y Jairo Huasaja
- **Data Analyst**: Diego Flores
- **Developers**: Sebastian Cuadrado
- **UI/UX**: Piero COntreras
- **QA**: Aaron Felices
