{{ config(  
    materialized='table', 
    unique_key='channel_id'
) }}

WITH stg_channels AS (
    SELECT DISTINCT
        channel_name,
        -- Generate a surrogate key for the channel dimension
        {{ dbt_utils.generate_surrogate_key(['channel_name']) }} AS channel_id
    FROM {{ ref('stg_telegram_messages') }}
)

SELECT
    channel_id,
    channel_name
FROM stg_channels


