
  create view "ports_dashboard"."public_staging"."stg_port_traffic__dbt_tmp"
    
    
  as (
    -- ============================================================================
-- FILE: models/staging/stg_port_traffic.sql
-- ============================================================================



with source_data as (
    select
        traffic_id,
        port_id,
        quality_flag_id,
        year,
        quarter,
        tonnage_mt,
        imports_mt,
        exports_mt,
        teus,
        num_vessels,
        data_source,
        source_url,
        has_tonnage,
        has_teus,
        analysis_note,
        extraction_date,
        data_notes,
        clean_date,
        created_at,
        updated_at
    from "ports_dashboard"."public"."fact_port_traffic"
    where port_id is not null
        and year is not null
),

enriched as (
    select
        traffic_id,
        port_id,
        quality_flag_id,
        year,
        quarter,
        coalesce(tonnage_mt, 0) as tonnage_mt,
        coalesce(imports_mt, 0) as imports_mt,
        coalesce(exports_mt, 0) as exports_mt,
        coalesce(teus, 0) as teus,
        coalesce(num_vessels, 0) as num_vessels,
        data_source,
        source_url,
        has_tonnage,
        has_teus,
        analysis_note,
        extraction_date,
        data_notes,
        clean_date,
        created_at,
        updated_at,
        case 
            when quarter is not null then 'Q' || quarter
            else 'ANNUAL'
        end as period_type,
        case 
            when has_tonnage and has_teus then 'BOTH_INDICATORS'
            when has_tonnage then 'TONNAGE_ONLY'
            when has_teus then 'TEU_ONLY'
            else 'NO_DATA'
        end as indicator_type
    from source_data
)

select * from enriched
  );