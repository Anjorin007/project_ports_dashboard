# ============================================================================
# SCRIPT DE LANCEMENT COMPLET - West Africa Ports Dashboard
# PowerShell Script (Windows)
# 
# Utilisation:
#   powershell -ExecutionPolicy Bypass -File launch.ps1
# ============================================================================

param(
    [switch]$StopOnly = $false,
    [switch]$StatusOnly = $false
)

# ============================================================================
# CONFIGURATION
# ============================================================================

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$DockerComposePath = Join-Path $ProjectRoot "docker-compose.yml"
$CreateMartsPath = Join-Path $ProjectRoot "create_marts.sql"
$VenvPath = Join-Path $ProjectRoot "venv"

# Couleurs pour output
function Write-Status { Write-Host "✓ $args" -ForegroundColor Green }
function Write-Error { Write-Host "❌ $args" -ForegroundColor Red }
function Write-Warning { Write-Host "⚠ $args" -ForegroundColor Yellow }
function Write-Info { Write-Host "ℹ $args" -ForegroundColor Cyan }

# ============================================================================
# FONCTION: Arrêter tout
# ============================================================================

function Stop-Application {
    Write-Info "Arrêt des services..."
    
    Write-Info "  → Arrêt Streamlit..."
    
    Write-Info "  → Arrêt Docker..."
    docker-compose stop
    
    Write-Status "Services arrêtés"
}

# ============================================================================
# FONCTION: Vérifier status
# ============================================================================

function Get-Status {
    Write-Info "État actuel:"
    
    # Docker
    $dockerRunning = docker ps 2>$null | Select-String "ports_postgres_db"
    if ($dockerRunning) {
        Write-Status "  Docker: EN COURS"
    } else {
        Write-Warning "  Docker: ARRÊTÉ"
    }
    
    # PostgreSQL
    try {
        $dbTest = docker exec ports_postgres_db psql -U postgres -d ports_dashboard -c "SELECT 1" 2>$null
        Write-Status "  PostgreSQL: CONNECTÉ"
    } catch {
        Write-Warning "  PostgreSQL: DÉCONNECTÉ"
    }
    
    # Tables
    try {
        $tablesTest = docker exec ports_postgres_db psql -U postgres -d ports_dashboard -c "SELECT COUNT(*) FROM marts.mart_port_annual_summary" 2>$null
        Write-Status "  Tables Marts: EXISTANTES"
    } catch {
        Write-Warning "  Tables Marts: MANQUANTES"
    }
}

# ============================================================================
# FONCTION: STARTUP COMPLET
# ============================================================================

function Start-Application {
    cls
    Write-Host ""
    Write-Host "===================================================================" -ForegroundColor Cyan
    Write-Host "  🚀 West Africa Ports Dashboard - Startup Script" -ForegroundColor Cyan
    Write-Host "===================================================================" -ForegroundColor Cyan
    Write-Host ""
    
    # ========================================================================
    # 1. VÉRIFIER DOCKER
    # ========================================================================
    
    Write-Info "[1/6] Vérification Docker..."
    try {
        $dockerVersion = docker --version
        Write-Status "Docker trouvé: $dockerVersion"
    } catch {
        Write-Error "Docker n'est pas installé ou n'est pas dans PATH"
        Write-Info "Télécharge: https://www.docker.com/products/docker-desktop"
        pause
        exit 1
    }
    
    # ========================================================================
    # 2. DÉMARRER DOCKER
    # ========================================================================
    
    Write-Info "[2/6] Démarrage PostgreSQL..."
    
    $isRunning = docker ps 2>$null | Select-String "ports_postgres_db"
    
    if ($isRunning) {
        Write-Status "Conteneur déjà en cours"
    } else {
        Write-Info "  → Démarrage du conteneur..."
        docker-compose up -d
        
        # Attends que PostgreSQL soit ready
        Write-Info "  ⏳ Attente PostgreSQL (20s)..."
        Start-Sleep -Seconds 20
    }
    
    # ========================================================================
    # 3. TESTER CONNEXION
    # ========================================================================
    
    Write-Info "[3/6] Test de connexion PostgreSQL..."
    try {
        docker exec ports_postgres_db psql -U postgres -d ports_dashboard -c "SELECT COUNT(*) FROM fact_port_traffic;" >$null 2>&1
        Write-Status "PostgreSQL connecté ✓"
    } catch {
        Write-Error "Erreur de connexion PostgreSQL"
        pause
        exit 1
    }
    
    # ========================================================================
    # 4. CRÉER TABLES MARTS SI MANQUANTES
    # ========================================================================
    
    Write-Info "[4/6] Vérification des tables analytiques..."
    
    try {
        docker exec ports_postgres_db psql -U postgres -d ports_dashboard -c "SELECT 1 FROM marts.mart_port_annual_summary LIMIT 1;" >$null 2>&1
        Write-Status "Tables marts existantes"
    } catch {
        Write-Warning "Tables marts manquantes, création..."
        
        if (Test-Path $CreateMartsPath) {
            Get-Content $CreateMartsPath | docker exec -i ports_postgres_db psql -U postgres -d ports_dashboard
            Write-Status "Tables marts créées"
        } else {
            Write-Error "Fichier create_marts.sql introuvable"
        }
    }
    
    # ========================================================================
    # 5. ACTIVER VENV
    # ========================================================================
    
    Write-Info "[5/6] Activation environnement Python..."
    
    if (Test-Path (Join-Path $VenvPath "Scripts\Activate.ps1")) {
        & (Join-Path $VenvPath "Scripts\Activate.ps1")
        Write-Status "Venv activé"
    } else {
        Write-Error "Venv non trouvé"
        pause
        exit 1
    }
    
    # ========================================================================
    # 6. LANCER STREAMLIT
    # ========================================================================
    
    Write-Info "[6/6] Démarrage Streamlit..."
    Write-Host ""
    Write-Host "===================================================================" -ForegroundColor Green
    Write-Host "  ✓ Application prête !" -ForegroundColor Green
    Write-Host "  🌐 Accès: http://localhost:8501" -ForegroundColor Green
    Write-Host "" -ForegroundColor Green
    Write-Host "  Appuie sur Ctrl+C pour arrêter" -ForegroundColor Yellow
    Write-Host "===================================================================" -ForegroundColor Green
    Write-Host ""
    
    # Nettoie cache
    streamlit cache clear
    
    # Lance app
    streamlit run app.py
}

# ============================================================================
# MAIN
# ============================================================================

if ($StopOnly) {
    Stop-Application
} elseif ($StatusOnly) {
    Get-Status
} else {
    Start-Application
}

Write-Info "Au revoir!"