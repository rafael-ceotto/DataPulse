with source as(
    select * from {{source('datapulse', 'hospital_infections')}}
),

cleaned as(
    select
        id,
        facility_id,
        facility_name,
        state,
        measure_id,
        measure_name,
        compared_to_national,
        score,
        start_date,
        end_date,
        case
            when compared_to_national = 'Worse than the National Benchmark' then 'worse'
            when compared_to_national = 'Better than the National Benchmark' then 'better'
        end as benchmark_category
    from source
    where facility_id is not null
)

select * from cleaned