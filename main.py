import sys
import traceback
from PyQt5.QtWidgets import (QLabel, QVBoxLayout, QWidget, QApplication, QHBoxLayout, 
                             QFrame, QGridLayout, QPushButton, QTabWidget, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QMessageBox, QDateEdit, QComboBox,
                             QCheckBox, QGroupBox)
from PyQt5.QtGui import QPixmap, QColor, QPalette, QImage, QFont, QIcon
from PyQt5.QtCore import Qt, QTimer, QDate
import cv2
from pyzbar import pyzbar
from db_utils import (buscar_aluno_por_id, registrar_entrada_ou_saida, aluno_com_entrada_aberta,
                      relatorio_diario, relatorio_semanal, relatorio_entradas_por_turno,
                      dados_grafico_frequencia_tempo, obter_estatisticas_gerais, relatorio_por_periodo)
from face_overlay import detectar_rosto_e_overlay
import numpy as np
from datetime import datetime, timedelta
import mariadb
import io
from PIL import Image
# Importações para gráficos usando Tkinter
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk

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
        self.tempo_centralizado = 0

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
        main_tab = self.setup_main_tab()
        self.tab_widget.addTab(main_tab, "Controle")
        
        # Tab 2: Relatórios
        reports_tab = self.setup_reports_tab()
        self.tab_widget.addTab(reports_tab, "Relatórios")
        
        # Tab 3: Gráficos
        charts_tab = self.setup_charts_tab()
        self.tab_widget.addTab(charts_tab, "Gráficos")
        
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
        
        return main_tab

    def setup_reports_tab(self):
        """Configura a aba de relatórios."""
        reports_tab = QWidget()
        reports_layout = QVBoxLayout(reports_tab)

        # Filtros de data e turno
        filter_layout = QHBoxLayout()
        self.date_edit = QDateEdit(self)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setStyleSheet("QDateEdit { padding: 5px; border-radius: 5px; border: 1px solid #ccc; }")

        # Adicionar seletores de período
        self.date_inicio = QDateEdit(self)
        self.date_inicio.setDate(QDate.currentDate().addDays(-7))  # 7 dias atrás
        self.date_inicio.setCalendarPopup(True)
        self.date_inicio.setStyleSheet("QDateEdit { padding: 5px; border-radius: 5px; border: 1px solid #ccc; }")
        
        self.date_fim = QDateEdit(self)
        self.date_fim.setDate(QDate.currentDate())
        self.date_fim.setCalendarPopup(True)
        self.date_fim.setStyleSheet("QDateEdit { padding: 5px; border-radius: 5px; border: 1px solid #ccc; }")

        self.btn_relatorio_turno = QPushButton("Relatório por Turno", self)
        self.btn_relatorio_turno.setObjectName("reportButton")
        self.btn_relatorio_turno.clicked.connect(self.gerar_relatorio_turno)

        self.btn_relatorio_periodo = QPushButton("Relatório por Período", self)
        self.btn_relatorio_periodo.setObjectName("reportButton")
        self.btn_relatorio_periodo.clicked.connect(self.gerar_relatorio_periodo)
        
        self.btn_relatorio_diario = QPushButton("Relatório Diário", self)
        self.btn_relatorio_diario.setObjectName("reportButton")
        self.btn_relatorio_diario.clicked.connect(self.gerar_relatorio_diario)

        filter_layout.addWidget(QLabel("Data:"))
        filter_layout.addWidget(self.date_edit)
        filter_layout.addWidget(QLabel("Início:"))
        filter_layout.addWidget(self.date_inicio)
        filter_layout.addWidget(QLabel("Fim:"))
        filter_layout.addWidget(self.date_fim)
        filter_layout.addWidget(self.btn_relatorio_turno)
        filter_layout.addWidget(self.btn_relatorio_periodo)
        filter_layout.addWidget(self.btn_relatorio_diario)
        filter_layout.addStretch()

        reports_layout.addLayout(filter_layout)

        # Filtros de turno
        turno_group = QGroupBox("Filtros de Turno (para Relatórios Diário e por Período)")
        turno_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #28a745;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #28a745;
            }
        """)
        
        turno_layout = QHBoxLayout(turno_group)
        
        # Checkboxes para cada turno
        self.cb_cafe_manha = QCheckBox("Café da Manhã (09:30-09:50)")
        self.cb_almoco = QCheckBox("Almoço (11:00-12:50)")
        self.cb_cafe_tarde = QCheckBox("Café da Tarde (14:30-14:50)")
        self.cb_janta = QCheckBox("Janta (19:30-20:40)")
        
        # Marcar todos por padrão
        self.cb_cafe_manha.setChecked(True)
        self.cb_almoco.setChecked(True)
        self.cb_cafe_tarde.setChecked(True)
        self.cb_janta.setChecked(True)
        
        # Estilo para os checkboxes
        checkbox_style = """
            QCheckBox {
                font-size: 12px;
                color: #495057;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #adb5bd;
                border-radius: 3px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                border: 2px solid #28a745;
                border-radius: 3px;
                background-color: #28a745;
            }
        """
        
        self.cb_cafe_manha.setStyleSheet(checkbox_style)
        self.cb_almoco.setStyleSheet(checkbox_style)
        self.cb_cafe_tarde.setStyleSheet(checkbox_style)
        self.cb_janta.setStyleSheet(checkbox_style)
        
        turno_layout.addWidget(self.cb_cafe_manha)
        turno_layout.addWidget(self.cb_almoco)
        turno_layout.addWidget(self.cb_cafe_tarde)
        turno_layout.addWidget(self.cb_janta)
        turno_layout.addStretch()
        
        reports_layout.addWidget(turno_group)

        self.reports_table = QTableWidget(self)
        self.reports_table.setObjectName("reportsTable")
        self.reports_table.setColumnCount(4)
        self.reports_table.setHorizontalHeaderLabels(["Data", "Turno", "Hora", "Aluno"]) # Default headers
        self.reports_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.reports_table.setEditTriggers(QTableWidget.NoEditTriggers)
        reports_layout.addWidget(self.reports_table)

        return reports_tab

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
        controls_layout.setContentsMargins(15, 15, 15, 15)
        controls_layout.setSpacing(15)
        
        # Título dos controles
        controls_title = QLabel("Configurações do Gráfico", self)
        controls_title.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #495057;
                margin-bottom: 10px;
            }
        """)
        controls_layout.addWidget(controls_title)
        
        # Container para os controles
        controls_container = QHBoxLayout()
        
        # Label para o período
        periodo_label = QLabel("Período:", self)
        periodo_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: 500;
                color: #495057;
                margin-right: 10px;
            }
        """)
        controls_container.addWidget(periodo_label)
        
        # ComboBox para seleção do período
        self.periodo_combo = QComboBox(self)
        self.periodo_combo.addItems([
            "Últimas 24 horas",
            "Último dia",
            "Últimos 2 dias", 
            "Últimos 3 dias",
            "Últimos 5 dias",
            "Últimos 7 dias",
            "Últimos 15 dias",
            "Últimos 30 dias",
            "Últimos 60 dias",
            "Últimos 90 dias",
            "Últimos 120 dias"
        ])
        self.periodo_combo.setCurrentText("Últimas 24 horas")
        self.periodo_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 1px solid #ced4da;
                border-radius: 6px;
                background-color: white;
                font-size: 14px;
                min-width: 150px;
            }
            QComboBox:focus {
                border-color: #667eea;
                outline: none;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #495057;
                margin-right: 5px;
            }
        """)
        controls_container.addWidget(self.periodo_combo)
        
        # Espaçamento
        controls_container.addSpacing(20)
        
        # Botão para gerar gráfico
        self.btn_gerar_grafico = QPushButton("Gerar Gráfico de Frequência", self)
        self.btn_gerar_grafico.setObjectName("actionButton")
        self.btn_gerar_grafico.clicked.connect(self.gerar_grafico_frequencia)
        controls_container.addWidget(self.btn_gerar_grafico)
        
        # Adicionar stretch para empurrar tudo para a esquerda
        controls_container.addStretch()
        
        controls_layout.addLayout(controls_container)
        
        layout.addWidget(chart_controls)

        # Área para exibir gráfico - agora usando um layout para o canvas do matplotlib
        self.chart_layout = QVBoxLayout()
        
        # Label inicial
        self.chart_label = QLabel("Clique em 'Gerar Gráfico' para visualizar a frequência de entradas", self)
        self.chart_label.setObjectName("chartLabel")
        self.chart_label.setAlignment(Qt.AlignCenter)
        self.chart_layout.addWidget(self.chart_label)
        
        layout.addLayout(self.chart_layout)
        
        return charts_tab

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
            # Fallback para valores padrão
            self.stats_alunos.setText("Alunos: 0")
            self.stats_hoje.setText("Hoje: 0")
            self.stats_mes.setText("Mês: 0")

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
                
                # Adicionar contador de tempo para centralização
                if not hasattr(self, 'tempo_centralizado'):
                    self.tempo_centralizado = 0
                
                if centralizado:
                    self.tempo_centralizado += 1
                    # Aguardar 1 segundo (30 frames a 30 FPS) para confirmar centralização
                    if self.tempo_centralizado >= 30:
                        x, y, w, h = bbox
                        self.foto_aluno = frame[y:y+h, x:x+w]
                        self.set_status_message("🎉 FOTO CAPTURADA! Registrando entrada...", "success")
                        self.capturando_foto = False
                        self.tempo_centralizado = 0
                        
                        # Mostrar a foto capturada
                        self.mostrar_foto_capturada()
                        
                        # Registrar entrada no banco
                        if self.aluno_atual:
                            tipo, timestamp = registrar_entrada_ou_saida(self.aluno_atual['id'], self.foto_aluno)
                            self.set_status_message(f"{tipo.title()} registrada com sucesso!", "success")
                            self.atualizar_estatisticas()
                        
                        QTimer.singleShot(3000, self.reset_and_clear)
                else:
                    self.tempo_centralizado = 0
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
                                
                                # Verificar se é entrada ou saída
                                registro_aberto = aluno_com_entrada_aberta(aluno['id'])
                                if registro_aberto:
                                    # É uma saída - registrar diretamente sem foto
                                    tipo, timestamp = registrar_entrada_ou_saida(aluno['id'], None)
                                    self.set_status_message(f"Saída registrada com sucesso!", "success")
                                    self.atualizar_estatisticas()
                                    QTimer.singleShot(3000, self.reset_and_clear)
                                else:
                                    # É uma entrada - capturar foto
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

    def mostrar_foto_capturada(self):
        """Exibe a foto capturada em uma janela popup."""
        if self.foto_aluno is not None:
            # Converter a foto para RGB
            foto_rgb = cv2.cvtColor(self.foto_aluno, cv2.COLOR_BGR2RGB)
            h, w, ch = foto_rgb.shape
            bytes_per_line = ch * w
            qt_image = QImage(foto_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_image)
            
            # Criar uma janela popup para mostrar a foto
            popup = QWidget()
            popup.setWindowTitle("Foto Capturada")
            popup.setGeometry(200, 200, 400, 500)
            popup.setStyleSheet("""
                QWidget {
                    background-color: #f8f9fa;
                    font-family: 'Segoe UI', Arial, sans-serif;
                }
            """)
            
            layout = QVBoxLayout(popup)
            
            # Título
            titulo = QLabel("FOTO CAPTURADA COM SUCESSO!")
            titulo.setStyleSheet("""
                QLabel {
                    color: #28a745;
                    font-size: 18px;
                    font-weight: bold;
                    padding: 10px;
                    background-color: #d4edda;
                    border-radius: 8px;
                    margin: 10px;
                }
            """)
            titulo.setAlignment(Qt.AlignCenter)
            layout.addWidget(titulo)
            
            # Imagem da foto
            foto_label = QLabel()
            foto_label.setPixmap(pixmap.scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            foto_label.setAlignment(Qt.AlignCenter)
            foto_label.setStyleSheet("""
                QLabel {
                    border: 2px solid #28a745;
                    border-radius: 8px;
                    padding: 10px;
                    background-color: white;
                }
            """)
            layout.addWidget(foto_label)
            
            # Informações do aluno
            if self.aluno_atual:
                info_text = f"Aluno: {self.aluno_atual.get('nome', 'N/A')}\nMatrícula: {self.aluno_atual.get('matricula', 'N/A')}"
                info_label = QLabel(info_text)
                info_label.setStyleSheet("""
                    QLabel {
                        color: #495057;
                        font-size: 14px;
                        padding: 10px;
                        background-color: white;
                        border-radius: 8px;
                        margin: 10px;
                    }
                """)
                info_label.setAlignment(Qt.AlignCenter)
                layout.addWidget(info_label)
            
            # Botão de fechar
            btn_fechar = QPushButton("OK")
            btn_fechar.setStyleSheet("""
                QPushButton {
                    background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 8px;
                    font-weight: 500;
                    font-size: 14px;
                    min-width: 100px;
                }
                QPushButton:hover {
                    background: linear-gradient(135deg, #218838 0%, #1ea085 100%);
                }
            """)
            btn_fechar.clicked.connect(popup.close)
            layout.addWidget(btn_fechar, alignment=Qt.AlignCenter)
            
            # Mostrar a janela
            popup.show()
            
            # Fechar automaticamente após 2 segundos
            QTimer.singleShot(2000, popup.close)

    def gerar_relatorio_rapido(self):
        """Gera um relatório rápido do dia atual."""
        try:
            data_hoje = datetime.date.today()
            
            # Obter turnos selecionados
            turnos_selecionados = []
            if self.cb_cafe_manha.isChecked():
                turnos_selecionados.append('Café da Manhã')
            if self.cb_almoco.isChecked():
                turnos_selecionados.append('Almoço')
            if self.cb_cafe_tarde.isChecked():
                turnos_selecionados.append('Café da Tarde')
            if self.cb_janta.isChecked():
                turnos_selecionados.append('Janta')
            
            # Se nenhum turno selecionado, usar todos
            if not turnos_selecionados:
                turnos_selecionados = ['Café da Manhã', 'Almoço', 'Café da Tarde', 'Janta']
            
            registros = relatorio_diario(data_hoje, turnos_filtro=turnos_selecionados)
            
            if not registros:
                QMessageBox.information(self, "Relatório Diário", "Nenhum registro encontrado para hoje.")
                return
            
            msg = f"Relatório Diário - {data_hoje.strftime('%d/%m/%Y')}\n\n"
            msg += f"Turnos incluídos: {', '.join(turnos_selecionados)}\n"
            msg += f"Total de entradas: {len(registros)}\n\n"
            
            turnos = {}
            for registro in registros:
                turno = registro.get('turno', 'Outros')
                if turno not in turnos:
                    turnos[turno] = []
                turnos[turno].append(registro)
            
            for turno, lista_registros in turnos.items():
                msg += f"{turno}: {len(lista_registros)} entradas\n"
            
            QMessageBox.information(self, "Relatório Diário", msg)
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao gerar relatório: {e}")

    def gerar_relatorio_turno(self):
        """Gera relatório por turno."""
        try:
            data_selecionada = self.date_edit.date().toPyDate()
            registros = relatorio_entradas_por_turno(data_selecionada)
            
            if not registros:
                QMessageBox.information(self, "Relatório por Turno", "Nenhum registro encontrado para a data selecionada.")
                return
            
            # Atualizar cabeçalhos da tabela
            self.reports_table.setHorizontalHeaderLabels(["Data", "Turno", "Total Entradas", "Alunos Únicos"])
            
            # Limpar tabela
            self.reports_table.setRowCount(0)
            
            # Preencher tabela
            for i, registro in enumerate(registros):
                self.reports_table.insertRow(i)
                self.reports_table.setItem(i, 0, QTableWidgetItem(data_selecionada.strftime('%d/%m/%Y')))
                self.reports_table.setItem(i, 1, QTableWidgetItem(str(registro[0])))  # Turno
                self.reports_table.setItem(i, 2, QTableWidgetItem(str(registro[1])))  # Total Entradas
                self.reports_table.setItem(i, 3, QTableWidgetItem(str(registro[2])))  # Alunos Únicos
            
            QMessageBox.information(self, "Relatório por Turno", f"Relatório gerado com sucesso!\nEncontrados {len(registros)} turnos.")
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao gerar relatório: {e}")

    def gerar_relatorio_periodo(self):
        """Gera relatório por período."""
        try:
            data_inicio = self.date_inicio.date().toPyDate()
            data_fim = self.date_fim.date().toPyDate()
            
            # Obter turnos selecionados
            turnos_selecionados = []
            if self.cb_cafe_manha.isChecked():
                turnos_selecionados.append('Café da Manhã')
            if self.cb_almoco.isChecked():
                turnos_selecionados.append('Almoço')
            if self.cb_cafe_tarde.isChecked():
                turnos_selecionados.append('Café da Tarde')
            if self.cb_janta.isChecked():
                turnos_selecionados.append('Janta')
            
            # Se nenhum turno selecionado, usar todos
            if not turnos_selecionados:
                turnos_selecionados = ['Café da Manhã', 'Almoço', 'Café da Tarde', 'Janta']
            
            registros = relatorio_por_periodo(data_inicio, data_fim, turnos_filtro=turnos_selecionados)
            
            if not registros:
                QMessageBox.information(self, "Relatório por Período", "Nenhum registro encontrado para o período selecionado.")
                return
            
            # Atualizar cabeçalhos da tabela
            self.reports_table.setHorizontalHeaderLabels(["Data", "Total Entradas", "Alunos Únicos"])
            
            self.reports_table.setRowCount(0)
            
            for i, registro in enumerate(registros):
                self.reports_table.insertRow(i)
                data = registro[0]
                
                # Tratar diferentes tipos de data que podem vir do banco
                try:
                    if hasattr(data, 'strftime'):  # Se é um objeto datetime.date ou datetime.datetime
                        data_str = data.strftime('%d/%m/%Y')
                    elif isinstance(data, str):  # Se é uma string
                        # Tentar converter string para data e formatar
                        try:
                            from datetime import datetime
                            data_obj = datetime.strptime(data, '%Y-%m-%d').date()
                            data_str = data_obj.strftime('%d/%m/%Y')
                        except:
                            data_str = str(data)
                    else:
                        data_str = str(data)
                except:
                    data_str = str(data)
                
                self.reports_table.setItem(i, 0, QTableWidgetItem(data_str))
                self.reports_table.setItem(i, 1, QTableWidgetItem(str(registro[1])))
                self.reports_table.setItem(i, 2, QTableWidgetItem(str(registro[2])))
            
            turnos_str = ", ".join(turnos_selecionados)
            QMessageBox.information(self, "Relatório por Período", f"Relatório gerado com sucesso!\nPeríodo: {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}\nTurnos: {turnos_str}\nEncontrados {len(registros)} dias.")
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao gerar relatório: {e}")

    def gerar_relatorio_diario(self):
        """Gera relatório diário detalhado."""
        try:
            data_selecionada = self.date_edit.date().toPyDate()
            
            # Obter turnos selecionados
            turnos_selecionados = []
            if self.cb_cafe_manha.isChecked():
                turnos_selecionados.append('Café da Manhã')
            if self.cb_almoco.isChecked():
                turnos_selecionados.append('Almoço')
            if self.cb_cafe_tarde.isChecked():
                turnos_selecionados.append('Café da Tarde')
            if self.cb_janta.isChecked():
                turnos_selecionados.append('Janta')
            
            # Se nenhum turno selecionado, usar todos
            if not turnos_selecionados:
                turnos_selecionados = ['Café da Manhã', 'Almoço', 'Café da Tarde', 'Janta']
            
            registros = relatorio_diario(data_selecionada, turnos_filtro=turnos_selecionados)
            
            if not registros:
                QMessageBox.information(self, "Relatório Diário", "Nenhum registro encontrado para a data selecionada.")
                return
            
            # Atualizar cabeçalhos da tabela
            self.reports_table.setHorizontalHeaderLabels(["Data", "Turno", "Hora", "Aluno"])
            
            self.reports_table.setRowCount(0)
            
            for i, registro in enumerate(registros):
                self.reports_table.insertRow(i)
                
                hora_entrada = registro.get('hora_entrada')
                if hora_entrada:
                    # Tratar diferentes tipos de datetime que podem vir do banco
                    try:
                        if hasattr(hora_entrada, 'strftime'):  # Se é um objeto datetime
                            hora_str = hora_entrada.strftime('%H:%M')
                        elif isinstance(hora_entrada, str):  # Se é uma string
                            # Tentar extrair hora de string
                            hora_str = str(hora_entrada)[:5]
                        else:
                            hora_str = str(hora_entrada)[:5]
                    except:
                        hora_str = str(hora_entrada)[:5]
                else:
                    hora_str = "N/A"
                
                self.reports_table.setItem(i, 0, QTableWidgetItem(data_selecionada.strftime('%d/%m/%Y')))
                self.reports_table.setItem(i, 1, QTableWidgetItem(registro.get('turno', 'N/A')))
                self.reports_table.setItem(i, 2, QTableWidgetItem(hora_str))
                self.reports_table.setItem(i, 3, QTableWidgetItem(registro.get('nome', 'N/A')))
            
            turnos_str = ", ".join(turnos_selecionados)
            QMessageBox.information(self, "Relatório Diário", f"Relatório gerado com sucesso!\nTurnos: {turnos_str}\nEncontrados {len(registros)} registros.")
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao gerar relatório: {e}")

    def gerar_grafico_frequencia(self):
        """Gera gráfico de frequência visual em janela separada."""
        try:
            print("=== DEBUG: Iniciando geração de gráfico visual ===")
            
            # Obter período selecionado
            periodo_selecionado = self.periodo_combo.currentText()
            print(f"DEBUG: Período selecionado: {periodo_selecionado}")
            
            # Calcular data início baseada no período selecionado
            data_fim = datetime.now()
            
            if periodo_selecionado == "Últimas 24 horas":
                data_inicio = data_fim - timedelta(hours=24)
                titulo_periodo = "Últimas 24 horas"
            elif periodo_selecionado == "Último dia":
                data_inicio = data_fim - timedelta(days=1)
                titulo_periodo = "Último dia"
            elif periodo_selecionado == "Últimos 2 dias":
                data_inicio = data_fim - timedelta(days=2)
                titulo_periodo = "Últimos 2 dias"
            elif periodo_selecionado == "Últimos 3 dias":
                data_inicio = data_fim - timedelta(days=3)
                titulo_periodo = "Últimos 3 dias"
            elif periodo_selecionado == "Últimos 5 dias":
                data_inicio = data_fim - timedelta(days=5)
                titulo_periodo = "Últimos 5 dias"
            elif periodo_selecionado == "Últimos 7 dias":
                data_inicio = data_fim - timedelta(days=7)
                titulo_periodo = "Últimos 7 dias"
            elif periodo_selecionado == "Últimos 15 dias":
                data_inicio = data_fim - timedelta(days=15)
                titulo_periodo = "Últimos 15 dias"
            elif periodo_selecionado == "Últimos 30 dias":
                data_inicio = data_fim - timedelta(days=30)
                titulo_periodo = "Últimos 30 dias"
            elif periodo_selecionado == "Últimos 60 dias":
                data_inicio = data_fim - timedelta(days=60)
                titulo_periodo = "Últimos 60 dias"
            elif periodo_selecionado == "Últimos 90 dias":
                data_inicio = data_fim - timedelta(days=90)
                titulo_periodo = "Últimos 90 dias"
            elif periodo_selecionado == "Últimos 120 dias":
                data_inicio = data_fim - timedelta(days=120)
                titulo_periodo = "Últimos 120 dias"
            else:
                # Fallback para 24 horas
                data_inicio = data_fim - timedelta(hours=24)
                titulo_periodo = "Últimas 24 horas"
            
            print(f"DEBUG: Data início: {data_inicio}")
            print(f"DEBUG: Data fim: {data_fim}")
            
            dados = dados_grafico_frequencia_tempo(data_inicio, data_fim)
            
            print(f"DEBUG: Dados retornados: {dados}")
            print(f"DEBUG: Tipo dos dados: {type(dados)}")
            print(f"DEBUG: Quantidade de dados: {len(dados) if dados else 0}")
            
            if not dados:
                print("DEBUG: Nenhum dado encontrado")
                QMessageBox.information(self, "Gráfico de Frequência", f"Nenhum dado encontrado para o período: {titulo_periodo}")
                return
            
            # Preparar dados para o gráfico
            intervalos = []
            totais = []
            
            for intervalo, total in dados:
                try:
                    # Converter string de intervalo para datetime
                    if isinstance(intervalo, str):
                        dt = datetime.strptime(intervalo, '%Y-%m-%d %H:%M:%S')
                    else:
                        dt = intervalo
                    
                    intervalos.append(dt)
                    totais.append(total)
                except Exception as e:
                    print(f"DEBUG: Erro ao processar intervalo '{intervalo}': {e}")
                    continue
            
            if not intervalos:
                QMessageBox.warning(self, "Gráfico de Frequência", "Nenhum dado válido encontrado para gerar o gráfico.")
                return
            
            # Criar janela Tkinter para o gráfico
            root = tk.Tk()
            root.title(f"Gráfico de Frequência - {titulo_periodo}")
            root.geometry("800x600")
            
            # Criar figura do matplotlib
            fig = Figure(figsize=(10, 6))
            ax = fig.add_subplot(111)
            
            # Criar gráfico de barras
            bars = ax.bar(range(len(intervalos)), totais, color='#28a745', alpha=0.7, edgecolor='#1e7e34')
            
            # Configurar eixos
            ax.set_xlabel('Período', fontsize=12, fontweight='bold')
            ax.set_ylabel('Número de Entradas', fontsize=12, fontweight='bold')
            ax.set_title(f'Frequência de Entradas - {titulo_periodo}', fontsize=14, fontweight='bold', color='#28a745')
            
            # Configurar rótulos do eixo X
            if len(intervalos) <= 24:  # Para períodos curtos, mostrar todas as horas
                x_labels = [dt.strftime('%H:%M') if '24 horas' in titulo_periodo else dt.strftime('%d/%m %H:%M') for dt in intervalos]
            else:  # Para períodos longos, mostrar apenas algumas datas
                x_labels = []
                for i, dt in enumerate(intervalos):
                    if i % max(1, len(intervalos) // 10) == 0:  # Mostrar ~10 rótulos
                        x_labels.append(dt.strftime('%d/%m'))
                    else:
                        x_labels.append('')
            
            ax.set_xticks(range(len(intervalos)))
            ax.set_xticklabels(x_labels, rotation=45, ha='right')
            
            # Adicionar valores nas barras
            for bar, total in zip(bars, totais):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                       f'{total}', ha='center', va='bottom', fontweight='bold')
            
            # Configurar grade
            ax.grid(True, alpha=0.3, linestyle='--')
            ax.set_axisbelow(True)
            
            # Ajustar layout
            fig.tight_layout()
            
            # Criar canvas do matplotlib
            canvas = FigureCanvasTkAgg(fig, master=root)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            print("DEBUG: Gráfico visual gerado com sucesso")
            QMessageBox.information(self, "Gráfico de Frequência", f"Gráfico visual gerado com sucesso para {titulo_periodo}!")
            
            # Executar a janela Tkinter
            root.mainloop()
            
        except Exception as e:
            print(f"DEBUG: Erro na geração do gráfico visual: {e}")
            print(f"DEBUG: Traceback completo:")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Erro", f"Erro ao gerar gráfico visual: {e}")

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