# api/main.py
from fastapi import FastAPI, Depends, HTTPException, Query
from typing import List
import psycopg2
from database import get_db, get_db_connection
from schemas import (
    TopProductsReport,
    ProductMention,
    ChannelActivity,
    MessageSearchResponse,
    MessageSearchResult
)
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Import CRUD operations
from crud import get_top_products, get_channel_activity, search_messages

app = FastAPI(
    title="Telegram Data Product API",
    description="API for analytical insights from Telegram data, powered by dbt and YOLO.",
    version="0.1.0"
)

@app.get("/")
async def root():
    return {"message": "Welcome to the Telegram Data Product API! Visit /docs for API documentation."}

@app.get(
    "/api/reports/top-products",
    response_model=TopProductsReport,
    summary="Get Top Mentioned Products",
    description="Returns a list of the most frequently mentioned 'products' (words) across all messages."
)
async def read_top_products(
    limit: int = Query(10, ge=1, le=100, description="Number of top products to return"),
    db_conn: psycopg2.extensions.connection = Depends(get_db)
):
    """
    Returns the top N most frequently mentioned products.
    """
    try:
        products = get_top_products(db_conn, limit)
        return TopProductsReport(products=products)
    except Exception as e:
        logging.error(f"API Error: Failed to retrieve top products: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while fetching top products.")


@app.get(
    "/api/channels/{channel_name}/activity",
    response_model=List[ChannelActivity],
    summary="Get Channel Posting Activity",
    description="Returns the daily message count for a specific Telegram channel."
)
async def read_channel_activity(
    channel_name: str,
    db_conn: psycopg2.extensions.connection = Depends(get_db)
):
    """
    Returns the posting activity for a specific channel.
    """
    try:
        activity = get_channel_activity(db_conn, channel_name)
        if not activity:
            raise HTTPException(status_code=404, detail=f"No activity found for channel: {channel_name}")
        return activity
    except HTTPException: # Re-raise HTTPExceptions (e.g., 404)
        raise
    except Exception as e:
        logging.error(f"API Error: Failed to retrieve activity for channel {channel_name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while fetching channel activity.")


@app.get(
    "/api/search/messages",
    response_model=MessageSearchResponse,
    summary="Search Messages by Keyword",
    description="Searches for Telegram messages containing a specified keyword."
)
async def search_telegram_messages(
    query: str = Query(..., min_length=2, description="Keyword to search for in message text"),
    db_conn: psycopg2.extensions.connection = Depends(get_db)
):
    """
    Searches for messages containing a specific keyword.
    """
    try:
        results = search_messages(db_conn, query)
        return MessageSearchResponse(query=query, results=results)
    except Exception as e:
        logging.error(f"API Error: Failed to search messages for '{query}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while searching messages.")