
  
    

  create  table "ports_dashboard"."public_marts"."mart_port_trends__dbt_tmp"
  
  
    as
  
  (
    

with annual_data as (
    select
        port_code,
        port_name,
        country,
        year,
        total_tonnage_mt,
        total_teus
    from "ports_dashboard"."public_marts"."mart_port_annual_summary"
),

with_lag as (
    select
        port_code,
        port_name,
        country,
        year,
        total_tonnage_mt,
        total_teus,
        lag(total_tonnage_mt) over (partition by port_code order by year) as prev_tonnage_mt,
        lag(total_teus) over (partition by port_code order by year) as prev_teus,
        round(100.0 * (total_tonnage_mt - lag(total_tonnage_mt) over (partition by port_code order by year)) / nullif(lag(total_tonnage_mt) over (partition by port_code order by year), 0), 2) as tonnage_yoy_pct,
        round(100.0 * (total_teus - lag(total_teus) over (partition by port_code order by year)) / nullif(lag(total_teus) over (partition by port_code order by year), 0), 2) as teu_yoy_pct
    from annual_data
)

select
    port_code,
    port_name,
    country,
    year,
    total_tonnage_mt,
    tonnage_yoy_pct,
    total_teus,
    teu_yoy_pct,
    current_timestamp as created_at
from with_lag
where year > 2020
order by port_code, year
  );
  