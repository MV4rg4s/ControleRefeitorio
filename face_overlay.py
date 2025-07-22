import cv2
import numpy as np

def detectar_rosto_e_overlay(frame, face_cascade):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(120, 120))
    overlay_frame = frame.copy()
    rosto_centralizado = False
    bbox = None
    for (x, y, w, h) in faces:
        # Desenhar oval (overlay)
        center = (x + w // 2, y + h // 2)
        axes = (w // 2, h // 2)
        cv2.ellipse(overlay_frame, center, axes, 0, 0, 360, (0, 255, 0), 3)
        # Critério de centralização (ajuste conforme necessário)
        frame_h, frame_w = frame.shape[:2]
        if (abs(center[0] - frame_w // 2) < 40) and (abs(center[1] - frame_h // 2) < 40):
            rosto_centralizado = True
            bbox = (x, y, w, h)
        break  # Só considera o primeiro rosto
    return overlay_frame, rosto_centralizado, bbox

def capturar_foto_automaticamente():
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    cap = cv2.VideoCapture(0)
    foto = None
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        overlay_frame, centralizado, bbox = detectar_rosto_e_overlay(frame, face_cascade)
        cv2.putText(overlay_frame, 'Encaixe seu rosto no oval', (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)
        cv2.imshow('Captura de Foto', overlay_frame)
        if centralizado:
            x, y, w, h = bbox
            foto = frame[y:y+h, x:x+w]
            cv2.putText(overlay_frame, 'Foto capturada!', (30, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,0), 2)
            cv2.imshow('Captura de Foto', overlay_frame)
            cv2.waitKey(1000)
            break
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()
    return foto

if __name__ == '__main__':
    foto = capturar_foto_automaticamente()
    if foto is not None:
        cv2.imshow('Foto Capturada', foto)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    else:
        print('Nenhuma foto capturada.') 