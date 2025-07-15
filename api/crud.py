# my_project/crud.py

from typing import List, Dict, Any
import psycopg2
from psycopg2 import sql
from schemas import ProductMention, ChannelActivity, MessageSearchResult
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def get_top_products(db_conn: psycopg2.extensions.connection, limit: int = 10) -> List[ProductMention]:
    """
    Retrieves the top N most frequently mentioned products from fct_messages.
    This assumes you have a way to extract product names from message_text,
    or a separate dim_products table linked to fct_messages.
    For simplicity, we'll extract common words as "products" for now.
    A more robust solution would involve NLP or a dedicated product dimension.
    """
    cursor = db_conn.cursor()
    try:
        # This query is a placeholder. You'll need to define what constitutes a "product"
        # and how to count mentions from your fct_messages table.
        # For demonstration, let's count occurrences of words, excluding common ones.
        query = sql.SQL("""
            SELECT
                word AS product_name,
                COUNT(*) AS mention_count
            FROM (
                SELECT
                    UNNEST(STRING_TO_ARRAY(LOWER(message_text), ' ')) AS word
                FROM raw.fct_messages
                WHERE message_text IS NOT NULL AND message_text != ''
            ) AS words
            WHERE word NOT IN ('the', 'a', 'an', 'and', 'or', 'in', 'on', 'at', 'for', 'to', 'is', 'it', 'with', 'from', 'this', 'that', 'we', 'you', 'i', 'of', 'be', 'are', 'was', 'were', 'has', 'have', 'had', 'do', 'does', 'did', 'not', 'but', 'so', 'if', 'then', 'else', 'when', 'where', 'how', 'what', 'why', 'who', 'which', 'can', 'will', 'would', 'should', 'could', 'get', 'go', 'come', 'take', 'make', 'give', 'see', 'find', 'know', 'say', 'tell', 'ask', 'show', 'try', 'call', 'mean', 'become', 'leave', 'put', 'begin', 'seem', 'help', 'talk', 'turn', 'start', 'run', 'move', 'like', 'want', 'need', 'feel', 'think', 'believe', 'hope', 'wish', 'expect', 'remember', 'understand', 'consider', 'allow', 'let', 'decide', 'happen', 'provide', 'bring', 'send', 'receive', 'return', 'change', 'follow', 'stop', 'open', 'close', 'read', 'write', 'play', 'watch', 'listen', 'look', 'hear', 'meet', 'join', 'build', 'create', 'develop', 'design', 'manage', 'control', 'improve', 'increase', 'decrease', 'reduce', 'add', 'remove', 'use', 'find', 'get', 'give', 'keep', 'let', 'make', 'put', 'seem', 'take', 'tell', 'think', 'try', 'turn', 'understand', 'want', 'work', 'would', 'write', 'go', 'come', 'say', 'see', 'know', 'look', 'find', 'give', 'tell', 'ask', 'show', 'try', 'call', 'mean', 'become', 'leave', 'put', 'begin', 'seem', 'help', 'talk', 'turn', 'start', 'run', 'move', 'like', 'want', 'need', 'feel', 'think', 'believe', 'hope', 'wish', 'expect', 'remember', 'understand', 'consider', 'allow', 'let', 'decide', 'happen', 'provide', 'bring', 'send', 'receive', 'return', 'change', 'follow', 'stop', 'open', 'close', 'read', 'write', 'play', 'watch', 'listen', 'look', 'hear', 'meet', 'join', 'build', 'create', 'develop', 'design', 'manage', 'control', 'improve', 'increase', 'decrease', 'reduce', 'add', 'remove', 'use', 'find', 'get', 'give', 'keep', 'let', 'make', 'put', 'seem', 'take', 'tell', 'think', 'try', 'turn', 'understand', 'want', 'work', 'would', 'write')
                AND LENGTH(word) > 2 
            GROUP BY 1
            ORDER BY mention_count DESC
            LIMIT %s;
        """)
        cursor.execute(query, (limit,))
        results = cursor.fetchall()

        return [ProductMention(product_name=row[0], mention_count=row[1]) for row in results]
    except psycopg2.Error as e:
        logging.error(f"Error fetching top products: {e}")
        raise
    finally:
        cursor.close()

def get_channel_activity(db_conn: psycopg2.extensions.connection, channel_name: str) -> List[ChannelActivity]:
    """
    Returns the posting activity for a specific channel, aggregated by day.
    Queries fct_messages and dim_channels.
    """
    cursor = db_conn.cursor()
    try:
        query = sql.SQL("""
            SELECT
                TO_CHAR(fm.message_timestamp, 'YYYY-MM-DD') AS activity_date,
                COUNT(fm.message_id) AS message_count
            FROM raw.fct_messages fm 
            JOIN raw.dim_channels dc ON fm.channel_id = dc.channel_id
            WHERE dc.channel_name ILIKE %s
            GROUP BY 1
            ORDER BY 1;
        """)
        cursor.execute(query, (channel_name,))
        results = cursor.fetchall()

        return [ChannelActivity(activity_date=row[0], message_count=row[1]) for row in results]
    except psycopg2.Error as e:
        logging.error(f"Error fetching channel activity for {channel_name}: {e}")
        raise
    finally:
        cursor.close()

def search_messages(db_conn: psycopg2.extensions.connection, query_text: str) -> List[MessageSearchResult]:
    """
    Searches for messages containing a specific keyword in fct_messages.
    """
    cursor = db_conn.cursor()
    try:
        # Using ILIKE for case-insensitive search
        search_pattern = f"%{query_text.lower()}%"
        query = sql.SQL("""
            SELECT
                fm.message_id,
                dc.channel_name,
                fm.message_timestamp,
                fm.message_text
            FROM raw.fct_messages fm 
            JOIN raw.dim_channels dc ON fm.channel_id = dc.channel_id
            WHERE LOWER(fm.message_text) ILIKE %s
            ORDER BY fm.message_timestamp DESC
            LIMIT 100; 
        """)
        cursor.execute(query, (search_pattern,))
        results = cursor.fetchall()

        return [
            MessageSearchResult(
                message_id=row[0],
                channel_name=row[1],
                message_timestamp=row[2],
                message_text=row[3]
            ) for row in results
        ]
    except psycopg2.Error as e:
        logging.error(f"Error searching messages for '{query_text}': {e}")
        raise
    finally:
        cursor.close()