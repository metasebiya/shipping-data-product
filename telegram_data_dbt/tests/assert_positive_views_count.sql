-- tests/assert_positive_views_count.sql
-- This singular test will return rows where views_count is less than 0.
-- If any rows are returned, the test fails.
SELECT
    message_surrogate_key,
    views_count
FROM {{ ref('fct_messages') }}
WHERE views_count < 0