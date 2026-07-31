@echo off
chcp 65001 >nul
title AWF KIEROWCY
where python >nul 2>&1
if errorlevel 1 (
    echo Nie znaleziono Pythona. Pobierz z python.org
    echo WAZNE: przy instalacji zaznacz "Add python.exe to PATH"
    pause & exit /b 1
)
python -c "import PIL" >nul 2>&1
if errorlevel 1 (
    echo Instaluje biblioteke Pillow ^(jednorazowo^)...
    python -m pip install --quiet pillow
)
python awf_kierowcy.py
if errorlevel 1 pause
