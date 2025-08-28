import firebase_admin
from firebase_admin import credentials, firestore
from config import FIREBASE_CREDENTIALS

# Inicialización de Firebase
cred = credentials.Certificate(FIREBASE_CREDENTIALS)
firebase_admin.initialize_app(cred)

db = firestore.client()
