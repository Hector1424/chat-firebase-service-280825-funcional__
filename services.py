from __future__ import annotations
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from uuid import uuid4
import secrets
from firebase_config import db
from config import COLL_PROJECTS, COLL_CHATS, SUBCOLL_MESSAGES
from config import COLL_FCM_TOKENS

from firebase_admin import messaging

from config import COLL_FCM_TOKENS

from firebase_admin import messaging


# Helpers
def now_utc():
    return datetime.now(timezone.utc)

def gen_uuid():
    return str(uuid4())

def gen_api_key(n: int = 40):
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return "".join(secrets.choice(alphabet) for _ in range(n))

def direct_pair_key(user_a: str, user_b: str):
    a, b = sorted([str(user_a), str(user_b)])
    return f"{a}:{b}"


# Projects CRUD
def create_project(name: str):
    pid = gen_uuid()
    api_key = gen_api_key(48)
    doc = {
        "uuid": pid,
        "name": name,
        "api_key": api_key,
        "created_at": now_utc(),
        "updated_at": now_utc(),
    }
    db.collection(COLL_PROJECTS).document(pid).set(doc)
    return doc

def list_projects():
    out = []
    for d in db.collection(COLL_PROJECTS).stream():
        out.append(d.to_dict())
    return out

def get_project(project_id: str):
    snap = db.collection(COLL_PROJECTS).document(project_id).get()
    return snap.to_dict() if snap.exists else None

def update_project(project_id: str, name: Optional[str] = None):
    updates = {}
    if name: updates["name"] = name
    if not updates: return get_project(project_id)
    updates["updated_at"] = now_utc()
    db.collection(COLL_PROJECTS).document(project_id).update(updates)
    return get_project(project_id)

def delete_project(project_id: str):
    db.collection(COLL_PROJECTS).document(project_id).delete()
    return True

def validate_project_auth(project_id: str, api_key: str):
    proj = get_project(project_id)
    return bool(proj and proj.get("api_key") == api_key)


# Chats CRUD
def create_direct_chat(project_id: str, user_a: str, user_b: str):
    pair = direct_pair_key(user_a, user_b)
    existing = db.collection(COLL_CHATS)\
        .where("project_id", "==", project_id)\
        .where("type", "==", "direct")\
        .where("pair_key", "==", pair)\
        .limit(1).stream()

    for doc in existing:
        item = doc.to_dict()
        item["id"] = doc.id
        item["existed"] = True
        return item

    payload = {
        "project_id": project_id,
        "type": "direct",
        "users": sorted([user_a, user_b]),
        "pair_key": pair,
        "created_at": now_utc(),
    }
    ref = db.collection(COLL_CHATS).add(payload)[1]
    payload["id"] = ref.id
    payload["existed"] = False
    return payload

def create_group_chat(project_id: str, users: List[str], title: Optional[str] = None):
    payload = {
        "project_id": project_id,
        "type": "group",
        "users": sorted(list(set(users))),
        "title": title,
        "created_at": now_utc(),
    }
    ref = db.collection(COLL_CHATS).add(payload)[1]
    payload["id"] = ref.id
    return payload

def list_chats(project_id: str):
    out = []
    qs = db.collection(COLL_CHATS).where("project_id", "==", project_id).stream()
    for d in qs:
        item = d.to_dict()
        item["id"] = d.id
        out.append(item)
    return out

def get_chat(chat_id: str):
    snap = db.collection(COLL_CHATS).document(chat_id).get()
    if not snap.exists: return None
    item = snap.to_dict()
    item["id"] = snap.id
    return item


# Messages
def add_message(chat_id: str, sender_id: str, text: str):
    msg = {
        "sender_id": sender_id,
        "text": text,
        "timestamp": now_utc(),
    }
    ref = db.collection(COLL_CHATS).document(chat_id).collection(SUBCOLL_MESSAGES).add(msg)[1]
    msg["id"] = ref.id

###################### logica notificaciones inicio

    # Get the project_id to pass to the notification function
    chat_doc = db.collection(COLL_CHATS).document(chat_id).get()
    project_id = chat_doc.to_dict().get("project_id", "N/A")

    # Call the new notification function after the message is saved
    send_push_notification(sender_id, chat_id, project_id)

###################### logica notificaciones fin


###################### logica notificaciones inicio

    # Get the project_id to pass to the notification function
    chat_doc = db.collection(COLL_CHATS).document(chat_id).get()
    project_id = chat_doc.to_dict().get("project_id", "N/A")

    # Call the new notification function after the message is saved
    send_push_notification(sender_id, chat_id, project_id)

###################### logica notificaciones fin

    return msg

def list_messages(chat_id: str):
    out = []
    q = db.collection(COLL_CHATS).document(chat_id).collection(SUBCOLL_MESSAGES).order_by("timestamp").stream()
    for d in q:
        item = d.to_dict()
        item["id"] = d.id
        out.append(item)
    return out

















# A new function to handle sending the notifications
def send_push_notification(sender_id: str, chat_id: str, project_id: str):
    try:
        chat_doc = db.collection(COLL_CHATS).document(chat_id).get()
        if not chat_doc.exists:
            print(f"Error: Chat with ID {chat_id} not found.")
            return

        chat_data = chat_doc.to_dict()
        chat_members = chat_data.get("users", [])

        fcm_tokens = []
        for user_id in chat_members:
            if user_id != sender_id:
                token_doc = db.collection(COLL_FCM_TOKENS).document(user_id).get()
                if token_doc.exists:
                    fcm_tokens.append(token_doc.to_dict()["token"])

        if not fcm_tokens:
            print("No tokens found to send notifications.")
            return

        message = messaging.MulticastMessage(
            tokens=fcm_tokens,
            notification=messaging.Notification(
                title=f"New message in {chat_data.get('title', 'your chat')}",
                body="You've received a new message.",
            ),
            data={"chat_id": chat_id, "project_id": project_id},
        )
        response = messaging.send_each_for_multicast(message)
        print(f"Notifications sent successfully: {response.success_count}")

    except Exception as e:
        print(f"An error occurred while sending notifications: {e}")






def save_fcm_token_to_db(user_uuid: str, token: str):
    """
    Guarda el token de notificaciones push de un usuario en la base de datos.
    """
    try:
        db.collection("fcm_tokens").document(user_uuid).set({
            "token": token,
            "timestamp": now_utc()
        })
        print(f"Token FCM guardado con éxito para el usuario {user_uuid}.")
        return True
    except Exception as e:
        print(f"Error al guardar el token FCM para el usuario {user_uuid}: {e}")
        return False

















# A new function to handle sending the notifications
def send_push_notification(sender_id: str, chat_id: str, project_id: str):
    try:
        chat_doc = db.collection(COLL_CHATS).document(chat_id).get()
        if not chat_doc.exists:
            print(f"Error: Chat with ID {chat_id} not found.")
            return

        chat_data = chat_doc.to_dict()
        chat_members = chat_data.get("users", [])

        fcm_tokens = []
        for user_id in chat_members:
            if user_id != sender_id:
                token_doc = db.collection(COLL_FCM_TOKENS).document(user_id).get()
                if token_doc.exists:
                    fcm_tokens.append(token_doc.to_dict()["token"])

        if not fcm_tokens:
            print("No tokens found to send notifications.")
            return

        message = messaging.MulticastMessage(
            tokens=fcm_tokens,
            notification=messaging.Notification(
                title=f"New message in {chat_data.get('title', 'your chat')}",
                body="You've received a new message.",
            ),
            data={"chat_id": chat_id, "project_id": project_id},
        )
        response = messaging.send_each_for_multicast(message)
        print(f"Notifications sent successfully: {response.success_count}")

    except Exception as e:
        print(f"An error occurred while sending notifications: {e}")






def save_fcm_token_to_db(user_uuid: str, token: str):
    """
    Guarda el token de notificaciones push de un usuario en la base de datos.
    """
    try:
        db.collection("fcm_tokens").document(user_uuid).set({
            "token": token,
            "timestamp": now_utc()
        })
        print(f"Token FCM guardado con éxito para el usuario {user_uuid}.")
        return True
    except Exception as e:
        print(f"Error al guardar el token FCM para el usuario {user_uuid}: {e}")
        return False