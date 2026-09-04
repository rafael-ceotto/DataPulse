with state_metrics as (
    select * from {{ ref('int_state_metrics') }}
),

pipeline_runs as (
    select
        avg_rating as latest_avg_rating,
        started_at as last_run_at
    from {{ ref('stg_pipeline_runs') }}
    order by started_at desc
    limit 1
)

select
    s.state,
    s.total_hospitals,
    s.rated_hospitals,
    s.avg_rating,
    s.high_rated_count,
    s.low_rated_count,
    s.completeness_pct,
    s.total_infection_measures,
    s.total_worse_infections,
    s.total_better_infections,
    case
        when s.total_infection_measures = 0 then null
        else round(
            s.total_better_infections::numeric / s.total_infection_measures * 100, 1
        )
    end as infection_better_pct,
    p.latest_avg_rating,
    p.last_run_at
from state_metrics s
cross join pipeline_runs p