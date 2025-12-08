"""
Phase 2: Chargement des données nettoyées dans PostgreSQL
Charge data/processed/ports_clean.csv → PostgreSQL

Prérequis:
- Docker: docker-compose up -d
- Dépendances: pip install psycopg2-binary pandas python-dotenv
"""

import sys
import os
import io

# Fix encoding on Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import pandas as pd
import psycopg2
from psycopg2 import sql, Error
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# ============================================================================
# CONFIGURATION
# ============================================================================

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('phase2_loader.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Config DB
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'ports_dashboard'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres'),
    'port': os.getenv('DB_PORT', '5432'),
}

CLEAN_CSV = Path('data/processed/ports_clean.csv')

# ============================================================================
# CLASSE PRINCIPALE
# ============================================================================

class PostgreSQLDataLoader:
    """Chargement données nettoyées → PostgreSQL"""
    
    def __init__(self, db_config):
        self.db_config = db_config
        self.connection = None
        self.cursor = None
    
    def connect(self):
        """Établit connexion PostgreSQL"""
        try:
            self.connection = psycopg2.connect(**self.db_config)
            self.cursor = self.connection.cursor()
            logger.info("[OK] Connexion PostgreSQL établie")
            return True
        except Error as e:
            logger.error(f"[ERROR] Erreur connexion: {e}")
            return False
    
    def close(self):
        """Ferme connexion"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
    
    def check_schema_ready(self):
        """Vérifie que le schéma existe"""
        try:
            self.cursor.execute("""
                SELECT EXISTS(
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name = 'fact_port_traffic'
                )
            """)
            exists = self.cursor.fetchone()[0]
            if not exists:
                logger.error("[ERROR] Table fact_port_traffic n'existe pas")
                return False
            logger.info("[OK] Schema PostgreSQL verifie")
            return True
        except Error as e:
            logger.error(f"[ERROR] Erreur verification schema: {e}")
            return False
    
    def load_clean_csv(self):
        """Charge CSV nettoyé"""
        try:
            df = pd.read_csv(CLEAN_CSV)
            logger.info(f"[OK] CSV charge: {len(df)} lignes")
            return df
        except Exception as e:
            logger.error(f"[ERROR] Erreur chargement CSV: {e}")
            return None
    
    def insert_data(self, df):
        """Insère les données nettoyées"""
        
        logger.info("\n" + "="*70)
        logger.info("INSERTION DONNEES NETTOYEES")
        logger.info("="*70)
        
        inserted = 0
        failed = 0
        
        for idx, row in df.iterrows():
            try:
                # Récupère l'ID du port
                self.cursor.execute(
                    "SELECT port_id FROM dim_port WHERE port_code = %s",
                    (row['port_code'],)
                )
                port_result = self.cursor.fetchone()
                if not port_result:
                    logger.warning(f"  Ligne {idx}: Port {row['port_code']} non trouve")
                    failed += 1
                    continue
                
                port_id = port_result[0]
                
                # Récupère l'ID du quality flag
                quality_flag_id = None
                if pd.notna(row['data_quality_flag']):
                    self.cursor.execute(
                        "SELECT flag_id FROM dim_quality_flag WHERE flag_name = %s",
                        (row['data_quality_flag'],)
                    )
                    flag_result = self.cursor.fetchone()
                    if flag_result:
                        quality_flag_id = flag_result[0]
                
                # Prépare les valeurs
                tonnage = float(row['tonnage_mt']) if pd.notna(row['tonnage_mt']) else None
                imports_mt = float(row['imports_mt']) if pd.notna(row['imports_mt']) else None
                exports_mt = float(row['exports_mt']) if pd.notna(row['exports_mt']) else None
                teus = int(row['teus']) if pd.notna(row['teus']) else None
                num_vessels = int(row['num_vessels']) if pd.notna(row['num_vessels']) else None
                quarter = float(row['quarter']) if pd.notna(row['quarter']) else None
                
                has_tonnage = bool(row['has_tonnage']) if 'has_tonnage' in row else (tonnage is not None)
                has_teus = bool(row['has_teus']) if 'has_teus' in row else (teus is not None)
                
                # Insertion
                self.cursor.execute("""
                    INSERT INTO fact_port_traffic 
                    (port_id, quality_flag_id, year, quarter, 
                     tonnage_mt, imports_mt, exports_mt, teus, num_vessels,
                     data_source, source_url, has_tonnage, has_teus,
                     analysis_note, extraction_date, data_notes, clean_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (port_id, year, quarter) 
                    DO UPDATE SET
                        tonnage_mt = EXCLUDED.tonnage_mt,
                        teus = EXCLUDED.teus,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    port_id,
                    quality_flag_id,
                    int(row['year']),
                    quarter,
                    tonnage,
                    imports_mt,
                    exports_mt,
                    teus,
                    num_vessels,
                    row['data_source'] if pd.notna(row['data_source']) else None,
                    row['source_url'] if pd.notna(row['source_url']) else None,
                    has_tonnage,
                    has_teus,
                    row['analysis_note'] if 'analysis_note' in row and pd.notna(row['analysis_note']) else None,
                    pd.Timestamp(row['extraction_date']).date(),
                    row['notes'] if pd.notna(row['notes']) else None,
                    pd.Timestamp(row['clean_date']).date() if 'clean_date' in row and pd.notna(row['clean_date']) else None,
                ))
                
                inserted += 1
                if (idx + 1) % 5 == 0:
                    logger.info(f"  {idx + 1}/{len(df)} lignes inserees...")
                    
            except Error as e:
                logger.error(f"  [ERROR] Ligne {idx}: {e}")
                failed += 1
        
        # Commit
        try:
            self.connection.commit()
            logger.info(f"\n[OK] Insertion complete:")
            logger.info(f"  - Reussis: {inserted}/{len(df)}")
            logger.info(f"  - Echoues: {failed}/{len(df)}")
            return inserted, failed
        except Error as e:
            logger.error(f"[ERROR] Erreur commit: {e}")
            self.connection.rollback()
            return 0, len(df)
    
    def log_etl_operation(self, num_records, status):
        """Enregistre l'opération dans ETL log"""
        try:
            self.cursor.execute("""
                INSERT INTO etl_load_history (load_phase, action, num_records, status)
                VALUES ('phase2', 'load_clean_data', %s, %s)
            """, (num_records, status))
            self.connection.commit()
        except Error as e:
            logger.warning(f"[WARNING] Erreur log ETL: {e}")
    
    def validate_load(self):
        """Valide le chargement"""
        logger.info("\n" + "="*70)
        logger.info("VALIDATION CHARGEMENT")
        logger.info("="*70)
        
        try:
            # Total records
            self.cursor.execute("SELECT COUNT(*) FROM fact_port_traffic")
            total = self.cursor.fetchone()[0]
            logger.info(f"[OK] Total records: {total}")
            
            # Par port
            self.cursor.execute("""
                SELECT p.port_code, COUNT(*) 
                FROM fact_port_traffic f
                JOIN dim_port p ON f.port_id = p.port_id
                GROUP BY p.port_code
                ORDER BY p.port_code
            """)
            logger.info(f"[OK] Distribution par port:")
            for port_code, count in self.cursor.fetchall():
                logger.info(f"    {port_code}: {count}")
            
            # Quality flags
            self.cursor.execute("""
                SELECT q.flag_name, COUNT(*)
                FROM fact_port_traffic f
                LEFT JOIN dim_quality_flag q ON f.quality_flag_id = q.flag_id
                GROUP BY q.flag_name
            """)
            logger.info(f"[OK] Distribution quality:")
            for flag, count in self.cursor.fetchall():
                logger.info(f"    {flag}: {count}")
            
        except Error as e:
            logger.error(f"[ERROR] Erreur validation: {e}")
    
    def run(self):
        """Exécution complète"""
        
        logger.info("\n" + "="*70)
        logger.info("PHASE 2: CHARGEMENT DONNEES NETTOYEES")
        logger.info("="*70)
        
        # 1. Connexion
        if not self.connect():
            return False
        
        # 2. Vérification schéma
        if not self.check_schema_ready():
            self.close()
            return False
        
        # 3. Chargement CSV
        df = self.load_clean_csv()
        if df is None or df.empty:
            self.close()
            return False
        
        # 4. Insertion
        inserted, failed = self.insert_data(df)
        
        # 5. Log ETL
        status = 'SUCCESS' if failed == 0 else 'PARTIAL' if inserted > 0 else 'FAILED'
        self.log_etl_operation(inserted, status)
        
        # 6. Validation
        self.validate_load()
        
        # 7. Fermeture
        self.close()
        
        logger.info("\n" + "="*70)
        logger.info("[OK] PHASE 2 COMPLETE")
        logger.info("="*70)
        
        return True


# ============================================================================
# EXECUTION
# ============================================================================

def main():
    """Script principal"""
    loader = PostgreSQLDataLoader(DB_CONFIG)
    success = loader.run()
    return 0 if success else 1


if __name__ == '__main__':
    exit(main())