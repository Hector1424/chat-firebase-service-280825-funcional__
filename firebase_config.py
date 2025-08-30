# import firebase_admin
# from firebase_admin import credentials, firestore
# from config import FIREBASE_CREDENTIALS

# # Inicialización de Firebase
# cred = credentials.Certificate(FIREBASE_CREDENTIALS)
# firebase_admin.initialize_app(cred)

# db = firestore.client()



import firebase_admin
from firebase_admin import credentials, firestore
# Importa la constante que creaste en config.py
from config import FIREBASE_CREDENTIALS, FIREBASE_MESSAGING_SENDER_ID

# Agrega la importación del servicio de mensajería para notificaciones push
from firebase_admin import messaging

# Inicialización de Firebase
cred = credentials.Certificate(FIREBASE_CREDENTIALS)

# Pasa la variable FIREBASE_MESSAGING_SENDER_ID
firebase_admin.initialize_app(cred, {'messagingSenderId': FIREBASE_MESSAGING_SENDER_ID})

db = firestore.client()