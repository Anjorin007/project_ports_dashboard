-- ============================================================================
-- PHASE 2: PostgreSQL Schema - Ports Dashboard
-- Données nettoyées (10 lignes, 4 ports)
-- ============================================================================

-- ============================================================================
-- TABLES DIMENSIONNELLES
-- ============================================================================

-- Dimension: Ports
CREATE TABLE IF NOT EXISTS dim_port (
    port_id SERIAL PRIMARY KEY,
    port_code VARCHAR(10) UNIQUE NOT NULL,
    port_name VARCHAR(255) NOT NULL,
    country VARCHAR(100) NOT NULL,
    region VARCHAR(50) DEFAULT 'West Africa',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE dim_port IS 'Dimension ports - Ports Afrique de l''Ouest';

-- Dimension: Quality Flags
CREATE TABLE IF NOT EXISTS dim_quality_flag (
    flag_id SERIAL PRIMARY KEY,
    flag_name VARCHAR(50) UNIQUE NOT NULL,
    flag_description VARCHAR(255),
    severity INT DEFAULT 1 CHECK (severity >= 1 AND severity <= 3)
);

COMMENT ON TABLE dim_quality_flag IS 'Dimension qualité - Classification données';

-- ============================================================================
-- TABLE FACTUELLE PRINCIPALE
-- ============================================================================

-- Fact: Port Traffic Data (étoile simple)
CREATE TABLE IF NOT EXISTS fact_port_traffic (
    traffic_id SERIAL PRIMARY KEY,
    
    -- Clés étrangères
    port_id INT NOT NULL REFERENCES dim_port(port_id),
    quality_flag_id INT REFERENCES dim_quality_flag(flag_id),
    
    -- Dimensions temporelles
    year INT NOT NULL,
    quarter INT,
    
    -- Indicateurs de trafic (peuvent être NULL)
    tonnage_mt NUMERIC(15, 2),
    imports_mt NUMERIC(15, 2),
    exports_mt NUMERIC(15, 2),
    teus INT,
    num_vessels INT,
    
    -- Métadonnées source
    data_source VARCHAR(255),
    source_url TEXT,
    
    -- Indicateurs nettoyage
    has_tonnage BOOLEAN DEFAULT FALSE,
    has_teus BOOLEAN DEFAULT FALSE,
    analysis_note VARCHAR(255),
    
    -- Audit
    extraction_date DATE NOT NULL,
    data_notes TEXT,
    clean_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Contrainte unicité (évite duplicatas)
    CONSTRAINT unique_port_traffic UNIQUE (port_id, year, quarter)
);

COMMENT ON TABLE fact_port_traffic IS 'Fait principal - Trafic portuaire';
COMMENT ON COLUMN fact_port_traffic.tonnage_mt IS 'Tonnage total (imports + exports) en tonnes métriques';
COMMENT ON COLUMN fact_port_traffic.teus IS 'Conteneurs (Twenty-foot Equivalent Units)';
COMMENT ON COLUMN fact_port_traffic.has_tonnage IS 'TRUE si donnée tonnage_mt disponible';
COMMENT ON COLUMN fact_port_traffic.has_teus IS 'TRUE si donnée teus disponible';

-- ============================================================================
-- TABLE LOGS ETL
-- ============================================================================

CREATE TABLE IF NOT EXISTS etl_load_history (
    load_id SERIAL PRIMARY KEY,
    load_phase VARCHAR(50), -- 'phase1', 'phase2', 'phase3'
    action VARCHAR(100), -- 'extraction', 'cleaning', 'load'
    num_records INT,
    status VARCHAR(50), -- 'SUCCESS', 'PARTIAL', 'FAILED'
    error_message TEXT,
    load_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE etl_load_history IS 'Logs ETL - Traçabilité des opérations';

-- ============================================================================
-- INDEXES POUR PERFORMANCE
-- ============================================================================

CREATE INDEX idx_fact_port_id ON fact_port_traffic(port_id);
CREATE INDEX idx_fact_year ON fact_port_traffic(year);
CREATE INDEX idx_fact_year_quarter ON fact_port_traffic(year, quarter);
CREATE INDEX idx_fact_quality ON fact_port_traffic(quality_flag_id);
CREATE INDEX idx_fact_port_year ON fact_port_traffic(port_id, year);

-- ============================================================================
-- DONNÉES DE RÉFÉRENCE
-- ============================================================================

-- Insérer les ports
INSERT INTO dim_port (port_code, port_name, country) VALUES
    ('PAC', 'Port Autonome de Cotonou', 'Benin'),
    ('TEMA', 'Port of Tema', 'Ghana'),
    ('LOME', 'Port Autonome de Lomé', 'Togo'),
    ('ABIDJAN', 'Port Autonome d''Abidjan', 'Côte d''Ivoire')
ON CONFLICT (port_code) DO NOTHING;

-- Insérer les quality flags
INSERT INTO dim_quality_flag (flag_name, flag_description, severity) VALUES
    ('VERIFIED', 'Donnée vérifiée de source officielle', 1),
    ('ESTIMATED', 'Donnée estimée par interpolation', 2),
    ('PARTIAL', 'Donnée partielle ou incomplète', 2)
ON CONFLICT (flag_name) DO NOTHING;

-- ============================================================================
-- VUES ANALYTIQUES
-- ============================================================================

-- Vue 1: Données complètes avec contexte
CREATE OR REPLACE VIEW v_port_traffic_full AS
SELECT 
    f.traffic_id,
    p.port_code,
    p.port_name,
    p.country,
    f.year,
    f.quarter,
    f.tonnage_mt,
    f.imports_mt,
    f.exports_mt,
    f.teus,
    f.num_vessels,
    q.flag_name as quality_flag,
    f.analysis_note,
    f.data_source,
    f.source_url,
    f.has_tonnage,
    f.has_teus,
    f.extraction_date,
    f.created_at
FROM fact_port_traffic f
JOIN dim_port p ON f.port_id = p.port_id
LEFT JOIN dim_quality_flag q ON f.quality_flag_id = q.flag_id
ORDER BY p.port_code, f.year, f.quarter;

COMMENT ON VIEW v_port_traffic_full IS 'Vue consolidée - Données avec contexte complet';

-- Vue 2: Résumé annuel par port
CREATE OR REPLACE VIEW v_port_annual_summary AS
SELECT 
    p.port_code,
    p.port_name,
    p.country,
    f.year,
    COUNT(*) as num_records,
    SUM(f.tonnage_mt) as total_tonnage_mt,
    AVG(f.tonnage_mt) as avg_tonnage_mt,
    SUM(CASE WHEN f.teus IS NOT NULL THEN f.teus ELSE 0 END) as total_teus,
    SUM(CASE WHEN q.flag_name = 'VERIFIED' THEN 1 ELSE 0 END) as verified_records,
    SUM(CASE WHEN q.flag_name = 'ESTIMATED' THEN 1 ELSE 0 END) as estimated_records
FROM fact_port_traffic f
JOIN dim_port p ON f.port_id = p.port_id
LEFT JOIN dim_quality_flag q ON f.quality_flag_id = q.flag_id
GROUP BY p.port_code, p.port_name, p.country, f.year
ORDER BY p.port_code, f.year;

COMMENT ON VIEW v_port_annual_summary IS 'Vue annuelle - Résumés par port et année';

-- Vue 3: Disponibilité des indicateurs
CREATE OR REPLACE VIEW v_indicator_availability AS
SELECT 
    p.port_code,
    p.port_name,
    f.year,
    COUNT(*) as total_records,
    SUM(CASE WHEN f.has_tonnage THEN 1 ELSE 0 END) as records_with_tonnage,
    SUM(CASE WHEN f.has_teus THEN 1 ELSE 0 END) as records_with_teus,
    SUM(CASE WHEN f.has_tonnage AND f.has_teus THEN 1 ELSE 0 END) as records_with_both
FROM fact_port_traffic f
JOIN dim_port p ON f.port_id = p.port_id
GROUP BY p.port_code, p.port_name, f.year
ORDER BY p.port_code, f.year;

COMMENT ON VIEW v_indicator_availability IS 'Vue disponibilité - Quels ports ont quels indicateurs';

-- ============================================================================
-- FONCTIONS UTILITAIRES
-- ============================================================================

-- Fonction: Mise à jour timestamp
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Updated_at sur fact_port_traffic
CREATE TRIGGER trg_fact_port_traffic_update
    BEFORE UPDATE ON fact_port_traffic
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- ============================================================================
-- VALIDATION SCHEMA
-- ============================================================================

-- Tables créées
SELECT 
    schemaname,
    tablename
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY tablename;