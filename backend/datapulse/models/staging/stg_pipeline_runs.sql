with source as (
    select * from {{ source('datapulse','pipeline_runs')}}
),

cleaned as(
    select
        id,
        started_at,
        finished_at,
        status,
        records_received,
        records_processed,
        records_failed,
        avg_rating,
        insight,
        extract(epoch from (finished_at - started_at)) as duration_seconds
    from source
    where status = 'success'
)

select * from cleaned