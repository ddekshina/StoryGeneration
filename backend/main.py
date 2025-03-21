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
import uuid  # For unique filenames

# Load environment variables
load_dotenv()

# MongoDB Connection
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client["dementia"]  # Use the existing database name
collection = db["fileids"]  # The main collection containing the mem_data field

# OpenAI API Key
openai.api_key = os.getenv("OPENAI_API_KEY")
MODEL = "gpt-4o-mini-tts"

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

# Route to fetch user memories
@app.get("/memories/")
async def get_memories():
    user_data = collection.find_one({}, {"_id": 0, "mem_data": 1})  # Fetch only mem_data
    if not user_data or "mem_data" not in user_data:
        raise HTTPException(status_code=404, detail="No memories found")
    return user_data["mem_data"]

# Route to generate story with audio & image
@app.get("/generate_story")
async def generate_story():
    user_data = collection.find_one({}, {"_id": 0, "mem_data": 1})
    if not user_data or "mem_data" not in user_data:
        raise HTTPException(status_code=404, detail="No memories found")

    memories = user_data["mem_data"]
    selected_memory = random.choice(memories)
    
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

        # 🎙 Generate Audio using OpenAI TTS
        audio_filename = f"story_{uuid.uuid4()}.mp3"
        audio_response = openai.audio.speech.create(
            model="tts-1",  # OpenAI's TTS model
            voice="alloy",  # Choose a voice (alloy, echo, fable, onyx, nova, shimmer)
            input=story
        )

        # Save the audio file
        with open(audio_filename, "wb") as audio_file:
            audio_file.write(audio_response.content)

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