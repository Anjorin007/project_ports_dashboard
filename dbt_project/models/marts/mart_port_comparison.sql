{{ config(
    materialized='table',
    schema='marts',
    tags=['marts', 'comparison']
) }}

with latest_year_data as (
    select
        port_id,
        port_code,
        port_name,
        country,
        year,
        total_tonnage_mt,
        total_teus
    from {{ ref('mart_port_annual_summary') }}
    where year = (select max(year) from {{ ref('mart_port_annual_summary') }})
),

market_share as (
    select
        port_code,
        port_name,
        country,
        year,
        total_tonnage_mt,
        total_teus,
        round(100.0 * total_tonnage_mt / nullif(sum(total_tonnage_mt) over (), 0), 2) as tonnage_market_share_pct,
        round(100.0 * total_teus / nullif(sum(total_teus) over (), 0), 2) as teu_market_share_pct,
        rank() over (order by total_tonnage_mt desc) as tonnage_rank,
        rank() over (order by total_teus desc) as teu_rank
    from latest_year_data
)

select * from market_share
order by tonnage_rank