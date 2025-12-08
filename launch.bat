@echo off
REM ============================================================================
REM SCRIPT DE LANCEMENT COMPLET - West Africa Ports Dashboard
REM Windows Batch Script
REM ============================================================================

setlocal enabledelayedexpansion

echo.
echo ====================================================================
echo   🚀 West Africa Ports Dashboard - Startup Script
echo ====================================================================
echo.

REM ============================================================================
REM 1. DÉMARRER DOCKER
REM ============================================================================

echo [1/5] Vérification Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker n'est pas installé ou n'est pas dans PATH
    echo    Installe Docker Desktop: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)
echo ✓ Docker trouvé

echo [2/5] Démarrage PostgreSQL (Docker)...
docker-compose ps | find "ports_postgres_db" >nul
if errorlevel 1 (
    echo   → Conteneur non trouvé, création...
    docker-compose up -d
) else (
    echo   → Conteneur existe, vérification status...
    docker-compose start
)

REM Attends que PostgreSQL soit ready (15 secondes)
echo   ⏳ Attente PostgreSQL (15s)...
timeout /t 15 /nobreak

REM ============================================================================
REM 2. VÉRIFIER CONNEXION BASE DE DONNÉES
REM ============================================================================

echo.
echo [3/5] Test de connexion PostgreSQL...
docker exec ports_postgres_db psql -U postgres -d ports_dashboard -c "SELECT COUNT(*) FROM fact_port_traffic;" >nul 2>&1
if errorlevel 1 (
    echo ❌ Erreur de connexion PostgreSQL
    pause
    exit /b 1
)
echo ✓ PostgreSQL connecté

REM ============================================================================
REM 3. VÉRIFIER TABLES MARTS
REM ============================================================================

echo.
echo [4/5] Vérification des tables analytiques...
docker exec ports_postgres_db psql -U postgres -d ports_dashboard -c "SELECT COUNT(*) FROM marts.mart_port_annual_summary;" >nul 2>&1
if errorlevel 1 (
    echo   ⚠ Tables marts manquantes, création...
    Get-Content create_marts.sql | docker exec -i ports_postgres_db psql -U postgres -d ports_dashboard
    echo ✓ Tables marts créées
) else (
    echo ✓ Tables marts existantes
)

REM ============================================================================
REM 4. LANCER VENV & STREAMLIT
REM ============================================================================

echo.
echo [5/5] Démarrage application Streamlit...
echo.

REM Active venv
call venv\Scripts\activate.bat

REM Nettoie cache Streamlit
streamlit cache clear

REM Lance l'app
echo.
echo ====================================================================
echo   ✓ Application démarrée !
echo   🌐 Accès: http://localhost:8501
echo.
echo   Appuie sur Ctrl+C pour arrêter
echo ====================================================================
echo.

streamlit run app.py

REM ============================================================================
REM 5. CLEANUP (optionnel)
REM ============================================================================

REM Désactive venv
deactivate

echo.
echo Application fermée
pause