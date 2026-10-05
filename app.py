import os
import time
import threading
import requests
import gradio as gr

# Al desplegar, SnapDeploy te dará una URL de tu aplicación. 
# Debes poner esa URL en las variables de entorno de SnapDeploy como APP_URL
APP_URL = os.environ.get("APP_URL", "https://tu-app.snapdeploy.dev")

def auto_ping():
    """Mantiene el contenedor despierto enviando un estímulo cada 14 minutos"""
    time.sleep(30)
    print("🚀 Auto-ping iniciado...")
    while True:
        try:
            response = requests.get(APP_URL, timeout=10)
            print(f"⏱️ Ping enviado. Estado: {response.status_code}")
        except Exception as e:
            print(f"❌ Error en ping: {e}")
        time.sleep(14 * 60) # 14 minutos

# --- Aquí va la inicialización de tu agente Hermes ---
# agent.start_telegram_loop()

with gr.Blocks() as demo:
    gr.Markdown("# Hermes Agent en SnapDeploy")

if __name__ == "__main__":
    # Hilo para que no se duerma
    threading.Thread(target=auto_ping, daemon=True).start()
    # Lanzar la interfaz en el puerto expuesto
    demo.launch(server_name="0.0.0.0", server_port=7860)
