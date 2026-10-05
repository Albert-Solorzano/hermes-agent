import os
import time
import threading
import requests
import gradio as gr

# IMPORT CORREGIDO PARA EL SDK DE NOUS RESEARCH
try:
    from hermes import AIAgent as HermesAgent
except ImportError:
    from hermes_agent.agent import AIAgent as HermesAgent

# 1. LEER LAS VARIABLES DE ENTORNO OFICIALES
llm_api_key = os.environ.get("GEMINI_API_KEY")
telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN")
telegram_user_id = os.environ.get("TELEGRAM_USER_ID")
notion_token = os.environ.get("NOTION_API_KEY")
app_url = os.environ.get("APP_URL", "https://tu-app-temporal.dev")

# 2. INICIALIZAR EL BACKEND DE HERMES CON GEMINI
agent = HermesAgent(
    api_key=llm_api_key,
    platform="google",  # O proveedor correspondiente según la versión del SDK
    model="gemini-1.5-flash",
    enabled_toolsets=["web_search", "telegram_messaging", "notion_integration"],
    telegram_token=telegram_token,
    allowed_user_id=telegram_user_id,
    notion_token=notion_token
)

# Arrancar el loop del bot de Telegram en segundo plano
# Si tu versión usa start_loop(), el try-except asegura que no falle
try:
    agent.start_telegram_loop()
except AttributeError:
    threading.Thread(target=agent.run_conversation, daemon=True).start()

# 3. SISTEMA DE AUTO-PING PARA EVITAR QUE SNAPDEPLOY SE DUERMA
def mantener_despierto():
    time.sleep(30)
    print("🚀 Sistema de Auto-Ping activado...")
    while True:
        try:
            response = requests.get(app_url, timeout=10)
            print(f"⏱️ [Auto-Ping] Solicitud enviada a {app_url}. Estado: {response.status_code}")
        except Exception as e:
            print(f"❌ [Auto-Ping] Error de conexión: {e}")
        time.sleep(14 * 60)

# 4. INTERFAZ WEB DE GRADIO
def responder_chat_web(mensaje, historial):
    return agent.chat(mensaje)

demo = gr.ChatInterface(
    fn=responder_chat_web, 
    title="🧠 Centro de Control - Hermes Agent",
    description="Tu agente autónomo con acceso a Internet, Telegram y Notion está corriendo de forma segura en la nube."
)

if __name__ == "__main__":
    threading.Thread(target=mantener_despierto, daemon=True).start()
    demo.launch(server_name="0.0.0.0", server_port=7860)
