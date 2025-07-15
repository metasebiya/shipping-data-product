{{ config(
    materialized='incremental',
    unique_key=['image_path', 'detected_class', 'message_id'],
    on_schema_change='append_new_columns'
) }}

WITH raw_detections AS (
    SELECT
        id AS raw_detection_id,
        image_path,
        message_id,
        channel_name,
        detected_class,
        confidence_score,
        detection_bbox,
        processed_at
    FROM {{ source('raw', 'image_detections') }}
    {% if is_incremental() %}
      -- Only process new detections since the last run
      WHERE processed_at > (SELECT MAX(processed_at) FROM {{ this }})
    {% endif %}
),
-- Optional: Join with fct_messages to pull in more context or validate linkage
joined_detections AS (
    SELECT
        rd.raw_detection_id,
        rd.image_path,
        rd.detected_class,
        rd.confidence_score,
        rd.detection_bbox,
        rd.processed_at,
        fm.message_surrogate_key, -- Link to the fact_messages table
        fm.message_id AS telegram_message_id, -- Original telegram message ID
        fm.channel_id,            -- Link to dim_channels
        fm.message_timestamp,
        fm.message_text
    FROM raw_detections rd
    LEFT JOIN {{ ref('fct_messages') }} fm
        ON rd.message_id = fm.message_id
        -- AND rd.channel_name = fm.channel_name -- Add this if channel_name is reliable in both to prevent false joins
        -- NOTE: The linkage on message_id might be tricky if message_id isn't globally unique.
        -- If telegram's message_id is only unique within a channel, you'll need (message_id, channel_id) for the join.
        -- For now, relying on message_id from the image path for simplicity.
        -- Better: Store telegram's photo_file_id with the image path to join directly to fct_messages
)
SELECT * FROM joined_detections