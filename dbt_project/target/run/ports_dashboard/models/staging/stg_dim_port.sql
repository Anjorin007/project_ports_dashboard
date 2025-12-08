
  create view "ports_dashboard"."public_staging"."stg_dim_port__dbt_tmp"
    
    
  as (
    

select
    port_id,
    port_code,
    port_name,
    country,
    region,
    created_at
from "ports_dashboard"."public"."dim_port"
where port_id is not null
  );