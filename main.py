import sys
import traceback
from PyQt5.QtWidgets import (QLabel, QVBoxLayout, QWidget, QApplication, QHBoxLayout, 
                             QFrame, QGridLayout, QPushButton, QTabWidget, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QMessageBox, QDateEdit, QComboBox)
from PyQt5.QtGui import QPixmap, QColor, QPalette, QImage, QFont, QIcon
from PyQt5.QtCore import Qt, QTimer, QDate
import cv2
from pyzbar import pyzbar
from db_utils import (buscar_aluno_por_id, registrar_entrada_ou_saida, 
                     relatorio_entradas_por_turno, relatorio_semanal, relatorio_mensal,
                     gerar_grafico_frequencia, obter_estatisticas_gerais)
from face_overlay import detectar_rosto_e_overlay
import numpy as np
from datetime import datetime, timedelta

# Hook para capturar exceções não tratadas e exibi-las no console
def excecao_nao_tratada(exctype, value, tb):
    print('--- ERRO INESPERADO NA APLICAÇÃO ---')
    traceback.print_tb(tb)
    print(f'TIPO: {exctype.__name__}')
    print(f'MENSAGEM: {value}')
    print('------------------------------------')
    sys.__excepthook__(exctype, value, tb)

sys.excepthook = excecao_nao_tratada

class ModernMainWindow(QWidget):
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
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumSize(1000, 700)

        # Layout Principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Header Moderno
        self.setup_header(main_layout)

        # 2. Content Area com Tabs
        self.setup_content_area(main_layout)

        # 3. Status Bar Moderna
        self.setup_status_bar(main_layout)

        # Aplicar o Stylesheet Moderno
        self.apply_modern_stylesheet()

    def setup_header(self, main_layout):
        """Cria o cabeçalho moderno."""
        header_frame = QFrame(self)
        header_frame.setObjectName("header")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 15, 20, 15)
        
        # Logo
        logo_label = QLabel(self)
        pixmap = QPixmap('logo_iff.png')
        if not pixmap.isNull():
            logo_label.setPixmap(pixmap.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        
        # Título
        title_label = QLabel('Sistema de Controle de Refeitório', self)
        title_label.setObjectName("title")
        
        # Estatísticas rápidas
        stats_frame = QFrame(self)
        stats_frame.setObjectName("statsFrame")
        stats_layout = QHBoxLayout(stats_frame)
        stats_layout.setContentsMargins(15, 8, 15, 8)
        stats_layout.setSpacing(20)
        
        self.stats_alunos = QLabel("Alunos: 0", self)
        self.stats_hoje = QLabel("Hoje: 0", self)
        self.stats_mes = QLabel("Mês: 0", self)
        
        for stat in [self.stats_alunos, self.stats_hoje, self.stats_mes]:
            stat.setObjectName("statLabel")
            stats_layout.addWidget(stat)
        
        header_layout.addWidget(logo_label)
        header_layout.addSpacing(15)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(stats_frame)
        
        main_layout.addWidget(header_frame)

    def setup_content_area(self, main_layout):
        """Cria a área de conteúdo com abas."""
        content_frame = QFrame(self)
        content_frame.setObjectName("contentFrame")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)

        # Criar TabWidget
        self.tab_widget = QTabWidget(self)
        self.tab_widget.setObjectName("tabWidget")
        
        # Tab 1: Controle Principal
        self.setup_main_tab()
        
        # Tab 2: Relatórios
        self.setup_reports_tab()
        
        # Tab 3: Gráficos
        self.setup_charts_tab()
        
        content_layout.addWidget(self.tab_widget)
        main_layout.addWidget(content_frame)

    def setup_main_tab(self):
        """Configura a aba principal de controle."""
        main_tab = QWidget()
        main_layout = QHBoxLayout(main_tab)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(20)

        # Painel de Vídeo
        video_panel = QFrame(self)
        video_panel.setObjectName("videoPanel")
        video_layout = QVBoxLayout(video_panel)
        video_layout.setContentsMargins(15, 15, 15, 15)
        
        video_title = QLabel("Câmera", self)
        video_title.setObjectName("panelTitle")
        video_layout.addWidget(video_title)
        
        self.video_label = QLabel('Iniciando câmera...', self)
        self.video_label.setObjectName("videoLabel")
        self.video_label.setAlignment(Qt.AlignCenter)
        video_layout.addWidget(self.video_label)
        
        # Painel de Informações
        info_panel = QFrame(self)
        info_panel.setObjectName("infoPanel")
        info_layout = QVBoxLayout(info_panel)
        info_layout.setContentsMargins(20, 20, 20, 20)

        info_title = QLabel("Dados do Aluno", self)
        info_title.setObjectName("panelTitle")
        info_layout.addWidget(info_title)
        
        # Grid para informações
        info_grid = QGridLayout()
        info_grid.setSpacing(15)
        
        self.nome_label = QLabel("Nome:", self)
        self.nome_valor = QLabel("-", self)
        self.nome_valor.setObjectName("infoValue")
        
        self.matricula_label = QLabel("Matrícula:", self)
        self.matricula_valor = QLabel("-", self)
        self.matricula_valor.setObjectName("infoValue")
        
        self.curso_label = QLabel("Curso:", self)
        self.curso_valor = QLabel("-", self)
        self.curso_valor.setObjectName("infoValue")
        
        self.status_label = QLabel("Status:", self)
        self.status_valor = QLabel("Aguardando...", self)
        self.status_valor.setObjectName("statusValue")
        
        info_grid.addWidget(self.nome_label, 0, 0)
        info_grid.addWidget(self.nome_valor, 0, 1)
        info_grid.addWidget(self.matricula_label, 1, 0)
        info_grid.addWidget(self.matricula_valor, 1, 1)
        info_grid.addWidget(self.curso_label, 2, 0)
        info_grid.addWidget(self.curso_valor, 2, 1)
        info_grid.addWidget(self.status_label, 3, 0)
        info_grid.addWidget(self.status_valor, 3, 1)
        
        info_layout.addLayout(info_grid)
        info_layout.addStretch()
        
        # Botões de ação
        buttons_layout = QHBoxLayout()
        
        self.btn_gerar_relatorio = QPushButton("Gerar Relatório", self)
        self.btn_gerar_relatorio.setObjectName("actionButton")
        self.btn_gerar_relatorio.clicked.connect(self.gerar_relatorio_rapido)
        
        self.btn_limpar = QPushButton("Limpar", self)
        self.btn_limpar.setObjectName("secondaryButton")
        self.btn_limpar.clicked.connect(self.reset_and_clear)
        
        buttons_layout.addWidget(self.btn_gerar_relatorio)
        buttons_layout.addWidget(self.btn_limpar)
        
        info_layout.addLayout(buttons_layout)

        main_layout.addWidget(video_panel, 2)
        main_layout.addWidget(info_panel, 1)
        
        self.tab_widget.addTab(main_tab, "Controle")

    def setup_reports_tab(self):
        """Configura a aba de relatórios."""
        reports_tab = QWidget()
        layout = QVBoxLayout(reports_tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Controles de filtro
        filter_frame = QFrame(self)
        filter_frame.setObjectName("filterFrame")
        filter_layout = QHBoxLayout(filter_frame)
        
        self.date_edit = QDateEdit(self)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setObjectName("dateEdit")
        
        self.period_combo = QComboBox(self)
        self.period_combo.addItems(["Hoje", "Esta Semana", "Este Mês", "Personalizado"])
        self.period_combo.setObjectName("comboBox")
        
        self.btn_relatorio_turno = QPushButton("Relatório por Turno", self)
        self.btn_relatorio_turno.setObjectName("reportButton")
        self.btn_relatorio_turno.clicked.connect(self.gerar_relatorio_turno)
        
        self.btn_relatorio_semanal = QPushButton("Relatório Semanal", self)
        self.btn_relatorio_semanal.setObjectName("reportButton")
        self.btn_relatorio_semanal.clicked.connect(self.gerar_relatorio_semanal)
        
        filter_layout.addWidget(QLabel("Data:"))
        filter_layout.addWidget(self.date_edit)
        filter_layout.addWidget(QLabel("Período:"))
        filter_layout.addWidget(self.period_combo)
        filter_layout.addWidget(self.btn_relatorio_turno)
        filter_layout.addWidget(self.btn_relatorio_semanal)
        filter_layout.addStretch()
        
        layout.addWidget(filter_frame)

        # Tabela de resultados
        self.reports_table = QTableWidget(self)
        self.reports_table.setObjectName("reportsTable")
        self.reports_table.setColumnCount(4)
        self.reports_table.setHorizontalHeaderLabels(["Período", "Turno", "Total Entradas", "Alunos Únicos"])
        self.reports_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        layout.addWidget(self.reports_table)
        
        self.tab_widget.addTab(reports_tab, "Relatórios")

    def setup_charts_tab(self):
        """Configura a aba de gráficos."""
        charts_tab = QWidget()
        layout = QVBoxLayout(charts_tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Controles para gráficos
        chart_controls = QFrame(self)
        chart_controls.setObjectName("filterFrame")
        controls_layout = QVBoxLayout(chart_controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        
        # Container para centralizar o botão à esquerda
        button_container = QHBoxLayout()
        
        self.btn_gerar_grafico = QPushButton("Gerar Gráfico de Frequência", self)
        self.btn_gerar_grafico.setObjectName("tabButton")
        self.btn_gerar_grafico.clicked.connect(self.gerar_grafico_frequencia)
        
        button_container.addWidget(self.btn_gerar_grafico)
        button_container.addStretch()
        
        controls_layout.addLayout(button_container)
        
        layout.addWidget(chart_controls)

        # Área para exibir gráfico
        self.chart_label = QLabel("Clique em 'Gerar Gráfico' para visualizar a frequência de entradas", self)
        self.chart_label.setObjectName("chartLabel")
        self.chart_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.chart_label)
        
        self.tab_widget.addTab(charts_tab, "Gráficos")

    def setup_status_bar(self, main_layout):
        """Cria a barra de status moderna."""
        self.status_bar = QLabel("Sistema pronto - Aguardando leitura do código de barras...", self)
        self.status_bar.setObjectName("statusBar")
        self.status_bar.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status_bar)

    def apply_modern_stylesheet(self):
        """Aplica o QSS moderno para estilizar a aplicação."""
        style = """
            /* Variáveis CSS */
            QWidget {
                font-family: 'Segoe UI', Arial, sans-serif;
                background-color: #f8f9fa;
            }
            
            /* Header */
            #header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-bottom: 1px solid #e9ecef;
            }
            
            #title {
                color: black;
                font-size: 24px;
                font-weight: 600;
                letter-spacing: 0.5px;
            }
            
            #statsFrame {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
            
            #statLabel {
                color: white;
                font-size: 14px;
                font-weight: 500;
            }
            
            /* Content Frame */
            #contentFrame {
                background-color: #ffffff;
                border-radius: 12px;
                margin: 20px;
                border: 1px solid #e9ecef;
            }
            
            /* Tab Widget */
            #tabWidget {
                background-color: transparent;
                border: none;
            }
            
            #tabWidget::pane {
                border: none;
                background-color: transparent;
            }
            
            #tabWidget QTabBar::tab {
                background-color: #f8f9fa;
                color: #6c757d;
                padding: 12px 24px;
                margin-right: 4px;
                border-radius: 8px 8px 0 0;
                font-weight: 500;
                border: 1px solid #e9ecef;
                border-bottom: none;
            }
            
            #tabWidget QTabBar::tab:selected {
                background-color: #ffffff;
                color: #495057;
                border-bottom: 2px solid #667eea;
            }
            
            /* Panels */
            #videoPanel, #infoPanel {
                background-color: #ffffff;
                border-radius: 12px;
                border: 1px solid #e9ecef;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            }
            
            #panelTitle {
                font-size: 18px;
                font-weight: 600;
                color: #495057;
                margin-bottom: 15px;
                padding-bottom: 8px;
                border-bottom: 2px solid #667eea;
            }
            
            #videoLabel {
                background-color: #f8f9fa;
                border-radius: 8px;
                border: 2px dashed #dee2e6;
                color: #6c757d;
                font-size: 16px;
            }
            
            #infoValue {
                font-size: 16px;
                font-weight: 500;
                color: #495057;
                padding: 8px 12px;
                background-color: #f8f9fa;
                border-radius: 6px;
                border: 1px solid #e9ecef;
            }
            
            #statusValue {
                font-size: 16px;
                font-weight: 600;
                color: #28a745;
                padding: 8px 12px;
                background-color: #d4edda;
                border-radius: 6px;
                border: 1px solid #c3e6cb;
            }
            
            /* Buttons */
            #actionButton {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: black;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: 500;
                font-size: 14px;
                min-width: 120px;
            }
            
            #actionButton:hover {
                background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%);
                transform: translateY(-1px);
            }
            
            #actionButton:pressed {
                transform: translateY(0px);
            }
            
            #secondaryButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: 500;
                font-size: 14px;
                min-width: 120px;
            }
            
            #secondaryButton:hover {
                background-color: #5a6268;
            }
            
            /* Tab Button */
            #tabButton {
                background-color: #f8f9fa;
                color: #6c757d;
                padding: 8px 16px;
                border-radius: 6px 6px 0 0;
                font-weight: 500;
                font-size: 12px;
                border: 1px solid #e9ecef;
                border-bottom: none;
                min-width: 80px;
            }
            
            #tabButton:hover {
                background-color: #e9ecef;
                color: #495057;
            }
            
            #tabButton:pressed {
                background-color: #ffffff;
                color: #495057;
                border-bottom: 2px solid #667eea;
            }
            
            /* Report Buttons */
            #reportButton {
                background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
                color: black;
                border: 2px solid black;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: 500;
                font-size: 14px;
                min-width: 140px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
            }
            
            #reportButton:hover {
                background: linear-gradient(135deg, #218838 0%, #1ea085 100%);
                border-color: black;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.4);
            }
            
            #reportButton:pressed {
                background: linear-gradient(135deg, #1e7e34 0%, #1a7a6b 100%);
                border-color: black;
                box-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
            }
            
            /* Filter Frame */
            #filterFrame {
                background-color: #f8f9fa;
                border-radius: 8px;
                padding: 15px;
                border: 1px solid #e9ecef;
            }
            
            /* Form Controls */
            #dateEdit, #comboBox {
                padding: 8px 12px;
                border: 1px solid #ced4da;
                border-radius: 6px;
                background-color: white;
                font-size: 14px;
            }
            
            #dateEdit:focus, #comboBox:focus {
                border-color: #667eea;
                outline: none;
            }
            
            /* Table */
            #reportsTable {
                background-color: white;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                gridline-color: #e9ecef;
            }
            
            #reportsTable QHeaderView::section {
                background-color: #f8f9fa;
                padding: 12px;
                border: none;
                border-bottom: 2px solid #dee2e6;
                font-weight: 600;
                color: #495057;
            }
            
            #reportsTable QTableCornerButton::section {
                background-color: #f8f9fa;
                border: none;
                border-bottom: 2px solid #dee2e6;
                border-right: 2px solid #dee2e6;
            }
            
            /* Chart Label */
            #chartLabel {
                background-color: #f8f9fa;
                border: 2px dashed #dee2e6;
                border-radius: 8px;
                padding: 40px;
                color: #6c757d;
                font-size: 16px;
            }
            
            /* Status Bar */
            #statusBar {
                background: linear-gradient(135deg, #495057 0%, #6c757d 100%);
                color: white;
                font-size: 14px;
                font-weight: 500;
                padding: 12px 20px;
                border-top: 1px solid #e9ecef;
            }
        """
        self.setStyleSheet(style)

    def set_status_message(self, message, status='normal'):
        """Atualiza a mensagem e cor da barra de status."""
        self.status_bar.setText(message)
        
        if status == 'success':
            self.status_valor.setText("Sucesso")
            self.status_valor.setStyleSheet("""
                #statusValue {
                    background-color: #d4edda;
                    color: #155724;
                    border-color: #c3e6cb;
                }
            """)
        elif status == 'error':
            self.status_valor.setText("Erro")
            self.status_valor.setStyleSheet("""
                #statusValue {
                    background-color: #f8d7da;
                    color: #721c24;
                    border-color: #f5c6cb;
                }
            """)
        else: # normal
            self.status_valor.setText("Aguardando...")
            self.status_valor.setStyleSheet("""
                #statusValue {
                    background-color: #d1ecf1;
                    color: #0c5460;
                    border-color: #bee5eb;
                }
            """)

    def clear_student_info(self):
        """Limpa os dados do painel de informações."""
        self.nome_valor.setText("-")
        self.matricula_valor.setText("-")
        self.curso_valor.setText("-")
        self.set_status_message("Aguardando...", "normal")

    def atualizar_estatisticas(self):
        """Atualiza as estatísticas no header."""
        try:
            stats = obter_estatisticas_gerais()
            self.stats_alunos.setText(f"Alunos: {stats.get('total_alunos', 0)}")
            self.stats_hoje.setText(f"Hoje: {stats.get('registros_hoje', 0)}")
            self.stats_mes.setText(f"Mês: {stats.get('registros_mes', 0)}")
        except Exception as e:
            print(f"Erro ao atualizar estatísticas: {e}")

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
                    self.set_status_message("Foto capturada! Registrando entrada/saída...", "success")
                    self.capturando_foto = False
                    
                    # Registrar entrada/saída no banco
                    if self.aluno_atual:
                        tipo, timestamp = registrar_entrada_ou_saida(self.aluno_atual['id'], self.foto_aluno)
                        self.set_status_message(f"{tipo.title()} registrada com sucesso!", "success")
                        self.atualizar_estatisticas()
                    
                    QTimer.singleShot(3000, self.reset_and_clear)
            else:
                # Se não, continua tentando ler o código de barras
                barcodes = pyzbar.decode(frame)
                if barcodes:
                    for barcode in barcodes:
                        if not self.codigo_lido:
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
                                QTimer.singleShot(3000, self.reset_and_clear)
                            break

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

    def gerar_relatorio_rapido(self):
        """Gera um relatório rápido do dia atual."""
        try:
            resultados = relatorio_entradas_por_turno()
            if resultados:
                msg = "Relatório do Dia:\n\n"
                for turno, total_entradas, alunos_unicos in resultados:
                    msg += f"{turno}: {total_entradas} entradas ({alunos_unicos} alunos únicos)\n"
                
                QMessageBox.information(self, "Relatório Rápido", msg)
            else:
                QMessageBox.information(self, "Relatório Rápido", "Nenhum registro encontrado para hoje.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao gerar relatório: {e}")

    def gerar_relatorio_turno(self):
        """Gera relatório por turno."""
        try:
            data_selecionada = self.date_edit.date().toPyDate()
            data_inicio = datetime.combine(data_selecionada, datetime.min.time())
            data_fim = datetime.combine(data_selecionada, datetime.max.time())
            
            resultados = relatorio_entradas_por_turno(data_inicio, data_fim)
            
            self.reports_table.setRowCount(len(resultados))
            for i, (turno, total_entradas, alunos_unicos) in enumerate(resultados):
                self.reports_table.setItem(i, 0, QTableWidgetItem(data_selecionada.strftime("%d/%m/%Y")))
                self.reports_table.setItem(i, 1, QTableWidgetItem(turno))
                self.reports_table.setItem(i, 2, QTableWidgetItem(str(total_entradas)))
                self.reports_table.setItem(i, 3, QTableWidgetItem(str(alunos_unicos)))
            
            QMessageBox.information(self, "Sucesso", "Relatório por turno gerado com sucesso!")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao gerar relatório: {e}")

    def gerar_relatorio_semanal(self):
        """Gera relatório semanal."""
        try:
            resultados = relatorio_semanal()
            
            self.reports_table.setRowCount(len(resultados))
            for i, (data, total_entradas, alunos_unicos) in enumerate(resultados):
                data_obj = datetime.strptime(str(data), "%Y-%m-%d")
                self.reports_table.setItem(i, 0, QTableWidgetItem(data_obj.strftime("%d/%m/%Y")))
                self.reports_table.setItem(i, 1, QTableWidgetItem("Todos"))
                self.reports_table.setItem(i, 2, QTableWidgetItem(str(total_entradas)))
                self.reports_table.setItem(i, 3, QTableWidgetItem(str(alunos_unicos)))
            
            QMessageBox.information(self, "Sucesso", "Relatório semanal gerado com sucesso!")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao gerar relatório: {e}")

    def gerar_grafico_frequencia(self):
        """Gera gráfico de frequência."""
        try:
            if gerar_grafico_frequencia():
                self.chart_label.setText("Gráfico gerado com sucesso! Verifique o arquivo 'grafico_frequencia.png'")
                QMessageBox.information(self, "Sucesso", "Gráfico gerado com sucesso!")
            else:
                self.chart_label.setText("Nenhum dado encontrado para gerar o gráfico")
                QMessageBox.warning(self, "Aviso", "Nenhum dado encontrado para o período especificado")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao gerar gráfico: {e}")

    def closeEvent(self, event):
        """Libera a câmera ao fechar a janela."""
        self.cap.release()
        super().closeEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ModernMainWindow()
    window.show()
    window.atualizar_estatisticas()  # Carrega estatísticas iniciais
    sys.exit(app.exec_())