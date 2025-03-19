from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import openai
import random
from fastapi.middleware.cors import CORSMiddleware
import certifi
from fastapi.responses import FileResponse
from gtts import gTTS
import uuid  # For unique filenames

# Load environment variables
load_dotenv()

# MongoDB Connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client["memories"]
collection = db["incidents"]

# OpenAI API Key
openai.api_key = os.getenv("OPENAI_API_KEY")
MODEL = "gpt-4o"

# Initialize FastAPI
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Model for Incident
class Incident(BaseModel):
    user_id: str
    date: str
    description: str

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

# Route to generate story with audio & image
@app.get("/generate_story/{user_id}")
async def generate_story(user_id: str):
    incidents = list(collection.find({"user_id": user_id}, {"_id": 0, "description": 1, "date": 1}))

    if not incidents:
        raise HTTPException(status_code=404, detail="No incidents found")

    # Select one random memory
    selected_memory = random.choice(incidents)
    
    # Create a nostalgic recap
    story_prompt = f"Turn this memory into a short, warm, and nostalgic recap for a dementia patient:\n\nDate: {selected_memory['date']}\nMemory: {selected_memory['description']}"
    
    try:
        response = openai.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "Gently remind the user of this past moment in a warm and reassuring tone. Keep it simple, clear, and nostalgic, as if speaking to someone with memory difficulties. Use 4-5 short sentences."},
                {"role": "user", "content": story_prompt}
            ]
        )
        story = response.choices[0].message.content

        # 🎙 Generate Audio
        audio_filename = f"story_{uuid.uuid4()}.mp3"
        tts = gTTS(text=story, lang="en")
        tts.save(audio_filename)

        # 🖼 Generate Image (DALL-E)
        dalle_response = openai.images.generate(
            prompt=f"A heartwarming image representing this memory: {selected_memory['description']}",
            model="dall-e-3",
            n=1,
            size="1024x1024"
        )
        image_url = dalle_response.data[0].url

        return {
            "title": "Remember When...",
            "story": story,
            "audio_url": f"http://localhost:8000/{audio_filename}",
            "image_url": image_url
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Serve the generated audio file
@app.get("/{filename}")
async def get_audio(filename: str):
    return FileResponse(filename, media_type="audio/mpeg")
