import os
import time
import threading
import requests
import gradio as gr

# IMPORT OFICIAL Y CORRECTO DE NOUS RESEARCH
from run_agent import AIAgent as HermesAgent

# 1. LEER LAS VARIABLES DE ENTORNO OFICIALES
# Hermes detecta el proveedor gemini automáticamente con esta URL base
llm_api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN")
telegram_user_id = os.environ.get("TELEGRAM_USER_ID")
notion_token = os.environ.get("NOTION_API_KEY")
app_url = os.environ.get("APP_URL", "https://tu-app-temporal.dev")

# 2. INICIALIZAR EL BACKEND DE HERMES SEGÚN LA DOCUMENTACIÓN DEL SDK
# El constructor acepta 'api_key' y el modelo en formato estándar
# Usa el formato nativo de Gemini (no OpenRouter-style) y la URL base oficial
agent = HermesAgent(
    model="gemini-2.5-flash",  # Formato nativo de Gemini; evita gemini-1.5-flash (descontinuado)
    api_key=llm_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta",
    enabled_toolsets=["web_search", "telegram_messaging", "notion_integration"],
    quiet_mode=True
)

# Arrancar el proceso de escucha continua del agente para Telegram
def iniciar_escucha_agente():
    print("🤖 Iniciando escucha de comandos en segundo plano...")
    try:
        agent.run_conversation(user_message="System boot")
    except Exception as e:
        print(f"⚠️ Nota de inicialización de backend: {e}")
        
    while True:
        try:
            agent.run_conversation(user_message="Check updates")
        except Exception as e:
            print(f"⚠️ Alerta en bucle de eventos: {e}")
        time.sleep(2)

threading.Thread(target=iniciar_escucha_agente, daemon=True).start()

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
    try:
        respuesta = agent.run_conversation(user_message=mensaje)
        return respuesta
    except Exception as e:
        return f"Error al procesar el comando: {e}"

demo = gr.ChatInterface(
    fn=responder_chat_web, 
    title="🧠 Centro de Control - Hermes Agent",
    description="Tu agente autónomo con acceso a Internet, Telegram y Notion está corriendo de forma segura en la nube."
)

if __name__ == "__main__":
    threading.Thread(target=mantener_despierto, daemon=True).start()
    demo.launch(server_name="0.0.0.0", server_port=7860)
