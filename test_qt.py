import sys
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout

app = QApplication(sys.argv)
window = QWidget()
window.setWindowTitle('Teste PyQt5')
layout = QVBoxLayout()
label = QLabel('Se você está vendo esta janela, PyQt5 está funcionando!')
layout.addWidget(label)
window.setLayout(layout)
window.show()
sys.exit(app.exec_()) 