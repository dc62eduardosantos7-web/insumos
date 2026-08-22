@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Criando ambiente virtual...
    py -m venv .venv
    if errorlevel 1 goto erro
)

echo Instalando dependencias...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto erro
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto erro

echo Preparando banco de dados...
".venv\Scripts\python.exe" manage.py migrate
if errorlevel 1 goto erro

echo.
echo Sistema disponivel em http://127.0.0.1:8000/
echo Para criar o administrador, feche o servidor e execute:
echo .venv\Scripts\python.exe manage.py createsuperuser
echo.
".venv\Scripts\python.exe" manage.py runserver
goto fim

:erro
echo.
echo Nao foi possivel concluir a instalacao.
pause

:fim
endlocal
