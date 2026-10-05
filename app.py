import os
import time
import threading
import requests
import gradio as gr

# IMPORT OFICIAL Y CORRECTO DE NOUS RESEARCH
from run_agent import AIAgent as HermesAgent

# 1. LEER LAS VARIABLES DE ENTORNO OFICIALES
llm_api_key = os.environ.get("GEMINI_API_KEY")
telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN")
telegram_user_id = os.environ.get("TELEGRAM_USER_ID")
notion_token = os.environ.get("NOTION_API_KEY")
app_url = os.environ.get("APP_URL", "https://tu-app-temporal.dev")

# 2. INICIALIZAR EL BACKEND DE HERMES SEGÚN LA DOCUMENTACIÓN DEL SDK
# El constructor acepta 'api_key' y el modelo en formato estándar
agent = HermesAgent(
    model="google/gemini-1.5-flash",  # Formato oficial de ruta para el modelo
    api_key=llm_api_key,
    enabled_toolsets=["web_search", "telegram_messaging", "notion_integration"],
    quiet_mode=True
)

# Arrancar el proceso de escucha del agente de manera asíncrona
def iniciar_escucha_agente():
    try:
        # Intenta mapear la plataforma configurada en las variables de entorno
        agent.run_conversation(user_message="System boot", platform="telegram")
    except Exception as e:
        print(f"⚠️ Nota de inicialización de backend: {e}")

threading.Thread(target=iniciar_escucha_agente, daemon=True).start()

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
    # La función .chat() procesa el mensaje directamente en el SDK
    return agent.chat(mensaje)

demo = gr.ChatInterface(
    fn=responder_chat_web, 
    title="🧠 Centro de Control - Hermes Agent",
    description="Tu agente autónomo con acceso a Internet, Telegram y Notion está corriendo de forma segura en la nube."
)

if __name__ == "__main__":
    threading.Thread(target=mantener_despierto, daemon=True).start()
    demo.launch(server_name="0.0.0.0", server_port=7860)
