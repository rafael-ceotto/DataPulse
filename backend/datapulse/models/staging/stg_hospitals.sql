with source as (
    select * from {{ source('datapulse', 'hospitals') }}
),

cleaned as (
    select
        facility_id,
        facility_name,
        address,
        city,
        state,
        zip_code,
        hospital_type,
        hospital_ownership,
        emergency_services,
        overall_rating,
        telephone_number
    from source
    where facility_id is not null
      and facility_name is not null
)

select * from cleaned