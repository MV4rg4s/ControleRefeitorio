import cv2
import numpy as np

def detectar_rosto_e_overlay(frame, face_cascade):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(120, 120))
    overlay_frame = frame.copy()
    rosto_centralizado = False
    bbox = None
    
    # Desenhar oval guia no centro da tela
    frame_h, frame_w = frame.shape[:2]
    center_x, center_y = frame_w // 2, frame_h // 2
    cv2.ellipse(overlay_frame, (center_x, center_y), (80, 100), 0, 0, 360, (0, 255, 0), 2)
    
    # Adicionar texto de instrução
    cv2.putText(overlay_frame, 'Encaixe seu rosto', (30, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    for (x, y, w, h) in faces:
        # Desenhar oval ao redor do rosto detectado
        face_center = (x + w // 2, y + h // 2)
        face_axes = (w // 2, h // 2)
        
        # Verificar se o rosto está centralizado
        if (abs(face_center[0] - center_x) < 50) and (abs(face_center[1] - center_y) < 50):
            # Rosto centralizado - desenhar em verde
            cv2.ellipse(overlay_frame, face_center, face_axes, 0, 0, 360, (0, 255, 0), 3)
            rosto_centralizado = True
            bbox = (x, y, w, h)
            cv2.putText(overlay_frame, 'ROSTO CENTRALIZADO!', (30, 60), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        else:
            # Rosto não centralizado - desenhar em vermelho
            cv2.ellipse(overlay_frame, face_center, face_axes, 0, 0, 360, (0, 0, 255), 2)
            cv2.putText(overlay_frame, 'Centralize o rosto', (30, 60), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
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