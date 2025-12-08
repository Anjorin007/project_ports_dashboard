# 🚀 Scripts de Lancement - Guide Complet

## Objectif

Un seul script pour :
1. ✅ Démarrer Docker PostgreSQL
2. ✅ Vérifier les connexions
3. ✅ Créer les tables si manquantes
4. ✅ Lancer Streamlit automatiquement

---

## Installation

### Étape 1 : Crée les scripts

À la **racine du projet**, crée **deux fichiers** :

#### Option A : Batch (classique Windows)

**Fichier** : `launch.bat`
- Copie le contenu de **Artifact 1** (script batch)

#### Option B : PowerShell (moderne)

**Fichier** : `launch.ps1`
- Copie le contenu de **Artifact 2** (script PowerShell)

---

## Utilisation

### Option A : Batch (`.bat`)

```bash
# Lancer l'application
launch.bat

# Ou directement en cliquant sur le fichier dans l'Explorateur
```

### Option B : PowerShell (`.ps1`)

```powershell
# Première fois: autoriser l'exécution
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope CurrentUser

# Lancer l'application
.\launch.ps1

# Ou via commande longue
powershell -ExecutionPolicy Bypass -File launch.ps1
```

**Commandes additionnelles** (PowerShell uniquement):

```powershell
# Arrêter tous les services
.\launch.ps1 -StopOnly

# Voir le status actuel
.\launch.ps1 -StatusOnly
```

---

## Qu'est-ce qui se passe au lancement ?

### Étape 1️⃣ : Vérification Docker
```
✓ Docker trouvé
```

### Étape 2️⃣ : Démarrage PostgreSQL
```
✓ Conteneur déjà en cours (ou créé si nouveau)
⏳ Attente PostgreSQL (15-20s)
```

### Étape 3️⃣ : Test connexion
```
✓ PostgreSQL connecté
```

### Étape 4️⃣ : Tables analytiques
```
✓ Tables marts existantes
(ou créées si manquantes)
```

### Étape 5️⃣ : Python venv
```
✓ Venv activé
```

### Étape 6️⃣ : Streamlit lancé
```
===================================================================
  ✓ Application prête !
  🌐 Accès: http://localhost:8501
===================================================================
```

**Ouvre le navigateur** → http://localhost:8501

---

## Problèmes & Solutions

### Docker n'est pas installé

```
❌ Docker n'est pas installé ou n'est pas dans PATH
```

**Solution** : Installe Docker Desktop
- Windows/Mac : https://www.docker.com/products/docker-desktop
- Linux : `sudo apt install docker.io`

### PostgreSQL ne démarre pas

**Symptôme** :
```
⏳ Attente PostgreSQL (20s)...
❌ Erreur de connexion PostgreSQL
```

**Solution** :
```bash
# Redémarre Docker manuellement
docker-compose down
docker-compose up -d

# Puis relance le script
```

### Venv introuvable

```
❌ Venv non trouvé
```

**Solution** :
```bash
# Crée venv
python -m venv venv

# Ou réinstalle les dépendances
pip install -r requirements.txt
```

---

## Fichiers essentiels

Pour que les scripts fonctionnent, tu dois avoir :

```
project_ports_dashboard/
├── launch.bat              ← Script batch
├── launch.ps1              ← Script PowerShell
├── app.py                  ← Application Streamlit
├── create_marts.sql        ← Création des tables
├── docker-compose.yml      ← Configuration Docker
├── venv/                   ← Environnement Python
├── .env                    ← Credentials BD
└── requirements.txt        ← Dépendances
```

---

## Arrêter l'application

### Streamlit
```bash
# Dans la console Streamlit
Ctrl+C
```

### Docker (optionnel - rester actif)
```bash
# PowerShell seulement
.\launch.ps1 -StopOnly

# Ou manuellement
docker-compose down
```

---

## Vérifier le status

### PowerShell
```powershell
.\launch.ps1 -StatusOnly
```

### Manuellement
```bash
# Docker
docker ps

# PostgreSQL
docker exec ports_postgres_db psql -U postgres -d ports_dashboard -c "SELECT 1"

# Tables
docker exec ports_postgres_db psql -U postgres -d ports_dashboard -c "SELECT COUNT(*) FROM marts.mart_port_annual_summary"
```

---

## Shortcut Desktop (optionnel)

### Créer un raccourci pour lancer facilement

**Windows** :
1. Clique droit sur `launch.bat`
2. "Créer un raccourci"
3. Déplace le raccourci sur le Bureau
4. Double-clique pour lancer

**PowerShell** (via `.bat` wrapper) :

Crée `launch_ps.bat` :
```batch
@echo off
powershell -ExecutionPolicy Bypass -File launch.ps1
pause
```

---

## Checklist Démarrage Quotidien

- [ ] Docker Desktop lancé (ou lancé par script)
- [ ] Script exécuté (`launch.bat` ou `launch.ps1`)
- [ ] Attente 20 secondes pour PostgreSQL
- [ ] Streamlit affiche "Application prête"
- [ ] Navigateur ouvre http://localhost:8501
- [ ] Dashboard affiche les données

---

## C'est tout ! 🎉

À chaque fois que tu veux utiliser le dashboard :

```bash
# Option A (Batch)
launch.bat

# Option B (PowerShell)
.\launch.ps1
```

**L'application sera prête en ~30 secondes** ✨