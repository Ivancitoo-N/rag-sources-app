@echo off
setlocal EnableDelayedExpansion
title RAG Sources App — Iniciando
color 0A

echo.
echo  =====================================================
echo    RAG Sources App  ^|  Local AI Document Q^&A
echo  =====================================================
echo.

set "ROOT=%~dp0"
set "BACKEND=%ROOT%backend"
set "FRONTEND=%ROOT%frontend"

:: HuggingFace Fixes for Windows (Prevents WinError 1314 symlink error)
set "HF_HUB_DISABLE_SYMLINKS=1"
set "HF_HUB_DISABLE_SYMLINKS_WARNING=1"

set "ERRORS=0"

:: ─── HELPER: print colored status ─────────────────────────────────────────
goto :main

:ok
echo   [OK]  %~1
goto :eof

:warn
echo   [??]  %~1
goto :eof

:fail
echo   [!!]  %~1
set ERRORS=1
goto :eof

:section
echo.
echo  -- %~1 --
goto :eof

:: ══════════════════════════════════════════════════════════════════════════
:main

:: ─── 1. PYTHON ────────────────────────────────────────────────────────────
call :section "Verificando Python"

python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    call :warn "Python NO encontrado en el PATH. Intentando buscar en rutas comunes..."
    if exist "C:\Python312\python.exe" ( set "PY=C:\Python312\python.exe" ) else ( 
        if exist "%LocalAppData%\Programs\Python\Python312\python.exe" ( set "PY=%LocalAppData%\Programs\Python\Python312\python.exe" ) else (
            call :fail "No se encontro Python 3.10+"
            echo  Descargando instalador de Python...
            curl -L -o "%TEMP%\python_installer.exe" "https://www.python.org/ftp/python/3.12.0/python-3.12.0-amd64.exe"
            if %ERRORLEVEL% EQU 0 (
                echo  Ejecutando instalador... Sigue los pasos y marca 'Add Python to PATH'.
                start /wait "" "%TEMP%\python_installer.exe"
                del "%TEMP%\python_installer.exe" >nul 2>&1
            )
            set ERRORS=1
        )
    )
) else (
    set "PY=python"
)

if "!PY!" NEQ "" (
    for /f "tokens=2" %%v in ('"!PY!" --version 2^>^&1') do set PY_VER=%%v
    call :ok "Python !PY_VER!"
)

:: ─── 2. NODE.JS ───────────────────────────────────────────────────────────
call :section "Verificando Node.js"

node --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    call :fail "Node.js NO encontrado"
    echo  Descargando Node.js...
    curl -L -o "%TEMP%\node_installer.msi" "https://nodejs.org/dist/v20.11.0/node-v20.11.0-x64.msi"
    if %ERRORLEVEL% EQU 0 (
        echo  Ejecutando instalador de Node.js...
        start /wait "" msiexec /i "%TEMP%\node_installer.msi"
        del "%TEMP%\node_installer.msi" >nul 2>&1
    )
    set ERRORS=1
) else (
    for /f %%v in ('node --version') do set NODE_VER=%%v
    call :ok "Node.js !NODE_VER!"
)

:: ─── 3. OLLAMA ────────────────────────────────────────────────────────────
call :section "Verificando Ollama"

ollama --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    call :fail "Ollama NO encontrado"
    echo  Descargando Ollama...
    curl -L -o "%TEMP%\OllamaSetup.exe" "https://ollama.com/download/OllamaSetup.exe"
    if %ERRORLEVEL% EQU 0 (
        echo  Instalando Ollama...
        start /wait "" "%TEMP%\OllamaSetup.exe"
        del "%TEMP%\OllamaSetup.exe" >nul 2>&1
    )
    set ERRORS=1
) else (
    call :ok "Ollama disponible"
    
    :: Iniciar si no corre
    curl -s http://localhost:11434/api/tags >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        call :warn "Ollama server no detectado. Iniciando..."
        start /b "" ollama serve
        timeout /t 5 /nobreak >nul
    )
    
    :: Verificar modelo
    echo   Verificando modelo llama3.2...
    ollama list | findstr "llama3.2" >nul
    if %ERRORLEVEL% NEQ 0 (
        call :warn "Descargando llama3.2 (puede tardar)..."
        ollama pull llama3.2:3b
    ) else (
        call :ok "Modelo llama3.2 listo"
    )
)

if %ERRORS% EQU 1 (
    echo.
    echo  [!!] Instala los componentes faltantes y reinicia este script.
    pause
    exit /b 1
)

:: ─── 4. BACKEND ───────────────────────────────────────────────────────────
call :section "Configurando Backend"

if not exist "%BACKEND%\.venv" (
    call :warn "Creando entorno virtual..."
    "!PY!" -m venv "%BACKEND%\.venv"
)

call :ok "Activando entorno virtual..."
set "VENV_PY=%BACKEND%\.venv\Scripts\python.exe"
set "VENV_PIP=%BACKEND%\.venv\Scripts\pip.exe"

echo   Verificando / Actualizando dependencias Python (esto puede tardar)...
"!VENV_PY!" -m pip install --upgrade pip
echo   Limpiando conflictos previos...
"!VENV_PIP!" uninstall typer typer-slim transformers huggingface-hub -y --quiet >nul 2>&1
"!VENV_PIP!" install -r "%BACKEND%\requirements.txt" --quiet
"!VENV_PIP!" install "transformers>=4.44.0,<5.0.0" "pymupdf" "python-docx" "huggingface-hub<1.0.0" "typer>=0.12.5,<0.13.0" "typer-slim>=0.12.5,<0.13.0" --upgrade --quiet
if %ERRORLEVEL% EQU 0 (
    call :ok "Dependencias Python al dia"
) else (
    call :fail "Error instalando dependencias Python"
)

if not exist "%BACKEND%\.env" (
    copy "%BACKEND%\.env.example" "%BACKEND%\.env" >nul
    call :warn ".env creado"
)

:: ─── 5. FRONTEND ──────────────────────────────────────────────────────────
call :section "Configurando Frontend"

if not exist "%FRONTEND%\node_modules" (
    call :warn "Instalando paquetes web (npm install)..."
    cd /d "%FRONTEND%" && call npm install --silent
    cd /d "%ROOT%"
)
call :ok "Paquetes web listos"

:: ─── 6. LANZAR ────────────────────────────────────────────────────────────
call :section "Lanzando Aplicacion"

echo   Iniciando Backend (http://127.0.0.1:8000)...
start "RAG-Backend" cmd /k "cd /d "%BACKEND%" && .venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload"

echo   Iniciando Frontend (http://localhost:5173)...
start "RAG-Frontend" cmd /k "cd /d "%FRONTEND%" && npm run dev"

timeout /t 6 /nobreak >nul
echo   Abriendo navegador...
start "" "http://localhost:5173"

echo.
echo  =====================================================
echo    Todo listo. La puerta (8000) ya deberia estar abierta.
echo    Si ves algun error de conexion al inicio, espera 5s
echo    y refresca la pagina con F5.
echo  =====================================================
echo.
pause
