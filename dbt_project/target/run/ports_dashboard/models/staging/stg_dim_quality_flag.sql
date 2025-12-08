
  create view "ports_dashboard"."public_staging"."stg_dim_quality_flag__dbt_tmp"
    
    
  as (
    

select
    flag_id,
    flag_name,
    flag_description,
    severity
from "ports_dashboard"."public"."dim_quality_flag"
where flag_id is not null
  );