import os
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Ruta al JSON de credenciales de Firebase
# La línea original que busca el archivo JSON ya no es necesaria.
# FIREBASE_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "serviceAccountKey.json")

# Construir el diccionario de credenciales de Firebase desde variables de entorno
FIREBASE_CREDENTIALS = {
    "type": os.getenv("FIREBASE_TYPE"),
    "project_id": os.getenv("FIREBASE_PROJECT_ID"),
    "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
    # Reemplaza los saltos de línea escapados ('\\n') por saltos de línea reales ('\n')
    "private_key": os.getenv("FIREBASE_PRIVATE_KEY", "").replace('\\n', '\n'),
    "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
    "client_id": os.getenv("FIREBASE_CLIENT_ID"),
    "auth_uri": os.getenv("FIREBASE_AUTH_URI"),
    "token_uri": os.getenv("FIREBASE_TOKEN_URI"),
    "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_X509_CERT_URL"),
    "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_X509_CERT_URL"),
}

# Nombres de colecciones en Firestore
COLL_PROJECTS = "projects"
COLL_CHATS = "chats"
SUBCOLL_MESSAGES = "messages"


# Nueva colección para los tokens de notificaciones
COLL_FCM_TOKENS = "fcm_tokens"


# Agrega esta línea para cargar el messagingSenderId desde el .env
FIREBASE_MESSAGING_SENDER_ID = os.getenv("FIREBASE_MESSAGING_SENDER_ID")