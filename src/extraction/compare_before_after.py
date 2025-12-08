"""
Phase 1 - Comparaison Avant/Après Nettoyage
Vérifie que le nettoyage s'est déroulé correctement
"""

import pandas as pd
import json
from pathlib import Path

print("\n" + "="*70)
print("COMPARAISON AVANT/APRÈS NETTOYAGE")
print("="*70)

RAW_FILE = Path('data/raw/all_ports_raw.csv')
CLEAN_FILE = Path('data/processed/ports_clean.csv')
REPORT_FILE = Path('data/processed/cleaning_report.json')

# Charger les données
df_raw = pd.read_csv(RAW_FILE)
df_clean = pd.read_csv(CLEAN_FILE)

# Charger le rapport
with open(REPORT_FILE, 'r', encoding='utf-8') as f:
    report = json.load(f)

# ============================================================================
# SECTION 1 : COMPARAISON GLOBALE
# ============================================================================

print("\n[1] COMPARAISON GLOBALE")
print("-" * 70)

print(f"\nLignes:")
print(f"  AVANT : {len(df_raw)} lignes")
print(f"  APRÈS : {len(df_clean)} lignes")
print(f"  SUPPRIMÉES : {len(df_raw) - len(df_clean)} lignes ({100*(len(df_raw)-len(df_clean))/len(df_raw):.1f}%)")

print(f"\nPorts:")
ports_before = sorted(df_raw['port_code'].unique())
ports_after = sorted(df_clean['port_code'].unique())
print(f"  AVANT : {ports_before}")
print(f"  APRÈS : {ports_after}")
print(f"  SUPPRIMÉS : {set(ports_before) - set(ports_after)}")

print(f"\nAnnées:")
years_before = sorted(df_raw['year'].unique())
years_after = sorted(df_clean['year'].unique())
print(f"  AVANT : {years_before}")
print(f"  APRÈS : {years_after}")

# ============================================================================
# SECTION 2 : DÉTAILS PAR PORT
# ============================================================================

print("\n[2] DÉTAILS PAR PORT")
print("-" * 70)

for port in ports_after:
    raw_count = len(df_raw[df_raw['port_code'] == port])
    clean_count = len(df_clean[df_clean['port_code'] == port])
    
    clean_data = df_clean[df_clean['port_code'] == port]
    
    print(f"\n{port}:")
    print(f"  Lignes: {raw_count} → {clean_count} ({raw_count - clean_count} supprimées)")
    
    if clean_count > 0:
        years = sorted(clean_data['year'].unique())
        quarters = clean_data['quarter'].dropna().unique()
        
        print(f"  Années: {years}")
        print(f"  Trimestres: {sorted([int(q) for q in quarters if pd.notna(q)])}")
        
        # Indicateurs
        has_tonnage = clean_data['has_tonnage'].sum()
        has_teus = clean_data['has_teus'].sum()
        print(f"  Indicateurs: tonnage={has_tonnage}, teus={has_teus}")
        
        # Quality
        quality_dist = clean_data['data_quality_flag'].value_counts().to_dict()
        print(f"  Quality: {quality_dist}")

# ============================================================================
# SECTION 3 : VALIDATIONS CRITIQUES
# ============================================================================

print("\n[3] VALIDATIONS CRITIQUES")
print("-" * 70)

checks = {
    'Lagos supprimé': 'LAGOS' not in df_clean['port_code'].values,
    'PAC a 1 ligne': len(df_clean[df_clean['port_code'] == 'PAC']) == 1,
    'PAC est 2024 Q3': (
        len(df_clean[df_clean['port_code'] == 'PAC']) > 0 and
        df_clean[df_clean['port_code'] == 'PAC'].iloc[0]['year'] == 2024 and
        df_clean[df_clean['port_code'] == 'PAC'].iloc[0]['quarter'] == 3
    ),
    'Pas de duplicatas': len(df_clean) == len(df_clean.drop_duplicates(
        subset=['port_code', 'year', 'quarter', 'data_source']
    )),
    'Métadonnées ajoutées': all(col in df_clean.columns for col in [
        'included_in_analysis', 'has_tonnage', 'has_teus', 'clean_date'
    ]),
}

all_pass = True
for check, result in checks.items():
    status = "✓ PASS" if result else "✗ FAIL"
    print(f"{status}: {check}")
    if not result:
        all_pass = False

# ============================================================================
# SECTION 4 : STATISTIQUES MÉTADONNÉES
# ============================================================================

print("\n[4] STATISTIQUES MÉTADONNÉES")
print("-" * 70)

print(f"\nDates de nettoyage:")
clean_dates = df_clean['clean_date'].unique()
print(f"  {clean_dates[0]}")

print(f"\nDisponibilité indicateurs:")
print(f"  Avec tonnage: {df_clean['has_tonnage'].sum()}/{len(df_clean)}")
print(f"  Avec TEU: {df_clean['has_teus'].sum()}/{len(df_clean)}")
print(f"  Tous deux: {len(df_clean[(df_clean['has_tonnage']) & (df_clean['has_teus'])])}/{len(df_clean)}")

print(f"\nNotes d'analyse (premiers 3 uniques):")
for note in df_clean['analysis_note'].unique()[:3]:
    count = len(df_clean[df_clean['analysis_note'] == note])
    print(f"  {note}: {count} lignes")

# ============================================================================
# SECTION 5 : RAPPORT JSON
# ============================================================================

print("\n[5] RAPPORT JSON GÉNÉRÉ")
print("-" * 70)

print(f"\nFichier: {REPORT_FILE}")
print(f"Timestamp: {report['timestamp']}")
print(f"\nActions exécutées:")
for i, action in enumerate(report['actions'], 1):
    print(f"  [{i}] {action['action']}")

print(f"\nStatistiques AVANT:")
for key, value in report['stats_before'].items():
    if isinstance(value, (int, list, dict)):
        print(f"  {key}: {value}")

print(f"\nStatistiques APRÈS:")
for key, value in report['stats_after'].items():
    if isinstance(value, (int, list, dict)):
        print(f"  {key}: {value}")

# ============================================================================
# CONCLUSION
# ============================================================================

print("\n" + "="*70)
if all_pass:
    print("✓✓✓ NETTOYAGE VALIDÉ - Données prêtes pour PHASE 2")
    print("="*70)
    print(f"\nFichiers générés:")
    print(f"  1. {CLEAN_FILE} ({len(df_clean)} lignes)")
    print(f"  2. {REPORT_FILE}")
    print(f"  3. phase1_cleaning.log")
    print(f"\nProchaine étape: PHASE 2 - PostgreSQL")
else:
    print("✗ NETTOYAGE - PROBLÈMES DÉTECTÉS")
    print("="*70)

print("\n" + "="*70)