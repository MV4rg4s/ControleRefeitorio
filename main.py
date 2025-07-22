import sys
import traceback
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget, QApplication
from PyQt5.QtGui import QPixmap, QColor, QPalette, QImage
from PyQt5.QtCore import Qt, QTimer
import cv2
from pyzbar import pyzbar
from db_utils import buscar_aluno_por_id
from face_overlay import capturar_foto_automaticamente, detectar_rosto_e_overlay
import cv2
import numpy as np

def excecao_nao_tratada(exctype, value, tb):
    print('Exceção não tratada:', exctype, value)
    traceback.print_tb(tb)
    sys.__excepthook__(exctype, value, tb)

sys.excepthook = excecao_nao_tratada

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Controle de Refeitório - IFF')
        self.setGeometry(100, 100, 600, 500)
        self.setup_ui()
        self.cap = cv2.VideoCapture(0)
        self.timer = QTimer()
        self.timer.timeout.connect(self.atualizar_frame)
        self.timer.start(30)
        self.codigo_lido = None
        self.aluno_atual = None
        self.foto_aluno = None

    def setup_ui(self):
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(34, 139, 34))
        self.setPalette(palette)
        self.setAutoFillBackground(True)
        layout = QVBoxLayout()
        self.logo_label = QLabel(self)
        self.logo_label.setAlignment(Qt.AlignCenter)
        pixmap = QPixmap('logo_iff.png')
        if not pixmap.isNull():
            self.logo_label.setPixmap(pixmap.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.logo_label.setText('LOGO IFF')
            self.logo_label.setStyleSheet('color: white; font-size: 24px;')
        layout.addWidget(self.logo_label)
        title = QLabel('Controle de Entrada e Saída do Refeitório')
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet('color: white; font-size: 20px; font-weight: bold;')
        layout.addWidget(title)
        self.info_label = QLabel('Aguardando leitura do código de barras...')
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet('color: white; font-size: 16px;')
        layout.addWidget(self.info_label)
        self.video_label = QLabel(self)
        self.video_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.video_label)
        self.dados_aluno_label = QLabel('')
        self.dados_aluno_label.setAlignment(Qt.AlignCenter)
        self.dados_aluno_label.setStyleSheet('color: white; font-size: 16px;')
        layout.addWidget(self.dados_aluno_label)
        self.setLayout(layout)

    def atualizar_frame(self):
        try:
            ret, frame = self.cap.read()
            if not ret:
                print('Falha ao capturar frame da webcam')
                return
            barcodes = pyzbar.decode(frame)
            if not self.codigo_lido:
                for barcode in barcodes:
                    barcode_data = barcode.data.decode('utf-8')
                    barcode_type = barcode.type
                    print(f'Código detectado: {barcode_data}, tipo: {barcode_type}')
                    if barcode_type in ['CODE128', 'CODE39']:
                        self.codigo_lido = barcode_data
                        print(f'Código lido: {self.codigo_lido}')
                        self.info_label.setText(f'Código lido: {self.codigo_lido}')
                        aluno = buscar_aluno_por_id(self.codigo_lido)
                        print(f'Resultado da busca no banco: {aluno}')
                        if aluno is not None:
                            print('Tipo do aluno:', type(aluno))
                            print('Campos do aluno:', aluno.keys())
                            print('Conteúdo do aluno:', aluno)
                            data_nasc = str(aluno['data_nascimento']) if aluno['data_nascimento'] is not None else ''
                            dados = f"Nome: {aluno['nome']}\nMatrícula: {aluno['matricula']}\nNascimento: {data_nasc}\nCurso: {aluno['curso']}"
                            self.dados_aluno_label.setText(dados + '\nAguardando captura do rosto...')
                            self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                            self.capturando_foto = True
                        else:
                            print('Aluno não encontrado!')
                            self.dados_aluno_label.setText('Aluno não encontrado!')
                        break
            # Se for para capturar a foto, desenhar overlay e capturar automaticamente
            if hasattr(self, 'capturando_foto') and self.capturando_foto:
                overlay_frame, centralizado, bbox = detectar_rosto_e_overlay(frame, self.face_cascade)
                print(f'Centralizado: {centralizado}, bbox: {bbox}')
                if centralizado:
                    x, y, w, h = bbox
                    self.foto_aluno = frame[y:y+h, x:x+w]
                    self.dados_aluno_label.setText(self.dados_aluno_label.text() + '\nFoto capturada!')
                    self.capturando_foto = False
                rgb_image = cv2.cvtColor(overlay_frame, cv2.COLOR_BGR2RGB)
            else:
                # Desenhar retângulo nos códigos detectados
                for barcode in barcodes:
                    (x, y, w, h) = barcode.rect
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            self.video_label.setPixmap(QPixmap.fromImage(qt_image).scaled(400, 300, Qt.KeepAspectRatio))
        except Exception as e:
            print('Erro em atualizar_frame:', e)

    def closeEvent(self, event):
        self.cap.release()
        super().closeEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_()) 