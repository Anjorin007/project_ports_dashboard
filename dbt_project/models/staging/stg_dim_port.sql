{{ config(
    materialized='view',
    schema='staging',
    tags=['staging', 'dimensions']
) }}

select
    port_id,
    port_code,
    port_name,
    country,
    region,
    created_at
from {{ source('raw', 'dim_port') }}
where port_id is not null