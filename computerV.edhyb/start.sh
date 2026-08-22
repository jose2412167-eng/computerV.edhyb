#!/bin/bash

# start.sh - Script de inicialización y despliegue rápido para MoodMeter
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "=========================================================="
echo "          INICIANDO PIPELINE DE MOODMETER 📊🎭            "
echo "=========================================================="
echo ""

# Validar y crear entorno virtual venv si no existe
if [ ! -d "venv" ]; then
    echo "[!] Entorno virtual 'venv' no detectado. Creándolo e instalando dependencias..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
else
    echo "[x] Entorno virtual 'venv' detectado. Activándolo..."
    source venv/bin/activate
fi

echo ""
echo "[*] Servidor FastAPI arrancando de forma local en http://127.0.0.1:8000"
echo "[*] Abre tu navegador web en esa dirección para ver tu MoodMeter."
echo "[!] Nota: La primera vez que el backend realice un análisis, DeepFace"
echo "    descargará automáticamente el modelo convolucional de emociones (~20MB)."
echo "    Esto se realiza una sola vez de forma interna."
echo ""
echo "Presiona Ctrl+C para detener el servidor."
echo "----------------------------------------------------------"

# Iniciar servidor local
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
