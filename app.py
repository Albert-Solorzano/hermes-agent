import os
import time
import threading
import requests
import gradio as gr

# Import oficial de Nous Research
from run_agent import AIAgent as HermesAgent


# ============================================================
# 1. VARIABLES DE ENTORNO
# ============================================================
llm_api_key = (
    os.environ.get("GEMINI_API_KEY")
    or os.environ.get("GOOGLE_API_KEY")
)

telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN")
telegram_user_id = os.environ.get("TELEGRAM_USER_ID")
notion_token = os.environ.get("NOTION_API_KEY")

app_url = os.environ.get("APP_URL", "https://tu-app-temporal.dev")

# Modelo configurable desde variables de entorno.
# gemini-2.5-flash se retira el 20/oct/2026:
# cámbialo por un modelo vigente cuando lo verifiques con ListModels.
model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")


# ============================================================
# 2. VALIDACIÓN BÁSICA
# ============================================================
if not llm_api_key:
    raise RuntimeError(
        "Falta GEMINI_API_KEY o GOOGLE_API_KEY. "
        "Configúrala como variable de entorno antes de desplegar."
    )


# ============================================================
# 3. INICIALIZACIÓN DE HERMES
# ============================================================
# Hermes espera un endpoint compatible con OpenAI cuando se define base_url.
# Gemini expone compatibilidad OpenAI en:
# https://generativelanguage.googleapis.com/v1beta/openai/
agent = HermesAgent(
    model=model_name,
    api_key=llm_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    enabled_toolsets=[
        "web_search",
        "telegram_messaging",
        "notion_integration",
    ],
    quiet_mode=True,
)


# ============================================================
# 4. INTERFAZ WEB GRADIO
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
# 5. AUTO-PING PARA SNAPDEPLOY
# ============================================================
def mantener_despierto():
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
            print(f"❌ [Auto-Ping] Error: {e}")

        # Cada 14 minutos
        time.sleep(14 * 60)


# ============================================================
# 6. ARRANQUE
# ============================================================
if __name__ == "__main__":
    threading.Thread(target=mantener_despierto, daemon=True).start()

    print("🤖 Hermes Agent iniciado.")
    print(f"🧠 Modelo: {model_name}")
    print("🌐 Interfaz web disponible en el puerto 7860.")

    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
    )
