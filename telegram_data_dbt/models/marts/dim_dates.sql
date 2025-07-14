-- models/marts/dim_dates.sql
{{ config(
    materialized='table',
    unique_key='date_day'
) }}

WITH date_spine AS (
    -- Generates a series of dates. Adjust start_date and end_date as needed.
    SELECT generate_series(
        '2023-01-01'::date, -- Start date (adjust as per your data range)
        current_date + interval '1 year', -- End date (e.g., extend a year into the future)
        '1 day'::interval
    )::date AS date_day
),
final AS (
    SELECT
        date_day,
        EXTRACT(YEAR FROM date_day) AS year,
        EXTRACT(MONTH FROM date_day) AS month,
        TO_CHAR(date_day, 'Month') AS month_name,
        EXTRACT(DAY FROM date_day) AS day_of_month,
        EXTRACT(DOW FROM date_day) AS day_of_week, -- 0=Sunday, 6=Saturday
        TO_CHAR(date_day, 'Day') AS day_of_week_name,
        EXTRACT(DOY FROM date_day) AS day_of_year,
        EXTRACT(WEEK FROM date_day) AS week_of_year,
        EXTRACT(QUARTER FROM date_day) AS quarter,
        TO_CHAR(date_day, 'YYYY-MM') AS year_month,
        -- Add more date attributes as needed (e.g., is_weekend, fiscal_period)
        CASE
            WHEN EXTRACT(DOW FROM date_day) IN (0, 6) THEN TRUE
            ELSE FALSE
        END AS is_weekend
    FROM date_spine
)

SELECT * FROM final
ORDER BY date_day