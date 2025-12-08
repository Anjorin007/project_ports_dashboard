

select
    port_id,
    port_code,
    port_name,
    country,
    region,
    created_at
from "ports_dashboard"."public"."dim_port"
where port_id is not null