from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import openai
from fastapi.middleware.cors import CORSMiddleware
import certifi



# Load environment variables
load_dotenv()

# MongoDB Connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(os.getenv("MONGO_URI"), tlsCAFile=certifi.where())
db = client["memories"]
collection = db["incidents"]

# Test MongoDB Connection
try:
    client.admin.command('ping')
    print("✅ Successfully connected to MongoDB!")
except Exception as e:
    print("❌ MongoDB Connection Error:", e)

# Initialize FastAPI
app = FastAPI()

# Enable CORS (for frontend communication)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenAI API Key (Ensure it's set in your `.env` file)
openai.api_key = os.getenv("OPENAI_API_KEY")
MODEL = "gpt-4o"

# Pydantic Model for Incident
class Incident(BaseModel):
    user_id: str
    date: str
    description: str
    emotion: str = None
    tags: list[str] = []

# Route to add an incident
@app.post("/incidents/")
async def add_incident(incident: Incident):
    try:
        collection.insert_one(incident.model_dump())
        return {"message": "Incident added successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Route to fetch user incidents
@app.get("/incidents/{user_id}")
async def get_incidents(user_id: str):
    incidents = list(collection.find({"user_id": user_id}, {"_id": 0}))
    if not incidents:
        raise HTTPException(status_code=404, detail="No incidents found")
    return incidents

# Route to generate a story using OpenAI
@app.get("/generate_story/{user_id}")
async def generate_story(user_id: str):
    incidents = list(collection.find({"user_id": user_id}, {"_id": 0, "description": 1, "date": 1}))

    if not incidents:
        raise HTTPException(status_code=404, detail="No incidents found")

    # Construct a story prompt
    story_prompt = "Remember when...\n"
    for incident in incidents:
        story_prompt += f"- On {incident['date']}, {incident['description']}.\n"

    # Generate the story using OpenAI
    try:
        response = openai.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "Create a nostalgic and engaging story based on these memories."},
                {"role": "user", "content": story_prompt}
            ]
        )
        story = response.choices[0].message.content
        return {"title": "Remember When...", "story": story}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
