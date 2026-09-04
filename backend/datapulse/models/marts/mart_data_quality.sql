with hospital_quality as (
    select * from {{ ref('int_hospital_quality') }}
),

pipeline_runs as (
    select * from {{ ref('stg_pipeline_runs') }}
)

select
    count(*)                                                    as total_hospitals,
    count(case when overall_rating is not null then 1 end)      as rated_hospitals,
    count(case when overall_rating is null then 1 end)          as unrated_hospitals,
    count(case when overall_rating <= 2 then 1 end)             as low_rated_hospitals,
    round(
        count(case when overall_rating is not null then 1 end)::numeric
        / nullif(count(*), 0) * 100, 1
    )                                                           as completeness_pct,
    (select count(*) from pipeline_runs)                        as total_pipeline_runs,
    (select max(started_at) from pipeline_runs)                 as last_successful_run
from hospital_quality