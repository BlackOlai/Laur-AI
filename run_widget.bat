@echo off
echo ========================================
echo Iniciando Laura HUD - Widget de Desktop
echo ========================================
echo.
echo Verificando dependencias...
pip install pywebview pywinstyles --quiet
echo.

python widget_launcher.py
pause
