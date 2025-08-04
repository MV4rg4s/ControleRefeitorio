@echo off
echo ========================================
echo Instalando dependencias do Sistema de Controle de Refeitorio
echo ========================================

echo.
echo Atualizando pip...
python -m pip install --upgrade pip

echo.
echo Instalando dependencias principais...
pip install opencv-python==4.12.0.88
pip install PyQt5==5.15.9
pip install pyzbar==0.1.9
pip install Pillow==11.3.0
pip install mariadb==1.1.13
pip install numpy==2.2.6

echo.
echo Instalando dependencias para relatorios e graficos...
pip install pandas==2.3.1
pip install matplotlib==3.10.5

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