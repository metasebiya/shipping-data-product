-- models/staging/stg_telegram_messages.sql
-- Materialize as a view for development, can be table later for performance if needed
{{ config(
    materialized='view'
) }}

WITH raw_messages_extracted AS (
    SELECT
        id AS raw_message_id,
        channel_name,
        message_date,
        -- Extract relevant fields from the JSONB object
        -- Assuming each 'message_json' contains an array of messages, and we need to UNNEST them.
        -- If message_json is a single message object, adjust this part.
        -- Based on your `data_loader.py`, `message_json` contains a JSON array of message objects.
        jsonb_array_elements(message_json) AS message_data,
        loaded_at
    FROM {{ source('raw', 'telegram_messages') }}
),
final AS (
    SELECT
        raw_message_id,
        channel_name,
        message_date,
        (message_data ->> 'id')::BIGINT AS message_id,          -- Unique ID of the message within the channel
        (message_data ->> 'text')::TEXT AS message_text,       -- The message content
        (message_data ->> 'date')::TIMESTAMP AS message_timestamp, -- The actual timestamp of the message
        (message_data ->> 'views')::BIGINT AS views_count,       -- Number of views
        (message_data ->> 'has_media')::BOOLEAN AS has_media,   -- Does the message contain media?
        -- Extract file_id if media exists and is a photo (for YOLO later)
        CASE
            WHEN (message_data -> 'media' ->> 'type') = 'photo'
            THEN (message_data -> 'media' ->> 'file_id')::TEXT
            ELSE NULL
        END AS photo_file_id,
        loaded_at -- When this raw record was loaded into our raw layer
    FROM raw_messages_extracted
    WHERE message_data IS NOT NULL -- Ensure we only process valid message data
)

SELECT * FROM final