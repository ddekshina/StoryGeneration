# StoryGeneration
This project implements a web application for managing user memories and generating stories based on those memories using OpenAI's API. The application allows users to store and retrieve memories, generate stories related to a selected memory, and displays the generated content.

## Idea

The project provides a platform for users to create and store memories, along with a mechanism to generate creative stories based on these memories using AI.

## Features

*   **Memory Management:** Allows users to create, store, and retrieve memories.
*   **Story Generation:** Generates creative stories, titles, and potentially images and audio based on user memories, leveraging the OpenAI API.
*   **User Interface:** Contains a front-end component (`RememberWhen`) that fetches a story from a backend service.
*   **Tagging System:** Enables users to tag or categorize memories.
*   **Error Handling:** Includes error handling for API calls and database interactions.
*   **API Endpoints:**
    *   `/memories/{userId}`: Fetches memories for a user.
    *   `/memories/`: Posts a new memory.
    *   `/generate-story/`: Posts a request to generate a story.
    *   `/generate`: Generates story using OpenAI API.
    *   `/audio/{filename}`: Serves generated audio files.
    *   `/health`: Health check endpoint.
*   **CORS Handling:**  Configured to allow cross-origin requests from any domain.
*   **Logging:** Includes middleware to log incoming requests and response status codes.

## How it Works

**Backend:**

- FastAPI manages memories in MongoDB.
- Pydantic models ensure data validation.
- API endpoints handle storing/retrieving memories, generating stories (using OpenAI), serving audio, and health checks.
- It interacts with OpenAI for story, title, image, and TTS generation, handling potential errors.
- MongoDB indexes improve query speed.
- Utilizes asynchronous operations.

**Frontend:**

- The RememberWhen React component displays fetched stories.
- The main App component shows memory lists, enables adding memories, and generating stories.
- axios is used for backend communication.
- useState and useEffect manage state and side effects.
- Conditional rendering handles loading and errors.
- frontend/src/index.js is the entry point, rendering App.
- frontend/src/App.css styles the UI.
- Frontend communicates with the backend at http://localhost:8000.

## Tech Stack

*   **Programming Languages:** Python, JavaScript
*   **Backend Framework:** FastAPI
*   **Web Server:** Uvicorn (for running FastAPI)
*   **Database:** MongoDB (via PyMongo)
*   **API Interaction:** OpenAI API
*   **Configuration:** python-dotenv
*   **Data Validation:** Pydantic
*   **SSL Certificate Handling:** certifi
*   **Frontend Framework:** React
*   **Frontend State Management:** React Hooks (useState, useEffect)
*   **Frontend Styling:** CSS (using `App.css` and `index.css`)
*   **CSS Post-processing:** Tailwind CSS (with Autoprefixer and PostCSS)
*   **Testing:**  Jest, React Testing Library
*   **Other Libraries**: axios

