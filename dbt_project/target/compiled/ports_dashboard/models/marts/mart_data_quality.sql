

select
    port_code,
    port_name,
    country,
    year,
    records_with_tonnage,
    records_with_teus,
    num_records,
    round(100.0 * records_with_tonnage / nullif(num_records, 0), 2) as tonnage_coverage_pct,
    round(100.0 * records_with_teus / nullif(num_records, 0), 2) as teu_coverage_pct,
    case
        when records_with_tonnage > 0 then 'HIGH'
        when records_with_teus > 0 then 'MEDIUM'
        else 'LOW'
    end as quality_level
from "ports_dashboard"."public_marts"."mart_port_annual_summary"
order by port_code, year