import os
import time
import threading
import requests
import gradio gr

from run_agent import AIAgent as HermesAgent


# ============================================================
# 1. VARIABLES DE ENTORNO
# ============================================================
llm_api_key = (
    os.environ.get("GEMINI_API_KEY")
    or os.environ.get("GOOGLE_API_KEY")
)

telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN")
telegram_allowed_users = os.environ.get("TELEGRAM_ALLOWED_USERS", "")
notion_token = os.environ.get("NOTION_API_KEY")

# URL real asignada por SnapDeploy para el Auto-Ping
app_url = os.environ.get("APP_URL", "https://snapdeploy.app")

model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

TELEGRAM_API = f"https://telegram.org{telegram_token}"


# ============================================================
# 2. VALIDACIÓN
# ============================================================
if not llm_api_key:
    raise RuntimeError(
        "Falta GEMINI_API_KEY o GOOGLE_API_KEY. "
        "Configúrala antes de desplegar."
    )

if not telegram_token:
    raise RuntimeError(
        "Falta TELEGRAM_BOT_TOKEN. "
        "Créalo con @BotFather y configúralo en SnapDeploy."
    )

# IDs numéricos autorizados, separados por coma.
allowed_users = {
    user.strip()
    for user in telegram_allowed_users.split(",")
    if user.strip()
}


# ============================================================
# 3. INICIALIZAR HERMES
# ============================================================
agent = HermesAgent(
    model=model_name,
    api_key=llm_api_key,
    base_url="https://googleapis.com",
    enabled_toolsets=[
        "web_search",
        "telegram_messaging",
        "notion_integration",
    ],
    quiet_mode=True,
)


# ============================================================
# 4. FUNCIONES DE TELEGRAM
# ============================================================
def telegram_send(chat_id: int, text: str):
    """Envía un mensaje de texto a Telegram."""
    try:
        requests.post(
            f"{TELEGRAM_API}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": text[:4096],
                "parse_mode": "Markdown",
            },
            timeout=20,
        )
    except Exception as e:
        print(f"❌ [Telegram] No se pudo enviar mensaje: {e}")

        # Reintento sin Markdown por si el texto tiene caracteres especiales
        try:
            requests.post(
                f"{TELEGRAM_API}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": text[:4096],
                },
                timeout=20,
            )
        except Exception as e2:
            print(f"❌ [Telegram] Reintento fallido: {e2}")


def procesar_mensaje_telegram(chat_id: int, texto: str):
    """Procesa un mensaje entrante con Hermes y responde."""
    try:
        telegram_send(chat_id, "🧠 Procesando tu solicitud...")

        respuesta = agent.run_conversation(texto)

        if isinstance(respuesta, dict):
            respuesta = (
                respuesta.get("content")
                or respuesta.get("response")
                or str(respuesta)
            )

        if not respuesta:
            respuesta = "No recibí una respuesta válida del agente."

        telegram_send(chat_id, str(respuesta))

    except Exception as e:
        print(f"❌ [Telegram] Error procesando mensaje: {e}")
        telegram_send(
            chat_id,
            f"❌ Ocurrió un error al procesar tu solicitud:\n{e}",
        )


def telegram_polling():
    """Escucha nuevos mensajes usando long polling."""
    offset = None
    print("📩 [Telegram] Polling iniciado.")

    while True:
        try:
            params = {"timeout": 30}
            if offset:
                params["offset"] = offset

            response = requests.get(
                f"{TELEGRAM_API}/getUpdates",
                params=params,
                timeout=40,
            )
            data = response.json()

            if not data.get("ok"):
                print(f"⚠️ [Telegram] Respuesta inválida: {data}")
                time.sleep(3)
                continue

            for update in data.get("result", []):
                offset = update["update_id"] + 1

                message = update.get("message")
                if not message:
                    continue

                chat_id = message["chat"]["id"]
                user_id = str(message["from"]["id"])
                texto = message.get("text", "").strip()

                if not texto:
                    continue

                if allowed_users and user_id not in allowed_users:
                    print(
                        f"🚫 [Telegram] Usuario no autorizado: {user_id}"
                    )
                    telegram_send(
                        chat_id,
                        "⛔ No tienes permiso para usar este agente.",
                    )
                    continue

                print(f"📩 [Telegram] Mensaje de {user_id}: {texto}")

                # Procesar en un hilo para no bloquear el polling
                threading.Thread(
                    target=procesar_mensaje_telegram,
                    args=(chat_id, texto),
                    daemon=True,
                ).start()

        except Exception as e:
            print(f"❌ [Telegram] Error en polling: {e}")
            time.sleep(5)


# ============================================================
# 5. INTERFAZ WEB GRADIO
# ============================================================
def responder_chat_web(mensaje, historial):
    try:
        respuesta = agent.run_conversation(mensaje)

        if isinstance(respuesta, dict):
            return (
                respuesta.get("content")
                or respuesta.get("response")
                or str(respuesta)
            )

        return respuesta

    except Exception as e:
        return f"❌ Error al procesar el comando: {e}"


demo = gr.ChatInterface(
    fn=responder_chat_web,
    title="🧠 Centro de Control — Hermes Agent",
    description=(
        "Agente conectado a Gemini, búsqueda web, Telegram y Notion. "
        f"Modelo actual: {model_name}"
    ),
)


# ============================================================
# 6. AUTO-PING PARA SNAPDEPLOY
# ============================================================
def mantener_despierto():
    # Esperar a que el servidor web esté completamente arriba antes del primer ping
    time.sleep(30)
    print("🚀 Auto-Ping activado.")

    while True:
        try:
            response = requests.get(app_url, timeout=10)
            print(
                f"⏱️ [Auto-Ping] {app_url} — "
                f"Estado: {response.status_code}"
            )
        except Exception as e:
            print(f"❌ [Auto-Ping] Error de resolución: {e}")

        # Ejecutar ping cada 14 minutos (SnapDeploy suspende a los 15 minutos)
        time.sleep(14 * 60)


# ============================================================
# 7. ARRANQUE
# ============================================================
if __name__ == "__main__":
    # Iniciar hilos en segundo plano para procesos paralelos
    threading.Thread(target=mantener_despierto, daemon=True).start()
    threading.Thread(target=telegram_polling, daemon=True).start()

    print("🤖 Hermes Agent iniciado.")
    print(f"🧠 Modelo: {model_name}")
    print("📩 Telegram polling activo.")

    # Captura el puerto inyectado por SnapDeploy, usa 54321 por defecto
    port = int(os.environ.get("PORT", 54321)) 
    print(f"🌐 Interfaz web vinculada al puerto: {port}")

    # Inicialización compatible con colas HTTP estables en servidores cloud
    demo.queue().launch(
        server_name="0.0.0.0",
        server_port=port,
        prevent_thread_lock=False,
        share=False,
    )
