import cv2
from pyzbar import pyzbar

def ler_codigo_barras_webcam():
    cap = cv2.VideoCapture(0)
    codigo_lido = None
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        barcodes = pyzbar.decode(frame)
        for barcode in barcodes:
            barcode_data = barcode.data.decode('utf-8')
            barcode_type = barcode.type
            if barcode_type == 'CODE39':
                codigo_lido = barcode_data
                # Desenhar retângulo ao redor do código
                (x, y, w, h) = barcode.rect
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, f'{barcode_data}', (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                break
        cv2.imshow('Leitor de Código de Barras', frame)
        if codigo_lido or cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()
    return codigo_lido

if __name__ == '__main__':
    print('Aproxime a carteirinha com o código de barras da webcam...')
    codigo = ler_codigo_barras_webcam()
    if codigo:
        print(f'Código lido: {codigo}')
    else:
        print('Nenhum código lido.') 