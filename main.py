import json
from fastapi import FastAPI, HTTPException, Depends, Header
from typing import Optional, List
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from services import (
    create_project, list_projects, get_project, update_project, delete_project,
    validate_project_auth, create_direct_chat, create_group_chat,
    list_chats, get_chat, add_message, list_messages
)
from google.cloud.firestore_v1._helpers import DatetimeWithNanoseconds



app = FastAPI(title="Chat API mínima")

# --- INICIO: Configuración de CORS ---
# Esto permite que tu frontend (cliente de prueba) se comunique con tu backend
# sin que el navegador lo bloquee.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todos los orígenes (para desarrollo)
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos los métodos (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],  # Permite todas las cabeceras
)
# --- FIN: Configuración de CORS ---



# Schemas
class ProjectIn(BaseModel):
    name: str

class ProjectUpdate(BaseModel):
    name: Optional[str] = None

class ChatDirectIn(BaseModel):
    users: List[str]

class ChatGroupIn(BaseModel):
    users: List[str]
    title: Optional[str] = None

class MessageIn(BaseModel):
    sender_id: str
    text: str

# Dependency para validar auth
def require_project_auth(
    x_project_id: str = Header(..., alias="X-Project-Id"),
    x_api_key: str = Header(..., alias="X-Api-Key"),
):
    if not validate_project_auth(x_project_id, x_api_key):
        raise HTTPException(status_code=401, detail="Proyecto inválido o API key incorrecta")
    return x_project_id

# ---- Projects ----
@app.post("/projects")
def http_create_project(data: ProjectIn):
    return create_project(data.name)

@app.get("/projects")
def http_list_projects():
    return list_projects()

@app.get("/projects/{pid}")
def http_get_project(pid: str):
    pr = get_project(pid)
    if not pr: raise HTTPException(404, "Proyecto no encontrado")
    return pr

@app.patch("/projects/{pid}")
def http_update_project(pid: str, data: ProjectUpdate):
    pr = update_project(pid, name=data.name)
    if not pr: raise HTTPException(404, "Proyecto no encontrado")
    return pr

@app.delete("/projects/{pid}")
def http_delete_project(pid: str):
    if not get_project(pid): raise HTTPException(404, "Proyecto no encontrado")
    delete_project(pid)
    return {"ok": True}

# ---- Chats ----
@app.get("/chats")
def http_list_chats(project_id: str = Depends(require_project_auth)):
    return list_chats(project_id)

@app.post("/chats/direct")
def http_create_direct_chat(data: ChatDirectIn, project_id: str = Depends(require_project_auth)):
    if len(data.users) != 2:
        raise HTTPException(400, "Chat directo requiere exactamente 2 usuarios")
    return create_direct_chat(project_id, data.users[0], data.users[1])

@app.post("/chats/group")
def http_create_group_chat(data: ChatGroupIn, project_id: str = Depends(require_project_auth)):
    if len(data.users) < 2:
        raise HTTPException(400, "Chat grupal requiere al menos 2 usuarios")
    return create_group_chat(project_id, data.users, data.title)

@app.get("/chats/{chat_id}")
def http_get_chat(chat_id: str, project_id: str = Depends(require_project_auth)):
    chat = get_chat(chat_id)
    if not chat or chat["project_id"] != project_id:
        raise HTTPException(404, "Chat no encontrado")
    return chat

# ---- Messages ----
@app.get("/chats/{chat_id}/messages")
def http_list_messages(chat_id: str, project_id: str = Depends(require_project_auth)):
    chat = get_chat(chat_id)
    if not chat or chat["project_id"] != project_id:
        raise HTTPException(404, "Chat no encontrado")
    return list_messages(chat_id)

@app.post("/chats/{chat_id}/messages")
def http_add_message(chat_id: str, data: MessageIn, project_id: str = Depends(require_project_auth)):
    chat = get_chat(chat_id)
    if not chat or chat["project_id"] != project_id:
        raise HTTPException(404, "Chat no encontrado")
    return add_message(chat_id, data.sender_id, data.text)


@app.get("/proyectos", response_class=HTMLResponse, tags=["frontend"])
def proyectos_page():
    proyectos = list_projects()
    for p in proyectos:
        if "created_at" in p and hasattr(p["created_at"], "isoformat"):
            p["created_at"] = p["created_at"].isoformat()
        if "updated_at" in p and hasattr(p["updated_at"], "isoformat"):
            p["updated_at"] = p["updated_at"].isoformat()

    proyectos_json = json.dumps(proyectos)

    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Gestión de Proyectos</title>
      <style>
        body {{
          font-family: Arial, sans-serif;
          margin: 0; padding: 2rem;
          background: #f4f6f8;
        }}
        h1 {{ text-align: center; }}
        #actions {{
          text-align: center;
          margin: 1rem 0;
        }}
        button {{
          background: #1976d2;
          border: none;
          color: white;
          padding: .6rem 1.2rem;
          border-radius: 6px;
          cursor: pointer;
          margin: 0 .2rem;
        }}
        button.danger {{
          background: #d32f2f;
        }}
        #search {{
          display:block;
          margin: 1rem auto;
          padding: 0.6rem 1rem;
          width: 80%;
          max-width: 500px;
          border:1px solid #ccc;
          border-radius: 8px;
        }}
        .grid {{
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
          gap: 1rem;
          margin-top: 2rem;
        }}
        .card {{
          background: #fff;
          padding: 1rem 1.2rem;
          border-radius: 12px;
          box-shadow: 0 2px 6px rgba(0,0,0,0.1);
          transition: transform .2s;
          position: relative;
        }}
        .card:hover {{ transform: translateY(-3px); }}
        .card h2 {{
          margin: 0 0 .5rem;
          font-size: 1.2rem;
          color: #333;
        }}
        .meta {{
          font-size: .85rem;
          color: #555;
          margin-top: .3rem;
        }}
        .apikey {{
          font-size: .75rem;
          color: #777;
          word-break: break-all;
        }}
        .card-actions {{
          margin-top: .8rem;
          text-align: right;
        }}
      </style>
    </head>
    <body>
      <h1>Gestión de Proyectos</h1>
      <div id="actions">
        <button onclick="crearProyecto()">+ Nuevo Proyecto</button>
      </div>
      <input type="text" id="search" placeholder="Buscar proyecto por nombre o UUID...">

      <div class="grid" id="cards"></div>

      <script>
        let proyectos = {proyectos_json};

        const container = document.getElementById("cards");
        const searchInput = document.getElementById("search");

        function render(data){{
          container.innerHTML = "";
          if(!data.length){{
            container.innerHTML = "<p>No hay proyectos.</p>";
            return;
          }}
          data.forEach(p => {{
            const card = document.createElement("div");
            card.className = "card";
            card.innerHTML = `
              <h2>${{p.name}}</h2>
              <div class="meta"><strong>UUID:</strong> ${{p.uuid}}</div>
              <div class="apikey"><strong>API Key:</strong> ${{p.api_key}}</div>
              <div class="meta"><strong>Creado:</strong> ${{p.created_at}}</div>
              <div class="meta"><strong>Actualizado:</strong> ${{p.updated_at}}</div>
              <div class="card-actions">
                <button class="danger" onclick="eliminarProyecto('${{p.uuid}}')">Eliminar</button>
              </div>
            `;

            
            container.appendChild(card);
          }});
        }}

        function filter(){{
          const term = searchInput.value.toLowerCase();
          const filtered = proyectos.filter(p =>
            p.name.toLowerCase().includes(term) || p.uuid.toLowerCase().includes(term)
          );
          render(filtered);
        }}
        searchInput.addEventListener("input", filter);

        async function crearProyecto(){{
          const name = prompt("Nombre del nuevo proyecto:");
          if(!name) return;
          const res = await fetch("/projects", {{
            method: "POST",
            headers: {{ "Content-Type": "application/json" }},
            body: JSON.stringify({{name}})
          }});
          if(res.ok){{
            const nuevo = await res.json();
            proyectos.unshift(nuevo);
            render(proyectos);
          }} else {{
            alert("Error al crear proyecto");
          }}
        }}

        async function eliminarProyecto(uuid){{
          if(!confirm("¿Seguro que deseas eliminar este proyecto?")) return;
          const res = await fetch(`/projects/${{uuid}}`, {{ method: "DELETE" }});
          if(res.ok){{
            proyectos = proyectos.filter(p => p.uuid !== uuid);
            render(proyectos);
          }} else {{
            alert("Error al eliminar");
          }}
        }}

        render(proyectos);
      </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)




























@app.get("/chatsConfig", response_class=HTMLResponse, tags=["frontend"])
def chats_config_page():
    proyectos = list_projects()
    chats = []

    # Normalizar proyectos (convertir fechas a string)
    for pr in proyectos:
        if "created_at" in pr and isinstance(pr["created_at"], DatetimeWithNanoseconds):
            pr["created_at"] = pr["created_at"].isoformat()
        if "updated_at" in pr and isinstance(pr["updated_at"], DatetimeWithNanoseconds):
            pr["updated_at"] = pr["updated_at"].isoformat()

    # Recorrer proyectos válidos
    for pr in proyectos:
        pid = pr.get("uuid")
        if not pid:
            continue
        for ch in list_chats(pid):
            ch["project_name"] = pr.get("name", "sin-nombre")
            ch["project_uuid"] = pid
            chats.append(ch)

    # Normalizar chats (convertir fechas a string)
    for c in chats:
        if "created_at" in c and isinstance(c["created_at"], DatetimeWithNanoseconds):
            c["created_at"] = c["created_at"].isoformat()
        if "updated_at" in c and isinstance(c["updated_at"], DatetimeWithNanoseconds):
            c["updated_at"] = c["updated_at"].isoformat()

    proyectos_json = json.dumps(proyectos)
    chats_json = json.dumps(chats)


    html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Gestión de Chats</title>
      <style>
        body {{
          font-family: Arial, sans-serif;
          margin: 0; padding: 2rem;
          background: #f4f6f8;
        }}
        h1 {{ text-align: center; }}
        #actions {{
          text-align: center;
          margin: 1rem 0;
        }}
        button {{
          background: #1976d2;
          border: none;
          color: white;
          padding: .6rem 1.2rem;
          border-radius: 6px;
          cursor: pointer;
          margin: 0 .2rem;
        }}
        button.danger {{
          background: #d32f2f;
        }}
        #search {{
          display:block;
          margin: 1rem auto;
          padding: 0.6rem 1rem;
          width: 80%;
          max-width: 500px;
          border:1px solid #ccc;
          border-radius: 8px;
        }}
        .grid {{
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
          gap: 1rem;
          margin-top: 2rem;
        }}
        .card {{
          background: #fff;
          padding: 1rem 1.2rem;
          border-radius: 12px;
          box-shadow: 0 2px 6px rgba(0,0,0,0.1);
        }}
        .card h2 {{
          margin: 0 0 .5rem;
          font-size: 1.2rem;
          color: #333;
        }}
        .meta {{
          font-size: .85rem;
          color: #555;
          margin-top: .3rem;
        }}
        .card-actions {{
          margin-top: .8rem;
          text-align: right;
        }}
      </style>
    </head>
    <body>
      <h1>Gestión de Chats</h1>
      <div id="actions">
        <button onclick="crearChat()">+ Nuevo Chat</button>
      </div>
      <input type="text" id="search" placeholder="Buscar chat por proyecto o usuarios...">

      <div class="grid" id="cards"></div>

      <script>
        let proyectos = {proyectos_json};
        let chats = {chats_json};

        const container = document.getElementById("cards");
        const searchInput = document.getElementById("search");

        function render(data){{
          container.innerHTML = "";
          if(!data.length){{
            container.innerHTML = "<p>No hay chats.</p>";
            return;
          }}
          data.forEach(c => {{
            const card = document.createElement("div");
            card.className = "card";
            card.innerHTML = `
              <h2>${{c.type.toUpperCase()}} Chat</h2>
              <div class="meta"><strong>Proyecto:</strong> ${{c.project_name}} (${{c.project_uuid}})</div>
              <div class="meta"><strong>Chat ID:</strong> ${{c.id}}</div>
              <div class="meta"><strong>Usuarios:</strong> ${{(c.users || []).join(", ")}}</div>
              <div class="meta"><strong>Creado:</strong> ${{c.created_at || ""}}</div>
              <div class="card-actions">
                <button class="danger" onclick="eliminarChat('${{c.id}}','${{c.project_uuid}}')">Eliminar</button>
              </div>
            `;



            container.appendChild(card);
          }});
        }}

        function filter(){{
          const term = searchInput.value.toLowerCase();
          const filtered = chats.filter(c =>
            c.project_name.toLowerCase().includes(term) ||
            (c.users || []).some(u => u.toLowerCase().includes(term))
          );
          render(filtered);
        }}
        searchInput.addEventListener("input", filter);

        async function crearChat(){{
          const pid = prompt("UUID del proyecto:");
          if(!pid) return;
          const type = prompt("Tipo de chat (direct/group):");
          if(!type) return;
          const users = prompt("Usuarios (separados por coma):");
          if(!users) return;
          let url = type === "direct" ? "/chats/direct" : "/chats/group";
          const res = await fetch(url, {{
            method: "POST",
            headers: {{
              "Content-Type": "application/json",
              "X-Project-Id": pid,
              "X-Api-Key": proyectos.find(p => p.uuid===pid)?.api_key || ""
            }},
            body: JSON.stringify({{users: users.split(",").map(u=>u.trim()), title:"Nuevo Chat"}})
          }});
          if(res.ok){{
            const nuevo = await res.json();
            nuevo.project_uuid = pid;
            nuevo.project_name = proyectos.find(p=>p.uuid===pid)?.name || "";
            chats.unshift(nuevo);
            render(chats);
          }} else {{
            alert("Error al crear chat");
          }}
        }}

        async function eliminarChat(id, pid){{
          if(!confirm("¿Seguro que deseas eliminar este chat?")) return;
          const res = await fetch(`/chats/${{id}}`, {{
            method: "DELETE",
            headers: {{
              "X-Project-Id": pid,
              "X-Api-Key": proyectos.find(p => p.uuid===pid)?.api_key || ""
            }}
          }});
          if(res.ok){{
            chats = chats.filter(c => c.id !== id);
            render(chats);
          }} else {{
            alert("Error al eliminar");
          }}
        }}

        render(chats);
      </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)



















@app.get("/mensajes", response_class=HTMLResponse, tags=["frontend"])
def mensajes_page():
    # Reunir proyectos y chats
    proyectos = list_projects()
    chats = []
    for pr in proyectos:
        # Normalizar fechas de proyectos
        if "created_at" in pr and isinstance(pr["created_at"], DatetimeWithNanoseconds):
            pr["created_at"] = pr["created_at"].isoformat()
        if "updated_at" in pr and isinstance(pr["updated_at"], DatetimeWithNanoseconds):
            pr["updated_at"] = pr["updated_at"].isoformat()

    for pr in proyectos:
        pid = pr.get("uuid")
        if not pid:
            continue
        for ch in list_chats(pid):
            ch["project_name"] = pr.get("name", "sin-nombre")
            ch["project_uuid"] = pid
            # Normalizar fechas de chats
            if "created_at" in ch and isinstance(ch["created_at"], DatetimeWithNanoseconds):
                ch["created_at"] = ch["created_at"].isoformat()
            chats.append(ch)

    import json
    proyectos_json = json.dumps(proyectos)
    chats_json = json.dumps(chats)

    # IMPORTANTE: no usar f-string para que las llaves {} de CSS/JS no rompan el render
    html = """
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Mensajes de Chats</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      margin: 0; padding: 2rem;
      background: #f4f6f8;
    }
    h1 { text-align: center; }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 1rem;
      margin-top: 2rem;
    }
    .card {
      background: #fff;
      padding: 1rem;
      border-radius: 10px;
      box-shadow: 0 2px 6px rgba(0,0,0,0.1);
      cursor: pointer;
    }
    .card:hover { background: #f0f8ff; }
    #messages-section {
      margin-top: 2rem;
      padding: 1rem;
      background: #fff;
      border-radius: 10px;
      box-shadow: 0 2px 6px rgba(0,0,0,0.1);
    }
    .message {
      border-bottom: 1px solid #eee;
      padding: .5rem 0;
    }
    .message strong { color: #1976d2; }
    form {
      margin-top: 1rem;
      display: flex;
      gap: .5rem;
      flex-wrap: wrap;
    }
    select, input {
      padding: .5rem;
      border: 1px solid #ccc;
      border-radius: 5px;
    }
    button {
      padding: .5rem 1rem;
      border: none;
      border-radius: 5px;
      background: #1976d2;
      color: white;
      cursor: pointer;
    }
  </style>
</head>
<body>
  <h1>Gestión de Mensajes</h1>
  <h2>Chats disponibles</h2>
  <div class="grid" id="chats"></div>

  <section id="messages-section" style="display:none;">
    <h2 id="chat-title">Mensajes del chat</h2>
    <div id="messages"></div>

    <form id="new-message-form">
      <select id="sender"></select>
      <select id="receiver"></select>
      <input type="text" id="text" placeholder="Escribe tu mensaje..." required>
      <button type="submit">Enviar</button>
    </form>
  </section>

  <script>
    let proyectos = """ + proyectos_json + """;
    let chats = """ + chats_json + """;

    const chatsContainer = document.getElementById("chats");
    const messagesSection = document.getElementById("messages-section");
    const messagesDiv = document.getElementById("messages");
    const chatTitle = document.getElementById("chat-title");
    const form = document.getElementById("new-message-form");
    const senderSel = document.getElementById("sender");
    const receiverSel = document.getElementById("receiver");
    const textInput = document.getElementById("text");

    let currentChat = null;
    let currentProject = null;

    function renderChats() {
      chatsContainer.innerHTML = "";
      chats.forEach(c => {
        const card = document.createElement("div");
        card.className = "card";
        card.innerHTML = `
          <h3>${c.type.toUpperCase()} Chat</h3>
          <div><strong>ID:</strong> ${c.id}</div>
          <div><strong>Proyecto:</strong> ${c.project_name} (${c.project_uuid})</div>
          <div><strong>Usuarios:</strong> ${(c.users || []).join(", ")}</div>
        `;
        card.onclick = () => openChat(c);
        chatsContainer.appendChild(card);
      });
    }

    async function openChat(chat) {
      currentChat = chat;
      currentProject = (proyectos || []).find(p => p.uuid === chat.project_uuid) || null;
      chatTitle.textContent = `Mensajes del chat (${chat.id})`;
      messagesSection.style.display = "block";

      // llenar selects con usuarios
      senderSel.innerHTML = "";
      receiverSel.innerHTML = "";
      (chat.users || []).forEach(u => {
        senderSel.innerHTML += `<option value="${u}">${u}</option>`;
        receiverSel.innerHTML += `<option value="${u}">${u}</option>`;
      });

      await loadMessages(chat.id);
    }

    async function loadMessages(chatId) {
      const headers = {};
      if (currentProject) {
        headers["X-Project-Id"] = currentChat.project_uuid;
        headers["X-Api-Key"] = currentProject.api_key || "";
      }
      const res = await fetch(`/chats/${chatId}/messages`, { headers });
      if (res.ok) {
        const msgs = await res.json();
        renderMessages(msgs);
      } else {
        messagesDiv.innerHTML = "<p>Error al cargar mensajes</p>";
      }
    }

    function renderMessages(msgs) {
      messagesDiv.innerHTML = "";
      if (!msgs.length) {
        messagesDiv.innerHTML = "<p>No hay mensajes aún</p>";
        return;
      }
      msgs.forEach(m => {
        const div = document.createElement("div");
        div.className = "message";
        div.innerHTML = `<strong>${m.sender_id}</strong> → <em>${m.text}</em> <span style="font-size:.8rem;color:#555">[${m.timestamp}]</span>`;
        messagesDiv.appendChild(div);
      });
    }

    form.onsubmit = async (e) => {
      e.preventDefault();
      const sender = senderSel.value;
      const text = textInput.value;
      if (!sender || !text) return;

      const headers = {
        "Content-Type": "application/json"
      };
      if (currentProject) {
        headers["X-Project-Id"] = currentChat.project_uuid;
        headers["X-Api-Key"] = currentProject.api_key || "";
      }

      const res = await fetch(`/chats/${currentChat.id}/messages`, {
        method: "POST",
        headers,
        body: JSON.stringify({ sender_id: sender, text })
      });
      if (res.ok) {
        textInput.value = "";
        await loadMessages(currentChat.id);
      } else {
        alert("Error al enviar mensaje");
      }
    };

    renderChats();
  </script>
</body>
</html>
"""
    return HTMLResponse(content=html)