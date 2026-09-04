with hospital_quality as (
    select * from {{ ref('int_hospital_quality') }}
)

select
    facility_id,
    facility_name,
    city,
    state,
    hospital_type,
    hospital_ownership,
    emergency_services,
    overall_rating,
    case
        when overall_rating = 5 then 'Excellent'
        when overall_rating = 4 then 'Good'
        when overall_rating = 3 then 'Average'
        when overall_rating <= 2 then 'Below Average'
        else 'Unrated'
    end as rating_category,
    total_infection_measures,
    infection_worse_count,
    infection_better_count,
    infection_average_count,
    case
        when total_infection_measures = 0 then null
        else round(
            infection_better_count::numeric / total_infection_measures * 100, 1
        )
    end as infection_better_pct
from hospital_quality