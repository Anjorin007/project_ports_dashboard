-- Crée schéma
CREATE SCHEMA IF NOT EXISTS marts;

-- Crée mart_port_annual_summary
CREATE TABLE marts.mart_port_annual_summary AS
SELECT 
    p.port_id,
    p.port_code,
    p.port_name,
    p.country,
    f.year,
    SUM(f.tonnage_mt) as total_tonnage_mt,
    AVG(f.tonnage_mt) as avg_tonnage_mt,
    SUM(f.teus) as total_teus,
    COUNT(*) as num_records,
    SUM(CASE WHEN f.has_tonnage THEN 1 ELSE 0 END) as records_with_tonnage,
    SUM(CASE WHEN f.has_teus THEN 1 ELSE 0 END) as records_with_teus
FROM fact_port_traffic f
JOIN dim_port p ON f.port_id = p.port_id
GROUP BY p.port_id, p.port_code, p.port_name, p.country, f.year;

-- Crée mart_port_comparison
CREATE TABLE marts.mart_port_comparison AS
SELECT 
    port_code,
    port_name,
    country,
    year,
    total_tonnage_mt,
    total_teus,
    ROUND(100.0 * total_tonnage_mt / NULLIF(SUM(total_tonnage_mt) OVER (), 0), 2) as tonnage_market_share_pct,
    ROUND(100.0 * total_teus / NULLIF(SUM(total_teus) OVER (), 0), 2) as teu_market_share_pct,
    RANK() OVER (ORDER BY total_tonnage_mt DESC) as tonnage_rank,
    RANK() OVER (ORDER BY total_teus DESC) as teu_rank
FROM marts.mart_port_annual_summary
WHERE year = (SELECT MAX(year) FROM marts.mart_port_annual_summary);

-- Crée mart_port_trends
CREATE TABLE marts.mart_port_trends AS
SELECT 
    port_code,
    port_name,
    country,
    year,
    total_tonnage_mt,
    LAG(total_tonnage_mt) OVER (PARTITION BY port_code ORDER BY year) as prev_tonnage_mt,
    ROUND(100.0 * (total_tonnage_mt - LAG(total_tonnage_mt) OVER (PARTITION BY port_code ORDER BY year))
        / NULLIF(LAG(total_tonnage_mt) OVER (PARTITION BY port_code ORDER BY year), 0), 2) as tonnage_yoy_pct,
    total_teus,
    LAG(total_teus) OVER (PARTITION BY port_code ORDER BY year) as prev_teus
FROM marts.mart_port_annual_summary
WHERE year > 2020;

-- Crée mart_data_quality
CREATE TABLE marts.mart_data_quality AS
SELECT 
    port_code,
    port_name,
    country,
    year,
    records_with_tonnage,
    records_with_teus,
    num_records,
    ROUND(100.0 * records_with_tonnage / NULLIF(num_records, 0), 2) as tonnage_coverage_pct,
    ROUND(100.0 * records_with_teus / NULLIF(num_records, 0), 2) as teu_coverage_pct,
    CASE
        WHEN records_with_tonnage > 0 THEN 'HIGH'
        WHEN records_with_teus > 0 THEN 'MEDIUM'
        ELSE 'LOW'
    END as quality_level
FROM marts.mart_port_annual_summary;