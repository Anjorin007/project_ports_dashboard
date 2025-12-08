

with traffic_data as (
    select
        port_id,
        year,
        tonnage_mt,
        teus,
        num_vessels,
        has_tonnage,
        has_teus,
        quality_flag_id
    from "ports_dashboard"."public_staging"."stg_port_traffic"
),

port_info as (
    select * from "ports_dashboard"."public_staging"."stg_dim_port"
),

annual_stats as (
    select
        t.port_id,
        p.port_code,
        p.port_name,
        p.country,
        t.year,
        sum(t.tonnage_mt) as total_tonnage_mt,
        avg(t.tonnage_mt) as avg_tonnage_mt,
        sum(t.teus) as total_teus,
        sum(t.num_vessels) as total_vessels,
        count(*) as num_records,
        sum(case when t.has_tonnage then 1 else 0 end) as records_with_tonnage,
        sum(case when t.has_teus then 1 else 0 end) as records_with_teus,
        current_timestamp as created_at
    from traffic_data t
    join port_info p on t.port_id = p.port_id
    group by t.port_id, p.port_code, p.port_name, p.country, t.year
)

select * from annual_stats