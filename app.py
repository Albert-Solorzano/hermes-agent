import os
import time
import threading
import requests
import gradio as gr
from hermes_agent import HermesAgent

# 1. LEER LAS VARIABLES DE ENTORNO OFICIALES
llm_api_key = os.environ.get("GEMINI_API_KEY")
telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN")
telegram_user_id = os.environ.get("TELEGRAM_USER_ID")
notion_token = os.environ.get("NOTION_API_KEY")
app_url = os.environ.get("APP_URL", "https://tu-app-temporal.dev")

# 2. INICIALIZAR EL BACKEND DE HERMES CON GEMINI
# Configurado con búsqueda web, mensajería de Telegram e integración de Notion
agent = HermesAgent(
    api_key=llm_api_key,
    provider="google",
    model="gemini-1.5-flash",  # El modelo más rápido e inteligente para agentes
    tools=["web_search", "telegram_messaging", "notion_integration"],
    telegram_token=telegram_token,
    allowed_user_id=telegram_user_id,
    notion_token=notion_token
)

# Arrancar el bot de Telegram en segundo plano para que escuche mensajes 24/7
agent.start_telegram_loop()

# 3. SISTEMA DE AUTO-PING PARA EVITAR QUE SNAPDEPLOY SE DUERMA
def mantener_despierto():
    time.sleep(30)  # Esperar a que Gradio encienda por completo
    print("🚀 Sistema de Auto-Ping activado...")
    while True:
        try:
            response = requests.get(app_url, timeout=10)
            print(f"⏱️ [Auto-Ping] Solicitud enviada a {app_url}. Estado: {response.status_code}")
        except Exception as e:
            print(f"❌ [Auto-Ping] Error de conexión: {e}")
        time.sleep(14 * 60)  # Se ejecuta estrictamente cada 14 minutos

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
