"""
Phase 1 - Validation Rapide du Dataset
Script pour vérifier que tout s'est déroulé correctement
"""

import pandas as pd
import json
from pathlib import Path

print("\n" + "="*70)
print("VALIDATION PHASE 1 - Vérification du Dataset Complet")
print("="*70)

# Fichier brut
csv_file = Path('data/raw/all_ports_raw.csv')
metadata_file = Path('data/raw/metadata_extraction.json')

# ============================================================================
# 1. VÉRIFICATION DES FICHIERS
# ============================================================================

print("\n[1/5] Vérification des fichiers...")
if csv_file.exists():
    print(f"✓ {csv_file} EXISTS")
else:
    print(f"✗ {csv_file} NOT FOUND")
    exit(1)

if metadata_file.exists():
    print(f"✓ {metadata_file} EXISTS")
else:
    print(f"⚠ {metadata_file} NOT FOUND (non critique)")

# ============================================================================
# 2. CHARGEMENT DES DONNÉES
# ============================================================================

print("\n[2/5] Chargement des données CSV...")
df = pd.read_csv(csv_file)
print(f"✓ CSV chargé: {len(df)} lignes, {len(df.columns)} colonnes")

# ============================================================================
# 3. STRUCTURE ET QUALITÉ
# ============================================================================

print("\n[3/5] Vérification de la structure...")

# Vérification colonnes
required_cols = [
    'port_code', 'port_name', 'country', 'year', 
    'tonnage_mt', 'teus', 'num_vessels',
    'data_source', 'source_url', 'data_quality_flag', 'notes'
]

missing_cols = [col for col in required_cols if col not in df.columns]
if missing_cols:
    print(f"✗ Colonnes manquantes: {missing_cols}")
else:
    print(f"✓ Toutes les colonnes requises présentes")

# Vérification ports
ports_expected = {'PAC', 'TEMA', 'LOME', 'ABIDJAN', 'LAGOS'}
ports_found = set(df['port_code'].unique())
print(f"✓ Ports trouvés: {sorted(ports_found)}")
if ports_found == ports_expected:
    print(f"✓ 5 ports présents (complet)")
else:
    print(f"⚠ Ports manquants: {ports_expected - ports_found}")

# Années présentes
years = sorted(df['year'].unique())
print(f"✓ Années: {years}")

# ============================================================================
# 4. QUALITÉ DES DONNÉES
# ============================================================================

print("\n[4/5] Analyse de qualité par port...")

for port_code in sorted(df['port_code'].unique()):
    port_data = df[df['port_code'] == port_code]
    port_name = port_data['port_name'].iloc[0]
    
    print(f"\n  {port_code} - {port_name}:")
    print(f"    Enregistrements: {len(port_data)}")
    print(f"    Années: {sorted(port_data['year'].unique())}")
    
    # Tonnage
    tonnage_count = port_data['tonnage_mt'].notna().sum()
    if tonnage_count > 0:
        print(f"    Tonnage: {tonnage_count} points (max: {port_data['tonnage_mt'].max():.0f} mt)")
    else:
        print(f"    Tonnage: Aucune donnée")
    
    # TEU
    teu_count = port_data['teus'].notna().sum()
    if teu_count > 0:
        print(f"    TEU: {teu_count} points (max: {port_data['teus'].max():.0f})")
    else:
        print(f"    TEU: Aucune donnée")
    
    # Navires
    vessel_count = port_data['num_vessels'].notna().sum()
    if vessel_count > 0:
        print(f"    Navires: {vessel_count} points (max: {port_data['num_vessels'].max():.0f})")
    else:
        print(f"    Navires: Aucune donnée")
    
    # Quality flags
    quality_dist = port_data['data_quality_flag'].value_counts()
    print(f"    Quality flags: {quality_dist.to_dict()}")

# ============================================================================
# 5. DONNÉES BRUTES - APERÇU
# ============================================================================

print("\n[5/5] Aperçu des données (premiers enregistrements)...")
print("\n" + df[['port_code', 'year', 'tonnage_mt', 'teus', 'data_quality_flag', 'notes']].to_string())

# ============================================================================
# RÉSUMÉ VALIDATION
# ============================================================================

print("\n" + "="*70)
print("CRITÈRES DE VALIDATION")
print("="*70)

validation_checks = {
    '5 ports présents': df['port_code'].nunique() == 5,
    '14+ lignes de données': len(df) >= 14,
    'Colonnes de traçabilité (source_url, quality_flag)': 'source_url' in df.columns and 'data_quality_flag' in df.columns,
    'Années 2023-2024 présentes': 2023 in df['year'].values and 2024 in df['year'].values,
    'Pas de valeurs NULL incohérentes': df['data_quality_flag'].notna().all(),
    'Notes documentées': df['notes'].notna().all() and len(df['notes'].iloc[0]) > 5,
}

all_pass = True
for check, result in validation_checks.items():
    status = "✓ PASS" if result else "✗ FAIL"
    print(f"{status}: {check}")
    if not result:
        all_pass = False

# ============================================================================
# CONCLUSION
# ============================================================================

print("\n" + "="*70)
if all_pass:
    print("✓✓✓ PHASE 1 VALIDÉE - Données prêtes pour PHASE 2")
    print("="*70)
    print("\nProchaine étape: PHASE 2 - Stockage PostgreSQL")
    print("\nPoints clés pour Phase 2:")
    print("  1. Créer schéma PostgreSQL (table ports_data)")
    print("  2. Charger all_ports_raw.csv")
    print("  3. Ajouter contraintes + types")
    print("  4. Mettre en place ETL automatisée")
else:
    print("✗ PHASE 1 - PROBLÈMES DÉTECTÉS")
    print("="*70)
    print("Vérifiez les erreurs ci-dessus avant de continuer")

print("\n" + "="*70)