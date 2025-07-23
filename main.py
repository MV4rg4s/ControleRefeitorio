import sys
import traceback
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget, QApplication, QHBoxLayout, QFrame, QGridLayout
from PyQt5.QtGui import QPixmap, QColor, QPalette, QImage, QFont
from PyQt5.QtCore import Qt, QTimer
import cv2
from pyzbar import pyzbar
# Certifique-se de que a função no db_utils se chama 'buscar_aluno_por_id' ou altere aqui
from db_utils import buscar_aluno_por_id 
from face_overlay import detectar_rosto_e_overlay
import numpy as np

# Hook para capturar exceções não tratadas e exibi-las no console
def excecao_nao_tratada(exctype, value, tb):
    print('--- ERRO INESPERADO NA APLICAÇÃO ---')
    traceback.print_tb(tb)
    print(f'TIPO: {exctype.__name__}')
    print(f'MENSAGEM: {value}')
    print('------------------------------------')
    sys.__excepthook__(exctype, value, tb)

sys.excepthook = excecao_nao_tratada

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        # Configurações da Câmera e Timer
        self.cap = cv2.VideoCapture(0)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.atualizar_frame)
        self.timer.start(30) # ~33 FPS

        # Variáveis de estado
        self.reset_state()
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Inicialização da UI
        self.setup_ui()

    def reset_state(self):
        """Reseta o estado da aplicação para a leitura inicial."""
        self.codigo_lido = None
        self.aluno_atual = None
        self.foto_aluno = None
        self.capturando_foto = False

    def setup_ui(self):
        """Cria e organiza todos os widgets da interface."""
        self.setWindowTitle('Controle de Refeitório - IFF')
        self.setGeometry(100, 100, 800, 600)

        # Layout Principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Header (Cabeçalho)
        header_frame = QFrame(self)
        header_frame.setObjectName("header")
        header_layout = QHBoxLayout(header_frame)
        
        logo_label = QLabel(self)
        pixmap = QPixmap('logo_iff.png') # Certifique-se que o logo está na pasta
        if not pixmap.isNull():
            logo_label.setPixmap(pixmap.scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        
        title_label = QLabel('Controle de Entrada e Saída do Refeitório', self)
        title_label.setObjectName("title")

        header_layout.addWidget(logo_label)
        header_layout.addSpacing(10)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        main_layout.addWidget(header_frame)

        # 2. Content Area (Área de Conteúdo)
        content_frame = QFrame(self)
        content_layout = QHBoxLayout(content_frame)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)

        # 2.1. Painel de Vídeo
        video_panel = QFrame(self)
        video_panel.setObjectName("videoPanel")
        video_layout = QVBoxLayout(video_panel)
        self.video_label = QLabel('Iniciando câmera...', self)
        self.video_label.setAlignment(Qt.AlignCenter)
        video_layout.addWidget(self.video_label)
        
        # 2.2. Painel de Informações do Aluno
        info_panel = QFrame(self)
        info_panel.setObjectName("infoPanel")
        info_layout = QGridLayout(info_panel)
        info_layout.setContentsMargins(20, 20, 20, 20)

        info_title = QLabel("Dados do Aluno", self)
        info_title.setObjectName("infoTitle")
        
        # Labels e campos de dados
        self.nome_label = QLabel("Nome:", self)
        self.nome_valor = QLabel("-", self)
        self.matricula_label = QLabel("Matrícula:", self)
        self.matricula_valor = QLabel("-", self)
        self.curso_label = QLabel("Curso:", self)
        self.curso_valor = QLabel("-", self)
        
        info_layout.addWidget(info_title, 0, 0, 1, 2)
        info_layout.addWidget(self.nome_label, 1, 0)
        info_layout.addWidget(self.nome_valor, 1, 1)
        info_layout.addWidget(self.matricula_label, 2, 0)
        info_layout.addWidget(self.matricula_valor, 2, 1)
        info_layout.addWidget(self.curso_label, 3, 0)
        info_layout.addWidget(self.curso_valor, 3, 1)
        info_layout.setColumnStretch(1, 1) # Faz a coluna de valor esticar

        content_layout.addWidget(video_panel, 2) # Ocupa 2/3 do espaço
        content_layout.addWidget(info_panel, 1)  # Ocupa 1/3 do espaço
        
        main_layout.addWidget(content_frame)

        # 3. Status Bar (Barra de Status)
        self.status_bar = QLabel("Aguardando leitura do código de barras...", self)
        self.status_bar.setObjectName("statusBar")
        self.status_bar.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status_bar)

        # Aplicar o Stylesheet
        self.apply_stylesheet()

    def apply_stylesheet(self):
        """Aplica o QSS (CSS do Qt) para estilizar a aplicação."""
        style = """
            /* Fundo da janela principal */
            QWidget {
                background-color: #F0F0F0; /* Cinza claro */
            }
            /* Cabeçalho */
            #header {
                background-color: #008000; /* Verde IFF */
                padding: 10px;
            }
            #title {
                color: white;
                font-size: 20px;
                font-weight: bold;
            }
            /* Painéis de conteúdo */
            #videoPanel, #infoPanel {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #DDDDDD;
            }
            #infoTitle {
                font-size: 18px;
                font-weight: bold;
                color: #333;
                border-bottom: 2px solid #008000;
                margin-bottom: 15px;
            }
            /* Labels do painel de informações */
            QLabel {
                font-size: 14px;
                color: #555;
            }
            /* Barra de Status */
            #statusBar {
                background-color: #333;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 12px;
            }
        """
        self.setStyleSheet(style)

    def set_status_message(self, message, status='normal'):
        """Atualiza a mensagem e cor da barra de status."""
        self.status_bar.setText(message)
        if status == 'success':
            style = "background-color: #008000; color: white;" # Verde
        elif status == 'error':
            style = "background-color: #D32F2F; color: white;" # Vermelho
        else: # normal
            style = "background-color: #333; color: white;" # Cinza escuro
        
        self.status_bar.setStyleSheet(f"#statusBar {{ {style} padding: 12px; font-size: 16px; font-weight: bold; }}")

    def clear_student_info(self):
        """Limpa os dados do painel de informações."""
        self.nome_valor.setText("-")
        self.matricula_valor.setText("-")
        self.curso_valor.setText("-")
        
    def atualizar_frame(self):
        """Função principal executada pelo Timer para processar cada frame da câmera."""
        try:
            ret, frame = self.cap.read()
            if not ret:
                self.set_status_message("Falha ao capturar frame da webcam", "error")
                return

            processed_frame = frame.copy()

            # Se um aluno já foi lido, passa para a fase de captura de foto
            if self.capturando_foto:
                processed_frame, centralizado, bbox = detectar_rosto_e_overlay(frame, self.face_cascade)
                if centralizado:
                    x, y, w, h = bbox
                    self.foto_aluno = frame[y:y+h, x:x+w]
                    self.set_status_message("Foto capturada com sucesso!", "success")
                    self.capturando_foto = False
                    # Aqui você salvaria a foto e o registro no banco
                    # Ex: salvar_registro(self.aluno_atual['id'], self.foto_aluno)
                    QTimer.singleShot(3000, self.reset_and_clear) # Reseta após 3 segundos
            else:
                # Se não, continua tentando ler o código de barras
                barcodes = pyzbar.decode(frame)
                if barcodes:
                    for barcode in barcodes:
                        if not self.codigo_lido: # Processa apenas o primeiro código
                            barcode_data = barcode.data.decode('utf-8')
                            self.codigo_lido = barcode_data
                            
                            aluno = buscar_aluno_por_id(self.codigo_lido)
                            if aluno:
                                self.aluno_atual = aluno
                                self.nome_valor.setText(aluno.get('nome', 'N/A'))
                                self.matricula_valor.setText(aluno.get('matricula', 'N/A'))
                                self.curso_valor.setText(aluno.get('curso', 'N/A'))
                                self.set_status_message("Aluno encontrado! Encaixe o rosto para a foto.", "success")
                                self.capturando_foto = True
                            else:
                                self.set_status_message(f"Aluno com ID '{self.codigo_lido}' não encontrado!", "error")
                                self.clear_student_info()
                                QTimer.singleShot(3000, self.reset_and_clear) # Reseta após 3 segundos
                            break # Sai do loop de barcodes

            # Exibe o frame processado na tela
            self.display_image(processed_frame)

        except Exception as e:
            print(f"Erro em atualizar_frame: {e}")
            traceback.print_exc()

    def reset_and_clear(self):
        """Função para limpar os dados e o status para uma nova leitura."""
        self.reset_state()
        self.clear_student_info()
        self.set_status_message("Aguardando leitura do código de barras...")

    def display_image(self, img):
        """Converte uma imagem do OpenCV para QPixmap e exibe no QLabel."""
        rgb_image = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)
        self.video_label.setPixmap(pixmap.scaled(self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def closeEvent(self, event):
        """Libera a câmera ao fechar a janela."""
        self.cap.release()
        super().closeEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())