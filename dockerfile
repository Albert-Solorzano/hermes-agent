FROM python:3.10-slim

WORKDIR /app

# Instalar dependencias necesarias
RUN pip install --no-cache-dir requests gradio hermes-agent python-telegram-bot

# Copiar tu script de Python
COPY app.py .

# Exponer el puerto estándar que leerá SnapDeploy
EXPOSE 7860

CMD ["python", "app.py"]
