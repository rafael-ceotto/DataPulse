with hospitals as (
    select * from {{ ref('stg_hospitals') }}
),

infections as (
    select
        facility_id,
        count(*) as total_measures,
        sum(case when benchmark_category = 'worse' then 1 else 0 end) as worse_count,
        sum(case when benchmark_category = 'better' then 1 else 0 end) as better_count,
        sum(case when benchmark_category = 'average' then 1 else 0 end) as average_count
    from {{ ref('stg_infections') }}
    group by facility_id
)

select
    h.facility_id,
    h.facility_name,
    h.city,
    h.state,
    h.hospital_type,
    h.hospital_ownership,
    h.emergency_services,
    h.overall_rating,
    coalesce(i.total_measures, 0)  as total_infection_measures,
    coalesce(i.worse_count, 0)     as infection_worse_count,
    coalesce(i.better_count, 0)    as infection_better_count,
    coalesce(i.average_count, 0)   as infection_average_count
from hospitals h
left join infections i on h.facility_id = i.facility_id