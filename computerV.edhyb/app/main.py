import os
import base64
import time
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Intentar importar DeepFace para resiliencia durante la fase de instalación
try:
    from deepface import DeepFace
except ImportError:
    DeepFace = None

app = FastAPI(
    title="MoodMeter API - Diagnóstico e Historial de Expresión Facial",
    description="Backend ligero para analizar emociones faciales en tiempo real usando DeepFace y Keras."
)

# Habilitar CORS para permitir integraciones locales ágiles y file://
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Definir carpetas clave de plantillas y archivos estáticos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

# Servir archivos estáticos si la carpeta existe
if os.path.exists(TEMPLATES_DIR):
    app.mount("/static", StaticFiles(directory=TEMPLATES_DIR), name="static")

# Modelo de datos Pydantic para recibir capturas en base64
class MoodAnalysisRequest(BaseModel):
    image: str  # String en formato DataURL o Base64 simple

def save_base64_image(base64_str: str, file_path: str):
    """Decodifica un string base64 (removiendo encabezados DataURL) y lo guarda en disco."""
    try:
        if "," in base64_str:
            base64_str = base64_str.split(",")[1]
        img_data = base64.b64decode(base64_str)
        with open(file_path, "wb") as f:
            f.write(img_data)
        return True
    except Exception as e:
        print(f"Error al decodificar imagen Base64: {e}")
        return False

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    """Sirve la interfaz web del MoodMeter."""
    index_path = os.path.join(TEMPLATES_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    return HTMLResponse(
        content="<h1>MoodMeter Frontend no encontrado</h1><p>Asegúrate de que la carpeta templates/index.html exista.</p>",
        status_code=404
    )

@app.post("/api/analyze-mood")
async def analyze_mood(payload: MoodAnalysisRequest):
    """
    Analiza una imagen facial y devuelve las emociones de forma porcentual,
    el recuadro de la cara y el tiempo de inferencia de la red neuronal.
    """
    if not DeepFace:
        raise HTTPException(
            status_code=503,
            detail="La librería DeepFace se está cargando o no se encuentra instalada en el sistema."
        )

    # Crear directorio temporal para procesar la imagen actual
    temp_dir = os.path.join(BASE_DIR, "..", "data", "temp")
    os.makedirs(temp_dir, exist_ok=True)
    
    temp_filename = f"mood_{int(time.time() * 1000)}.jpg"
    temp_path = os.path.join(temp_dir, temp_filename)

    # Guardar imagen en disco de forma temporal
    if not save_base64_image(payload.image, temp_path):
        raise HTTPException(status_code=400, detail="La imagen provista no tiene un formato Base64 decodificable válido.")

    start_time = time.time()
    try:
        # Analizar emociones usando DeepFace con el backend de OpenCV para máxima ligereza
        # actions=['emotion'] indica a la CNN calcular únicamente expresiones, acelerando el cómputo
        analysis = DeepFace.analyze(
            img_path=temp_path,
            actions=['emotion'],
            enforce_detection=True,  # Lanza excepción si no encuentra rostro detectable
            detector_backend="opencv"
        )

        inference_time = round(time.time() - start_time, 3)

        # Si el análisis retorna una lista (caso típico en versiones modernas de DeepFace)
        if isinstance(analysis, list):
            result = analysis[0]
        else:
            result = analysis

        # Extraer variables principales
        emotions_raw = result["emotion"]  # Diccionario con 7 emociones
        dominant_emotion = result["dominant_emotion"]
        region = result["region"]  # Caja facial: {x, y, w, h}

        # Asegurar remoción del archivo temporal
        if os.path.exists(temp_path):
            os.remove(temp_path)

        # Devolver respuesta estructurada
        return {
            "success": True,
            "dominant_emotion": dominant_emotion,
            "emotions": {k: float(round(v, 2)) for k, v in emotions_raw.items()},
            "box": {
                "x": int(region.get("x", 0)),
                "y": int(region.get("y", 0)),
                "w": int(region.get("w", 0)),
                "h": int(region.get("h", 0))
            },
            "inference_time_seconds": float(inference_time)
        }

    except Exception as e:
        # Limpiar archivo temporal
        if os.path.exists(temp_path):
            os.remove(temp_path)

        err_msg = str(e)
        if "Face could not be detected" in err_msg:
            raise HTTPException(
                status_code=422,
                detail="No se detectó ningún rostro en la imagen. Intenta con una mejor iluminación y colócate de frente."
            )
        raise HTTPException(
            status_code=500,
            detail=f"Error en el procesamiento neuronal de la imagen: {err_msg}"
        )
