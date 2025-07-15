# api/schemas.py

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# Schema for a single product mention
class ProductMention(BaseModel):
    product_name: str
    mention_count: int

# Schema for the top products report response
class TopProductsReport(BaseModel):
    products: List[ProductMention]

# Schema for channel activity
class ChannelActivity(BaseModel):
    activity_date: str # Or datetime if you prefer
    message_count: int

# Schema for a single message search result
class MessageSearchResult(BaseModel):
    message_id: int
    channel_name: str
    message_timestamp: datetime
    message_text: str
    # Optional: If you want to include image detection info in message search
    # detected_objects: Optional[List[str]] = None

# Schema for the list of message search results
class MessageSearchResponse(BaseModel):
    query: str
    results: List[MessageSearchResult]

# Optional: Schema for image detection details if you decide to expose them
class ImageDetection(BaseModel):
    detection_id: int
    image_filepath: str
    detected_class: str
    confidence_score: float
    # detection_bbox: List[float] # If you want to expose bounding box