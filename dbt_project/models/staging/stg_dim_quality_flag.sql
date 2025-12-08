{{ config(
    materialized='view',
    schema='staging',
    tags=['staging', 'dimensions']
) }}

select
    flag_id,
    flag_name,
    flag_description,
    severity
from {{ source('raw', 'dim_quality_flag') }}
where flag_id is not null