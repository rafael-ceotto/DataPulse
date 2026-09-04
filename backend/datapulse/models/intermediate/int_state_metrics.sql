with hospital_quality as (
    select * from {{ ref('int_hospital_quality') }}
)

select
    state,
    count(facility_id)                                    as total_hospitals,
    count(case when overall_rating is not null then 1 end) as rated_hospitals,
    round(avg(overall_rating)::numeric, 2)                as avg_rating,
    count(case when overall_rating >= 4 then 1 end)       as high_rated_count,
    count(case when overall_rating <= 2 then 1 end)       as low_rated_count,
    sum(total_infection_measures)                          as total_infection_measures,
    sum(infection_worse_count)                             as total_worse_infections,
    sum(infection_better_count)                            as total_better_infections,
    round(
        count(case when overall_rating is not null then 1 end)::numeric
        / nullif(count(facility_id), 0) * 100, 1
    )                                                      as completeness_pct
from hospital_quality
group by state