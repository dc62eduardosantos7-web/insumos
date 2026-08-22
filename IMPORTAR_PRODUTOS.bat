@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo O ambiente virtual ainda nao existe.
    echo Execute primeiro o arquivo INSTALAR_E_INICIAR.bat.
    pause
    goto fim
)

echo Esta operacao importara dados\Pasta1.xlsx.
echo Em descricoes repetidas, apenas o maior TOTAL sera mantido.
choice /M "Deseja continuar"
if errorlevel 2 goto fim

".venv\Scripts\python.exe" manage.py migrate
if errorlevel 1 goto erro
".venv\Scripts\python.exe" manage.py importar_produtos
if errorlevel 1 goto erro

echo.
echo Produtos importados com sucesso.
pause
goto fim

:erro
echo.
echo A importacao nao foi concluida.
pause

:fim
endlocal
