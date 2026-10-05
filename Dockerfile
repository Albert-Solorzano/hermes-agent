FROM python:3.11-slim

WORKDIR /app

# Instalar las librerías del requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar el código del agente
COPY app.py .

# Exponer el puerto obligatorio de SnapDeploy
EXPOSE 7860

CMD ["python", "app.py"]
