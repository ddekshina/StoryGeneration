from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi import Request
import os
import openai
import random
import uuid
from typing import Optional, List
from datetime import datetime
import certifi
from fastapi.responses import FileResponse

# Load environment variables
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("App is starting up...")
    yield
    print("App is shutting down...")

# Initialize FastAPI with lifespan only once
app = FastAPI(
    title="Memory Weaver API",
    description="Backend for memory story generation application",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class Memory(BaseModel):
    user_id: str
    date: str
    description: str
    tags: List[str] = []
    mood: Optional[str] = None
    location: Optional[str] = None
    created_at: Optional[datetime] = None

class StoryResponse(BaseModel):
    title: str
    story: str
    audio_url: Optional[str] = None
    image_url: Optional[str] = None
    tags_used: List[str] = []
    mood: Optional[str] = None

class StoryGenerationRequest(BaseModel):
    user_id: str
    tone: Optional[str] = "heartwarming"
    include_tags: Optional[List[str]] = None
    max_length: Optional[int] = 500

# Database Connection
def get_mongo_client():
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    
    try:
        print(f"Attempting to connect to MongoDB with URI: {MONGO_URI}")
        client = MongoClient(
            MONGO_URI,
            tlsCAFile=certifi.where(),
            connectTimeoutMS=5000,
            serverSelectionTimeoutMS=5000
        )
        client.admin.command('ping')
        print("✅ Successfully connected to MongoDB!")
        
        # List all databases
        print("Available databases:", client.list_database_names())
        return client
    except OperationFailure as auth_error:
        print(f"🔒 Authentication failed: {auth_error}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="MongoDB authentication failed"
        )
    except ConnectionFailure as conn_error:
        print(f"🔌 Connection failed: {conn_error}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not connect to MongoDB"
        )
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection error"
        )

# Initialize database connection
try:
    client = get_mongo_client()
    db = client["memory_weaver"]
    memories_collection = db["memories"]
    
    # Create indexes for better query performance
    memories_collection.create_index([("user_id", 1)])
    memories_collection.create_index([("created_at", -1)])
    memories_collection.create_index([("tags", 1)])
    memories_collection.create_index([("mood", 1)])
    
    print("✅ Database indexes created successfully!")
    print(f"Current collection count: {memories_collection.count_documents({})}")
except Exception as e:
    print(f"Failed to initialize database: {e}")
    raise

# Initialize OpenAI if API key exists
openai.api_key = os.getenv("OPENAI_API_KEY")

# Helper Functions
def initialize_user_collection(user_id: str):
    """Ensure user document exists with proper schema"""
    if not memories_collection.find_one({"user_id": user_id}):
        memories_collection.insert_one({
            "user_id": user_id,
            "memories": [],
            "created_at": datetime.utcnow(),
            "last_updated": datetime.utcnow()
        })

def get_user_memories_optimized(user_id: str, limit: int = 100):
    """Optimized function to get user memories with pagination"""
    return memories_collection.find_one(
        {"user_id": user_id},
        {
            "memories": {
                "$slice": ["$memories", limit]
            }
        }
    )

def get_memories_by_tags(user_id: str, tags: List[str]):
    """Get memories filtered by tags"""
    return memories_collection.find_one(
        {
            "user_id": user_id,
            "memories.tags": {"$in": tags}
        },
        {"_id": 0}
    )

# API Endpoints
@app.options("/memories/", include_in_schema=False)
async def options_memories():
    return {"message": "OK"}

@app.options("/memories/{user_id}", include_in_schema=False)
async def options_user_memories(user_id: str):
    return {"message": "OK"}

@app.options("/generate-story/", include_in_schema=False)
async def options_generate_story():
    return {"message": "OK"}
@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    print(f"Response status: {response.status_code}")
    return response

@app.post("/memories/", status_code=status.HTTP_201_CREATED)
async def create_memory(memory: Memory):
    """Add a new memory for a user"""
    try:
        print(f"Creating new memory for user: {memory.user_id}")
        memory_dict = memory.dict()
        memory_dict["created_at"] = datetime.utcnow()
        print("Memory data to insert:", memory_dict)
        
        # Check if user document exists
        user_doc = memories_collection.find_one({"user_id": memory.user_id})
        print(f"Existing user document: {user_doc}")
        
        # Using update_one with upsert for better structure
        result = memories_collection.update_one(
            {"user_id": memory.user_id},
            {
                "$push": {"memories": memory_dict},
                "$setOnInsert": {
                    "created_at": datetime.utcnow(),
                    "last_updated": datetime.utcnow()
                }
            },
            upsert=True
        )
        
        print(f"Update result: modified={result.modified_count}, upserted={result.upserted_id}")
        
        # Verify the update
        updated_doc = memories_collection.find_one({"user_id": memory.user_id})
        print(f"Updated document: {updated_doc}")
        
        if result.modified_count == 1 or result.upserted_id:
            return {"message": "Memory added successfully", "memory": memory_dict}
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to add memory"
        )
    except Exception as e:
        print(f"Error creating memory: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/memories/")
async def get_all_memories():
    """Get all memories from all users (for debugging)"""
    try:
        print("Attempting to fetch all memories...")
        memories = list(memories_collection.find({}, {"_id": 0}))
        print(f"Found {len(memories)} memories in database")
        print("Memory data:", memories)
        return {"memories": memories}
    except Exception as e:
        print(f"Error fetching memories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/memories/{user_id}")
async def get_user_memories(user_id: str):
    """Get all memories for a specific user"""
    try:
        print(f"Fetching memories for user_id: {user_id}")
        user_data = memories_collection.find_one({"user_id": user_id})
        print(f"User data found: {user_data}")
        if not user_data or not user_data.get("memories"):
            print("No memories found for user")
            return {"memories": []}
        print(f"Found {len(user_data['memories'])} memories for user")
        return {"memories": user_data["memories"]}
    except Exception as e:
        print(f"Error fetching user memories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.post("/generate-story/")
async def generate_story(request: StoryGenerationRequest):
    """Generate a creative story from a single random memory with multimedia elements"""
    try:
        # Get user memories
        user_data = get_user_memories_optimized(request.user_id)
        if not user_data or not user_data.get("memories"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No memories found for this user"
            )
        
        # Select one random memory
        memory = random.choice(user_data["memories"])
        print(f"Selected memory: {memory}")

        # Prepare memory context for story generation
        memory_context = (
            f"Date: {memory['date']}\n"
            f"Description: {memory['description']}\n"
            f"Location: {memory.get('location', 'unspecified')}\n"
            f"Mood: {memory.get('mood', 'unspecified')}\n"
            f"Tags: {', '.join(memory.get('tags', []))}"
        )

        # Generate story using OpenAI
        if openai.api_key:
            try:
                # Generate story with specific requirements
                story_prompt = f"""Create a creative and engaging story based on this memory:
                {memory_context}

                Requirements:
                - Length: 300-500 words
                - Style: Engaging narrative with vivid descriptions
                - Tone: {request.tone}
                - Expand creatively beyond the original memory
                - Include sensory details and emotional elements
                - Maintain the core essence of the memory
                - Format the response in Markdown"""

                story_response = openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a creative storyteller who transforms memories into engaging narratives."},
                        {"role": "user", "content": story_prompt}
                    ],
                    temperature=0.8,
                    max_tokens=1000,
                    presence_penalty=0.6,
                    frequency_penalty=0.5
                )
                
                story_content = story_response.choices[0].message.content

                # Generate title
                title_prompt = f"Create a short, engaging title (max 10 words) for this story:\n{story_content}"
                title_response = openai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Create a compelling title that captures the essence of the story."},
                        {"role": "user", "content": title_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=50
                )
                
                # Generate image using DALL-E
                image_prompt = f"""Create a visually striking illustration for this story:
                {story_content}

                Style: Digital art with warm, emotional atmosphere
                Focus on key emotional moments and visual elements
                Use vibrant colors and dynamic composition"""

                image_response = openai.images.generate(
                    prompt=image_prompt,
                    n=1,
                    size="1024x1024",  # Using supported size
                    response_format="url"
                )

                # Generate audio narration
                audio_filename = f"story_{uuid.uuid4()}.mp3"
                audio_response = openai.audio.speech.create(
                    model="tts-1",
                    voice="alloy",  # Using alloy voice for natural sound
                    input=story_content,
                    speed=1.0
                )
                audio_response.stream_to_file(audio_filename)

                # Prepare response
                response = {
                    "title": title_response.choices[0].message.content.strip(),
                    "story": story_content,
                    "image_url": image_response.data[0].url,
                    "audio_url": f"/audio/{audio_filename}",
                    "memory_used": {
                        "date": memory['date'],
                        "description": memory['description'],
                        "location": memory.get('location'),
                        "mood": memory.get('mood'),
                        "tags": memory.get('tags', [])
                    }
                }
                
            except Exception as ai_error:
                print(f"AI generation error: {ai_error}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to generate story: {str(ai_error)}"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OpenAI API key not configured"
            )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Story generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/audio/{filename}")
async def get_audio(filename: str):
    """Serve generated audio files"""
    if not os.path.exists(filename):
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(filename, media_type="audio/mpeg")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        client.admin.command('ping')
        return {"status": "healthy", "database": "connected"}
    except Exception:
        return {"status": "unhealthy", "database": "disconnected"}

# Startup event
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("App is starting up...")
    yield  # This is where your app runs
    print("App is shutting down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)