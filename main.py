import sys
import traceback
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget, QApplication, QFrame, QHBoxLayout
from PyQt5.QtGui import QPixmap, QColor, QPalette, QImage, QFont
from PyQt5.QtCore import Qt, QTimer
import cv2
from pyzbar import pyzbar
from db_utils import buscar_aluno_por_id, registrar_entrada_ou_saida, aluno_com_entrada_aberta
from face_overlay import detectar_rosto_e_overlay
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
        self.setGeometry(100, 100, 800, 600)
        self.setup_ui()
        self.cap = cv2.VideoCapture(0)
        self.timer = QTimer()
        self.timer.timeout.connect(self.atualizar_frame)
        self.timer.start(30)
        self.codigo_lido = None
        self.aluno_atual = None
        self.foto_aluno = None

    def setup_ui(self):
        # Gradiente de fundo
        self.setStyleSheet('''
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #e8ffe8, stop:1 #228B22);
            }
        ''')
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignCenter)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(20)

        # Logo do IFF
        self.logo_label = QLabel(self)
        self.logo_label.setAlignment(Qt.AlignCenter)
        pixmap = QPixmap('logo_iff.png')
        if not pixmap.isNull():
            self.logo_label.setPixmap(pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.logo_label.setText('IFF')
            self.logo_label.setStyleSheet('color: #228B22; font-size: 36px; font-weight: bold;')
        main_layout.addWidget(self.logo_label)

        # Título
        title = QLabel('Controle de Entrada e Saída do Refeitório')
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet('color: #228B22; font-size: 28px; font-weight: bold; letter-spacing: 1px;')
        main_layout.addWidget(title)

        # Cartão centralizado para dados do aluno
        self.card = QFrame(self)
        self.card.setStyleSheet('''
            QFrame {
                background: white;
                border-radius: 18px;
                box-shadow: 0px 4px 24px rgba(34,139,34,0.15);
            }
        ''')
        card_layout = QVBoxLayout()
        card_layout.setAlignment(Qt.AlignCenter)
        card_layout.setContentsMargins(30, 30, 30, 30)
        card_layout.setSpacing(18)

        # Webcam com borda arredondada
        self.video_label = QLabel(self)
        self.video_label.setFixedSize(420, 320)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet('''
            QLabel {
                border-radius: 18px;
                border: 3px solid #228B22;
                background: #f6fff6;
            }
        ''')
        card_layout.addWidget(self.video_label)

        # Info label (feedback)
        self.info_label = QLabel('Aguardando leitura do código de barras...')
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet('color: #228B22; font-size: 18px; font-weight: bold;')
        card_layout.addWidget(self.info_label)

        # Dados do aluno
        self.dados_aluno_label = QLabel('')
        self.dados_aluno_label.setAlignment(Qt.AlignCenter)
        self.dados_aluno_label.setWordWrap(True)
        self.dados_aluno_label.setStyleSheet('color: #333; font-size: 20px; font-weight: 500;')
        card_layout.addWidget(self.dados_aluno_label)

        self.card.setLayout(card_layout)
        main_layout.addWidget(self.card, alignment=Qt.AlignCenter)
        self.setLayout(main_layout)

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
                            self.aluno_atual = aluno
                            registro_aberto = aluno_com_entrada_aberta(aluno['id'])
                            if registro_aberto:
                                # Saída: registrar imediatamente, sem foto
                                tipo, horario = registrar_entrada_ou_saida(aluno['id'], None)
                                dados = f"<b>Nome:</b> {aluno['nome']}<br><b>Matrícula:</b> {aluno['matricula']}<br><b>Curso:</b> {aluno['curso']}"
                                self.dados_aluno_label.setStyleSheet('color: #228B22; font-size: 22px; font-weight: bold;')
                                self.dados_aluno_label.setText(dados + f'<br><span style="color:#228B22;">Saída registrada: {horario:%d/%m/%Y %H:%M:%S}</span>')
                                self.info_label.setText('Saída realizada com sucesso!')
                                QTimer.singleShot(3000, self.resetar_fluxo)
                            else:
                                # Entrada: seguir para captura de foto
                                data_nasc = str(aluno['data_nascimento']) if aluno['data_nascimento'] is not None else ''
                                dados = f"<b>Nome:</b> {aluno['nome']}<br><b>Matrícula:</b> {aluno['matricula']}<br><b>Nascimento:</b> {data_nasc}<br><b>Curso:</b> {aluno['curso']}"
                                self.dados_aluno_label.setStyleSheet('color: #333; font-size: 20px; font-weight: 500;')
                                self.dados_aluno_label.setText(dados + '<br><span style="color:#228B22;">Aguardando captura do rosto...</span>')
                                self.info_label.setText('Aguardando captura do rosto...')
                                self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                                self.capturando_foto = True
                        else:
                            print('Aluno não encontrado!')
                            self.dados_aluno_label.setStyleSheet('color: #c0392b; font-size: 20px; font-weight: bold;')
                            self.dados_aluno_label.setText('Aluno não encontrado!')
                            self.info_label.setText('Erro: Aluno não encontrado!')
                        break
            # Captura de foto e registro de entrada
            if hasattr(self, 'capturando_foto') and self.capturando_foto:
                overlay_frame, centralizado, bbox = detectar_rosto_e_overlay(frame, self.face_cascade)
                if centralizado:
                    x, y, w, h = bbox
                    self.foto_aluno = frame[y:y+h, x:x+w]
                    self.dados_aluno_label.setText(self.dados_aluno_label.text() + '<br><span style="color:#228B22;">Foto capturada!</span>')
                    self.info_label.setText('Foto capturada!')
                    self.capturando_foto = False
                    # Registrar entrada
                    if self.aluno_atual is not None:
                        try:
                            tipo, horario = registrar_entrada_ou_saida(self.aluno_atual['id'], self.foto_aluno)
                            self.dados_aluno_label.setStyleSheet('color: #228B22; font-size: 22px; font-weight: bold;')
                            self.dados_aluno_label.setText(self.dados_aluno_label.text() + f'<br><span style="color:#228B22;">Entrada registrada: {horario:%d/%m/%Y %H:%M:%S}</span>')
                            self.info_label.setText('Entrada realizada com sucesso!')
                            QTimer.singleShot(3000, self.resetar_fluxo)
                        except Exception as e:
                            self.dados_aluno_label.setStyleSheet('color: #c0392b; font-size: 20px; font-weight: bold;')
                            self.dados_aluno_label.setText(self.dados_aluno_label.text() + f'<br>Erro ao registrar: {e}')
                            self.info_label.setText('Erro ao registrar entrada!')
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
            self.video_label.setPixmap(QPixmap.fromImage(qt_image).scaled(420, 320, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        except Exception as e:
            print('Erro em atualizar_frame:', e)

    def resetar_fluxo(self):
        self.codigo_lido = None
        self.aluno_atual = None
        self.foto_aluno = None
        self.info_label.setText('Aguardando leitura do código de barras...')
        self.dados_aluno_label.setText('')

    def closeEvent(self, event):
        self.cap.release()
        super().closeEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_()) 