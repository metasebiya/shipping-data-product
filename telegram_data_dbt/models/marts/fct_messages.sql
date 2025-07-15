{{ config(
    materialized='incremental',
    unique_key='message_surrogate_key',
    on_schema_change='append_new_columns'
) }}

WITH stg_messages AS (
    SELECT *
    FROM {{ ref('stg_telegram_messages') }}
),
dim_channels AS (
    SELECT *
    FROM {{ ref('dim_channels') }}
),
dim_dates AS (
    SELECT *
    FROM {{ ref('dim_dates') }}
),
final AS (
    SELECT
        -- Generate a surrogate key for the fact message
        {{ dbt_utils.generate_surrogate_key(['stg_messages.raw_message_id', 'stg_messages.message_id']) }} AS message_surrogate_key,
        stg_messages.message_id, -- Original message ID from Telegram
        stg_messages.raw_message_id, -- FK to the raw message record
        channels.channel_id,
        dates.date_day AS message_date, -- Use the date from dim_dates
        stg_messages.message_text,
        stg_messages.message_timestamp,
        stg_messages.views_count,
        stg_messages.has_media,
        stg_messages.photo_file_id,
        LENGTH(stg_messages.message_text) AS message_length,
        CASE WHEN stg_messages.message_text ILIKE '%product%' OR stg_messages.message_text ILIKE '%drug%' THEN TRUE ELSE FALSE END AS mentions_product_or_drug,
        stg_messages.loaded_at -- Timestamp when this raw message was loaded into the raw layer
    FROM stg_messages
    LEFT JOIN dim_channels AS channels
        ON stg_messages.channel_name = channels.channel_name
    LEFT JOIN dim_dates AS dates
        ON stg_messages.message_date = dates.date_day
    {% if is_incremental() %}
      -- This tells dbt to only process new raw messages since the last run
      WHERE stg_messages.loaded_at > (SELECT MAX(loaded_at) FROM {{ this }})
    {% endif %}
)

SELECT * FROM final