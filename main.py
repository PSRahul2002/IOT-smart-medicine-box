from fastapi import FastAPI, Request, HTTPException
from pymongo import MongoClient
from datetime import datetime, timezone
import os

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://Rahul:qwerty123456@cluster0.n8whb.mongodb.net/IOT?tlsAllowInvalidCertificates=true") 
DB_NAME = "IOT"
COLLECTION_NAME = "terminal-data"

# Initialize FastAPI app and MongoDB client
app = FastAPI()
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# Helper function to save a message to MongoDB
def save_to_db(data: dict):
    data["timestamp"] = datetime.now(timezone.utc)  # Add a timestamp for when the message was received
    result = collection.insert_one(data)
    return str(result.inserted_id)

# Root endpoint to check server health
@app.get("/")
async def root():
    return {"message": "Smart Medicine Box API is running!"}

# Endpoint to receive messages from the IoT device
@app.post("/api/messages")
async def receive_message(request: Request):
    try:
        data = await request.json()
        if not isinstance(data, dict):
            raise HTTPException(status_code=400, detail="Invalid JSON payload")

        # Save to MongoDB
        message_id = save_to_db(data)
        return {"message": "Data saved successfully", "id": message_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint to query messages
@app.get("/api/messages")
async def query_messages(
    key: str = None,
    value: str = None,
    start_date: str = None,
    end_date: str = None,
    limit: int = 10
):
    """
    Query messages with optional filters:
    - key: Filter by a specific key (e.g., 'temperature', 'lid_status').
    - value: Filter by a specific value (e.g., 'open', '30.5').
    - start_date, end_date: Filter by date range (format: YYYY-MM-DD).
    - limit: Limit the number of results (default: 10).
    """
    query = {}

    # Add filters based on query parameters
    if key and value:
        query[key] = value
    if start_date:
        query["timestamp"] = {"$gte": datetime.fromisoformat(start_date)}
    if end_date:
        query["timestamp"] = query.get("timestamp", {})
        query["timestamp"]["$lte"] = datetime.fromisoformat(end_date)

    # Fetch messages from MongoDB
    messages = collection.find(query).sort("timestamp", -1).limit(limit)
    result = [
        {
            "id": str(message["_id"]),
            "data": {k: v for k, v in message.items() if k not in ["_id", "timestamp"]},
            "timestamp": message["timestamp"]
        }
        for message in messages
    ]

    return {"count": len(result), "messages": result}