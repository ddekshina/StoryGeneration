import { useEffect, useState } from "react";

const App = () => {
    const [userId, setUserId] = useState("123");
    const [date, setDate] = useState("");
    const [description, setDescription] = useState("");
    const [story, setStory] = useState(null);
    const [loadingStory, setLoadingStory] = useState(false);
    const [error, setError] = useState("");

    // Upload memory
    const uploadIncident = async (e) => {
        e.preventDefault();
        if (!date || !description.trim()) {
            setError("Please fill all fields.");
            return;
        }
        try {
            await fetch("http://localhost:8000/incidents/", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ user_id: userId, date, description })
            });
            setDate("");
            setDescription("");
            setError("");
        } catch (err) {
            setError("Error uploading memory.");
        }
    };

    // Generate story
    const generateStory = async () => {
        setLoadingStory(true);
        setError("");
        try {
            const res = await fetch(`http://localhost:8000/generate_story`);
            const data = await res.json();
            setStory(data);
        } catch (err) {
            setError("Error generating story.");
        }
        setLoadingStory(false);
    };

    return (
        <div className="container">
            <h1>📖 Remember When...</h1>

            {/* Upload Incident Form */}
            <form onSubmit={uploadIncident} className="form">
                <label>Date:</label>
                <input type="date" value={date} onChange={(e) => setDate(e.target.value)} required />

                <label>Memory:</label>
                <textarea
                    placeholder="Describe your memory..."
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    required
                ></textarea>

                <button type="submit">Add Memory</button>
            </form>

            {/* Error Messages */}
            {error && <p className="error">{error}</p>}

            {/* Generate Story Button */}
            <button onClick={generateStory} className="generate-btn">
                {loadingStory ? "Generating..." : "📜 Create My Story"}
            </button>

            {/* Display Story */}
            {story && (
                <div className="story-box">
                    <h2>{story.title}</h2>
                    <p>{story.story}</p>
                    <img src={story.image_url} alt="Memory" />
                    <audio controls>
                        <source src={story.audio_url} type="audio/mpeg" />
                    </audio>
                </div>
            )}
        </div>
    );
};

export default App;
