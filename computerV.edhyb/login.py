import cv2
from deepface import DeepFace
import os

print("📷 Iniciando sistema de seguridad...")

ruta_actual = os.path.dirname(os.path.abspath(__file__))
ruta_mi_foto = os.path.join(ruta_actual, "mi_foto.jpg")
ruta_intento = os.path.join(ruta_actual, "intento_login.jpg")

print(f"🔎 Verificando tu foto de referencia en: {ruta_mi_foto}")

img_referencia = cv2.imread(ruta_mi_foto)
if img_referencia is None:
    print("\n❌ ERROR FATAL: El archivo existe, pero está corrupto o es formato de celular (HEIC).")
    print("💡 SOLUCIÓN OBLIGATORIA: Abre tu foto original con el programa 'Paint' de Windows.")
    print("Dale a 'Archivo' -> 'Guardar como' -> 'Imagen JPEG'. Guárdala en esta carpeta y reemplaza la vieja.")
    exit()
else:
    print("✅ Foto de referencia cargada correctamente en la memoria.")

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not cap.isOpened():
    print("Error: No se pudo acceder a la cámara web.")
    exit()

print("\n--- INSTRUCCIONES ---")
print("1. Acomódate frente a la cámara.")
print("2. Presiona ESPACIO para tomar la foto.")
print("---------------------\n")

foto_tomada = False

while True:
    ret, frame = cap.read()
    if not ret: break

    cv2.imshow("Sistema de Seguridad", frame)
    tecla = cv2.waitKey(1) & 0xFF
    
    if tecla == 32: 
        cv2.imwrite(ruta_intento, frame)
        foto_tomada = True
        break
    elif tecla == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

if foto_tomada:
    img_intento = cv2.imread(ruta_intento)
    try:
        print("🧠 Analizando rostro con Inteligencia Artificial...")
        resultado = DeepFace.verify(
            img1_path="mi_foto.jpg", 
            img2_path="intento_login.jpg", 
            enforce_detection=False,
            detector_backend="mtcnn"  
        )
        
        if resultado["verified"]:
            print("\n✅ ¡ACCESO CONCEDIDO! Bienvenido al sistema.")
        else:
            print("\n❌ ACCESO DENEGADO. Rostro no reconocido.")
            
    except Exception as e:
        print(f"\n⚠️ Ocurrió un error en la verificación: {e}")
        
    if os.path.exists(ruta_intento):
        os.remove(ruta_intento)