import os

# Ruta al JSON de credenciales de Firebase
FIREBASE_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "serviceAccountKey.json")

# Nombres de colecciones en Firestore
COLL_PROJECTS = "projects"
COLL_CHATS = "chats"
SUBCOLL_MESSAGES = "messages"
