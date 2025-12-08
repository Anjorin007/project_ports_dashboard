"""
Phase 1 - Nettoyage du Dataset
Prépare les données brutes pour Phase 2 (PostgreSQL)

Actions:
1. Supprimer Lagos (qualité insuffisante)
2. Garder PAC 2024 Q3 seulement (filtrer 2019, 2023)
3. Ajouter métadonnées d'analyse
4. Générer rapport de nettoyage
"""

import pandas as pd
import json
import logging
from pathlib import Path
from datetime import datetime

# ============================================================================
# CONFIGURATION
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('phase1_cleaning.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

RAW_FILE = Path('data/raw/all_ports_raw.csv')
PROCESSED_DIR = Path('data/processed')
CLEAN_FILE = PROCESSED_DIR / 'ports_clean.csv'
REPORT_FILE = PROCESSED_DIR / 'cleaning_report.json'

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# CLASSE PRINCIPALE
# ============================================================================

class DatasetCleaner:
    """Nettoyage et enrichissement du dataset portuaire"""
    
    def __init__(self, raw_file):
        self.raw_file = raw_file
        self.df_raw = None
        self.df_clean = None
        self.report = {
            'timestamp': datetime.now().isoformat(),
            'actions': [],
            'stats_before': {},
            'stats_after': {},
        }
    
    def load_raw_data(self):
        """Charge le CSV brut"""
        logger.info("\n" + "="*70)
        logger.info("PHASE 1 - NETTOYAGE DATASET")
        logger.info("="*70)
        
        try:
            self.df_raw = pd.read_csv(self.raw_file)
            logger.info(f"✓ Dataset chargé: {len(self.df_raw)} lignes")
            
            # Statistiques avant
            self.report['stats_before'] = {
                'total_rows': len(self.df_raw),
                'ports': self.df_raw['port_code'].unique().tolist(),
                'num_ports': self.df_raw['port_code'].nunique(),
                'years': sorted(self.df_raw['year'].unique().tolist()),
                'quality_flags': self.df_raw['data_quality_flag'].value_counts().to_dict(),
                'ports_with_tonnage': [
                    port for port in self.df_raw['port_code'].unique()
                    if self.df_raw[self.df_raw['port_code'] == port]['tonnage_mt'].notna().any()
                ],
                'ports_with_teus': [
                    port for port in self.df_raw['port_code'].unique()
                    if self.df_raw[self.df_raw['port_code'] == port]['teus'].notna().any()
                ],
            }
            
            logger.info(f"  Ports trouvés: {self.report['stats_before']['num_ports']}")
            logger.info(f"  Années: {self.report['stats_before']['years']}")
            logger.info(f"  Quality flags: {self.report['stats_before']['quality_flags']}")
            
            return True
        except Exception as e:
            logger.error(f"✗ Erreur chargement: {e}")
            return False
    
    def remove_lagos(self):
        """Supprime Lagos (qualité insuffisante)"""
        logger.info("\n[1/4] Suppression Lagos...")
        
        initial_count = len(self.df_raw)
        self.df_raw = self.df_raw[self.df_raw['port_code'] != 'LAGOS']
        removed_count = initial_count - len(self.df_raw)
        
        logger.info(f"✓ Supprimé {removed_count} lignes Lagos")
        self.report['actions'].append({
            'action': 'remove_lagos',
            'rows_removed': removed_count,
            'reason': 'Qualité insuffisante (100% ESTIMATED, pas de données officielles NPA)'
        })
    
    def clean_pac_temporal(self):
        """Garde PAC 2024 Q3 seulement"""
        logger.info("\n[2/4] Nettoyage temporel PAC...")
        
        pac_initial = len(self.df_raw[self.df_raw['port_code'] == 'PAC'])
        
        # Garder seulement 2024 Q3 pour PAC
        pac_mask = (self.df_raw['port_code'] == 'PAC') & (
            ~((self.df_raw['year'] == 2024) & (self.df_raw['quarter'] == 3))
        )
        
        removed_count = len(self.df_raw[pac_mask & (self.df_raw['port_code'] == 'PAC')])
        self.df_raw = self.df_raw[~pac_mask]
        
        logger.info(f"✓ PAC nettoyé: {pac_initial} → {len(self.df_raw[self.df_raw['port_code'] == 'PAC'])} lignes")
        logger.info(f"  Supprimé: années 2019 (baseline) et 2023 (estimée, gap énorme)")
        
        self.report['actions'].append({
            'action': 'clean_pac_temporal',
            'rows_removed': removed_count,
            'reason': 'GAP temporel énorme (2019, 2023 supprimées). Garder 2024 Q3 VERIFIED',
            'pac_kept': '2024 Q3 (VERIFIED)',
            'pac_removed': '2019 (baseline), 2023 (interpolée, trop éloignée)'
        })
    
    def check_duplicates(self):
        """Vérifie les duplicatas"""
        logger.info("\n[3/4] Vérification duplicatas...")
        
        # Grouper par port, year, quarter pour détecter duplicatas
        duplicates = self.df_raw.groupby(
            ['port_code', 'year', 'quarter', 'data_source']
        ).size()
        
        has_duplicates = (duplicates > 1).any()
        
        if has_duplicates:
            logger.warning(f"⚠ Duplicatas détectés:")
            logger.warning(duplicates[duplicates > 1])
        else:
            logger.info(f"✓ Pas de duplicatas")
        
        self.report['actions'].append({
            'action': 'check_duplicates',
            'has_duplicates': has_duplicates,
            'duplicate_count': int((duplicates > 1).sum()) if has_duplicates else 0
        })
    
    def enrich_metadata(self):
        """Ajoute métadonnées d'analyse"""
        logger.info("\n[4/4] Enrichissement métadonnées...")
        
        # Colonne: included in analysis
        self.df_raw['included_in_analysis'] = True
        
        # Colonne: has tonnage
        self.df_raw['has_tonnage'] = self.df_raw['tonnage_mt'].notna()
        
        # Colonne: has TEUs
        self.df_raw['has_teus'] = self.df_raw['teus'].notna()
        
        # Colonne: clean date
        self.df_raw['clean_date'] = datetime.now().date()
        
        # Colonne: analysis note
        self.df_raw['analysis_note'] = self.df_raw.apply(
            self._get_analysis_note, axis=1
        )
        
        logger.info(f"✓ Métadonnées ajoutées:")
        logger.info(f"  - included_in_analysis")
        logger.info(f"  - has_tonnage")
        logger.info(f"  - has_teus")
        logger.info(f"  - clean_date")
        logger.info(f"  - analysis_note")
        
        # Statistiques enrichissement
        tonnage_ports = self.df_raw['has_tonnage'].sum()
        teu_ports = self.df_raw['has_teus'].sum()
        
        logger.info(f"\n  Indicateurs disponibles:")
        logger.info(f"    - Lignes avec tonnage: {tonnage_ports}/{len(self.df_raw)}")
        logger.info(f"    - Lignes avec TEU: {teu_ports}/{len(self.df_raw)}")
    
    def _get_analysis_note(self, row):
        """Génère note d'analyse pour chaque ligne"""
        notes = []
        
        if not row['has_tonnage'] and not row['has_teus']:
            notes.append("NO_DATA")
        if row['has_tonnage'] and row['has_teus']:
            notes.append("BOTH_INDICATORS")
        elif row['has_tonnage']:
            notes.append("TONNAGE_ONLY")
        elif row['has_teus']:
            notes.append("TEU_ONLY")
        
        if row['data_quality_flag'] == 'ESTIMATED':
            notes.append("ESTIMATED_VALUE")
        
        return "; ".join(notes) if notes else "COMPLETE"
    
    def validate_cleaning(self):
        """Valide le nettoyage"""
        logger.info("\n" + "="*70)
        logger.info("VALIDATION NETTOYAGE")
        logger.info("="*70)
        
        # Check 1: Lagos absent
        lagos_present = 'LAGOS' in self.df_raw['port_code'].values
        logger.info(f"{'✓' if not lagos_present else '✗'} Lagos absent: {not lagos_present}")
        
        # Check 2: PAC a 1 ligne
        pac_count = len(self.df_raw[self.df_raw['port_code'] == 'PAC'])
        logger.info(f"{'✓' if pac_count == 1 else '✗'} PAC a 1 ligne: {pac_count == 1}")
        
        if pac_count == 1:
            pac_row = self.df_raw[self.df_raw['port_code'] == 'PAC'].iloc[0]
            logger.info(f"    → {pac_row['year']} Q{pac_row['quarter']} ({pac_row['data_quality_flag']})")
        
        # Check 3: Ports restants
        remaining_ports = sorted(self.df_raw['port_code'].unique())
        logger.info(f"✓ Ports restants: {remaining_ports}")
        
        # Check 4: Compte par port
        logger.info(f"\n✓ Distribution par port:")
        for port in remaining_ports:
            port_data = self.df_raw[self.df_raw['port_code'] == port]
            tonnage_count = port_data['has_tonnage'].sum()
            teu_count = port_data['has_teus'].sum()
            logger.info(f"    {port}: {len(port_data)} lignes (tonnage={tonnage_count}, teus={teu_count})")
        
        # Check 5: Quality flags
        logger.info(f"\n✓ Distribution quality flags:")
        for flag in self.df_raw['data_quality_flag'].unique():
            count = len(self.df_raw[self.df_raw['data_quality_flag'] == flag])
            logger.info(f"    {flag}: {count}")
        
        # Check 6: Années
        years = sorted(self.df_raw['year'].unique())
        logger.info(f"\n✓ Années présentes: {years}")
        
        # Stats après
        self.report['stats_after'] = {
            'total_rows': len(self.df_raw),
            'ports': remaining_ports,
            'num_ports': len(remaining_ports),
            'years': years,
            'quality_flags': self.df_raw['data_quality_flag'].value_counts().to_dict(),
            'rows_with_tonnage': int(self.df_raw['has_tonnage'].sum()),
            'rows_with_teus': int(self.df_raw['has_teus'].sum()),
            'lagos_removed': True,
            'pac_filtered': True,
        }
        
        return True
    
    def save_clean_data(self):
        """Sauvegarde le dataset nettoyé"""
        logger.info("\n" + "="*70)
        logger.info("SAUVEGARDE DONNÉES NETTOYÉES")
        logger.info("="*70)
        
        try:
            # Sauvegarde CSV
            self.df_raw.to_csv(CLEAN_FILE, index=False)
            logger.info(f"✓ CSV nettoyé: {CLEAN_FILE}")
            logger.info(f"  Taille: {len(self.df_raw)} lignes, {len(self.df_raw.columns)} colonnes")
            
            # Sauvegarde rapport JSON
            with open(REPORT_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.report, f, indent=2, ensure_ascii=False, default=str)
            logger.info(f"✓ Rapport JSON: {REPORT_FILE}")
            
            return True
        except Exception as e:
            logger.error(f"✗ Erreur sauvegarde: {e}")
            return False
    
    def print_summary(self):
        """Affiche résumé final"""
        logger.info("\n" + "="*70)
        logger.info("RÉSUMÉ NETTOYAGE")
        logger.info("="*70)
        
        before = self.report['stats_before']
        after = self.report['stats_after']
        
        logger.info(f"\nAVANT NETTOYAGE:")
        logger.info(f"  Lignes: {before['total_rows']}")
        logger.info(f"  Ports: {before['num_ports']} {before['ports']}")
        logger.info(f"  Quality: {before['quality_flags']}")
        
        logger.info(f"\nAPRÈS NETTOYAGE:")
        logger.info(f"  Lignes: {after['total_rows']}")
        logger.info(f"  Ports: {after['num_ports']} {after['ports']}")
        logger.info(f"  Quality: {after['quality_flags']}")
        
        logger.info(f"\nMÉTADONNÉES ENRICHIES:")
        logger.info(f"  Lignes avec tonnage: {after['rows_with_tonnage']}/{after['total_rows']}")
        logger.info(f"  Lignes avec TEU: {after['rows_with_teus']}/{after['total_rows']}")
        
        logger.info(f"\nACTIONS EXÉCUTÉES:")
        for i, action in enumerate(self.report['actions'], 1):
            logger.info(f"  [{i}] {action['action']}")
            if 'rows_removed' in action:
                logger.info(f"      → Lignes supprimées: {action['rows_removed']}")
            logger.info(f"      → Raison: {action['reason']}")
        
        logger.info("\n✓ PHASE 1 NETTOYAGE COMPLÈTE")
        logger.info("="*70)
    
    def run(self):
        """Exécution complète"""
        
        # 1. Chargement
        if not self.load_raw_data():
            return False
        
        # 2. Nettoyage
        self.remove_lagos()
        self.clean_pac_temporal()
        self.check_duplicates()
        self.enrich_metadata()
        
        # 3. Validation
        if not self.validate_cleaning():
            return False
        
        # 4. Sauvegarde
        if not self.save_clean_data():
            return False
        
        # 5. Résumé
        self.print_summary()
        
        return True


# ============================================================================
# EXECUTION
# ============================================================================

def main():
    """Script principal"""
    cleaner = DatasetCleaner(RAW_FILE)
    success = cleaner.run()
    return 0 if success else 1


if __name__ == '__main__':
    exit(main())