@echo off
echo ========================================
echo Instalando dependencias do Sistema de Controle de Refeitorio
echo ========================================

echo.
echo Atualizando pip...
python -m pip install --upgrade pip

echo.
echo Instalando dependencias principais...
pip install opencv-python==4.8.1.78
pip install PyQt5==5.15.9
pip install pyzbar==0.1.9
pip install Pillow==10.0.1
pip install mariadb==1.1.8
pip install numpy==1.24.3

echo.
echo Instalando dependencias para relatorios e graficos...
pip install pandas==2.0.3
pip install matplotlib==3.7.2

echo.
echo ========================================
echo Instalacao concluida!
echo ========================================
echo.
echo Para testar o sistema, execute:
echo python test_system.py
echo.
echo Para adicionar dados de teste:
echo python add_test_data.py
echo.
echo Para executar o sistema:
echo python main.py
echo.
pause 