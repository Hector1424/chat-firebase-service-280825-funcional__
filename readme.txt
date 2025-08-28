Contenido de cada archivo

main.py → Define la app FastAPI, endpoints HTTP para proyectos, chats y mensajes.

services.py → Funciones que hacen las operaciones en Firestore (create_project, create_chat, add_message, etc.).

config.py → Variables centralizadas (colecciones de Firestore, nombre del archivo de credenciales).

firebase_config.py → Inicializa Firebase con serviceAccountKey.json y expone db.

requirements.txt → Lista mínima de dependencias (fastapi, uvicorn, firebase-admin, pydantic).

serviceAccountKey.json → Credenciales de Firebase descargadas desde la consola de Google Cloud.