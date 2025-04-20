import { useEffect, useState } from "react";
import "./App.css";
import axios from 'axios';

const App = () => {
    const [userId] = useState("123"); // Default user ID
    const [date, setDate] = useState("");
    const [description, setDescription] = useState("");
    const [tags, setTags] = useState([]);
    const [newTag, setNewTag] = useState("");
    const [mood, setMood] = useState("");
    const [location, setLocation] = useState("");
    const [memories, setMemories] = useState([]);
    const [story, setStory] = useState(null);
    const [storyTone, setStoryTone] = useState("heartwarming");
    const [maxLength, setMaxLength] = useState(500);
    const [selectedTags, setSelectedTags] = useState([]);
    const [loading, setLoading] = useState({
        memories: false,
        story: false,
        adding: false
    });
    const [error, setError] = useState("");

    // Available moods and tones
    const moods = ["happy", "nostalgic", "peaceful", "excited", "reflective", "grateful"];
    const tones = ["heartwarming", "humorous", "mystical", "adventurous", "romantic", "inspirational"];

    // Fetch memories on component mount
    useEffect(() => {
        const fetchMemories = async () => {
            setLoading(prev => ({ ...prev, memories: true }));
            setError("");
            try {
                const res = await fetch(`http://localhost:8000/memories/${userId}`);
                if (!res.ok) throw new Error("Failed to fetch memories");
                const data = await res.json();
                setMemories(data.memories || []);
            } catch (err) {
                setError(err.message);
                console.error("Fetch error:", err);
            } finally {
                setLoading(prev => ({ ...prev, memories: false }));
            }
        };
        fetchMemories();
    }, [userId]);

    // Add new tag
    const addTag = (e) => {
        e.preventDefault();
        if (newTag.trim() && !tags.includes(newTag.trim())) {
            setTags([...tags, newTag.trim()]);
            setNewTag("");
        }
    };

    // Remove tag
    const removeTag = (tagToRemove) => {
        setTags(tags.filter(tag => tag !== tagToRemove));
    };

    // Add new memory
    const addMemory = async (e) => {
        e.preventDefault();
        if (!date || !description.trim()) {
            setError("Please fill all required fields");
            return;
        }

        setLoading(prev => ({ ...prev, adding: true }));
        setError("");
        try {
            const response = await fetch("http://localhost:8000/memories/", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    user_id: userId,
                    date,
                    description,
                    tags,
                    mood,
                    location
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || "Failed to add memory");
            }

            // Refresh memories after successful addition
            const res = await fetch(`http://localhost:8000/memories/${userId}`);
            const data = await res.json();
            setMemories(data.memories || []);
            
            // Reset form
            setDate("");
            setDescription("");
            setTags([]);
            setMood("");
            setLocation("");
        } catch (err) {
            setError(err.message);
            console.error("Upload error:", err);
        } finally {
            setLoading(prev => ({ ...prev, adding: false }));
        }
    };

    // Generate story
    const generateStory = async () => {
        setLoading(prev => ({ ...prev, story: true }));
        setError("");
        try {
            const response = await axios.post(
                "http://localhost:8000/generate-story/",
                {
                    user_id: userId,
                    tone: storyTone,
                    include_tags: selectedTags.length > 0 ? selectedTags : undefined,
                    max_length: maxLength
                },
                {
                    headers: { "Content-Type": "application/json" },
                    timeout: 30000
                }
            );
            
            setStory(response.data);
        } catch (err) {
            const errorMessage = err.response?.data?.detail || 
                                err.response?.data?.message || 
                                err.message || 
                                "Failed to generate story";
            
            setError(`Error generating story: ${errorMessage}`);
            console.error("Story generation error:", err);
        } finally {
            setLoading(prev => ({ ...prev, story: false }));
        }
    };

    return (
        <div className="app-container">
            <header className="app-header">
                <h1>Memory Weaver</h1>
                <p className="subtitle">Preserve your precious moments</p>
            </header>

            <main className="main-content">
                {/* Add Memory Form */}
                <section className="memory-form-section">
                    <h2>Add New Memory</h2>
                    <form onSubmit={addMemory} className="memory-form">
                        <div className="form-group">
                            <label>Date:</label>
                            <input
                                type="date"
                                value={date}
                                onChange={(e) => setDate(e.target.value)}
                                required
                                className="form-input"
                            />
                        </div>
                        
                        <div className="form-group">
                            <label>Description:</label>
                            <textarea
                                value={description}
                                onChange={(e) => setDescription(e.target.value)}
                                placeholder="Describe your memory in detail..."
                                required
                                className="form-textarea"
                                rows={4}
                            />
                        </div>

                        <div className="form-group">
                            <label>Location (optional):</label>
                            <input
                                type="text"
                                value={location}
                                onChange={(e) => setLocation(e.target.value)}
                                placeholder="Where did this happen?"
                                className="form-input"
                            />
                        </div>

                        <div className="form-group">
                            <label>Mood:</label>
                            <select
                                value={mood}
                                onChange={(e) => setMood(e.target.value)}
                                className="form-input"
                            >
                                <option value="">Select a mood...</option>
                                {moods.map(m => (
                                    <option key={m} value={m}>{m.charAt(0).toUpperCase() + m.slice(1)}</option>
                                ))}
                            </select>
                        </div>

                        <div className="form-group">
                            <label>Tags:</label>
                            <div className="tags-input">
                                <input
                                    type="text"
                                    value={newTag}
                                    onChange={(e) => setNewTag(e.target.value)}
                                    placeholder="Add a tag..."
                                    className="form-input"
                                    onKeyPress={(e) => e.key === 'Enter' && addTag(e)}
                                />
                                <button type="button" onClick={addTag} className="add-tag-btn">
                                    Add Tag
                                </button>
                            </div>
                            <div className="tags-container">
                                {tags.map(tag => (
                                    <span key={tag} className="tag">
                                        {tag}
                                        <button
                                            type="button"
                                            onClick={() => removeTag(tag)}
                                            className="remove-tag"
                                        >
                                            ×
                                        </button>
                                    </span>
                                ))}
                            </div>
                        </div>
                        
                        <button
                            type="submit" 
                            className="submit-btn"
                            disabled={loading.adding}
                        >
                            {loading.adding ? (
                                <>
                                    <span className="spinner"></span> Saving...
                                </>
                            ) : "Save Memory"}
                        </button>
                    </form>
                </section>

                {/* Memories List */}
                <section className="memories-section">
                    <h2>Your Memories</h2>
                    {loading.memories ? (
                        <div className="loading-state">
                            <span className="spinner"></span> Loading memories...
                        </div>
                    ) : memories.length === 0 ? (
                        <p className="empty-state">No memories yet. Add your first memory!</p>
                    ) : (
                        <ul className="memories-list">
                            {memories.map((memory, index) => (
                                <li key={index} className="memory-item">
                                    <h3>{new Date(memory.date).toLocaleDateString()}</h3>
                                    <p>{memory.description}</p>
                                </li>
                            ))}
                        </ul>
                    )}
                </section>

                {/* Story Generator */}
                <section className="story-generator-section">
                    <h2>Create a Story</h2>
                    <div className="story-controls">
                        <div className="control-group">
                            <label>Story Tone:</label>
                            <select
                                value={storyTone}
                                onChange={(e) => setStoryTone(e.target.value)}
                                className="form-input"
                            >
                                {tones.map(tone => (
                                    <option key={tone} value={tone}>
                                        {tone.charAt(0).toUpperCase() + tone.slice(1)}
                                    </option>
                                ))}
                            </select>
                        </div>

                        <div className="control-group">
                            <label>Max Length (words):</label>
                            <input
                                type="number"
                                value={maxLength}
                                onChange={(e) => setMaxLength(parseInt(e.target.value))}
                                min="100"
                                max="1000"
                                className="form-input"
                            />
                        </div>

                        <div className="control-group">
                            <label>Filter by Tags:</label>
                            <div className="tags-container">
                                {Array.from(new Set(memories.flatMap(m => m.tags || []))).map(tag => (
                                    <span
                                        key={tag}
                                        className={`tag ${selectedTags.includes(tag) ? 'selected' : ''}`}
                                        onClick={() => {
                                            setSelectedTags(prev =>
                                                prev.includes(tag)
                                                    ? prev.filter(t => t !== tag)
                                                    : [...prev, tag]
                                            );
                                        }}
                                    >
                                        {tag}
                                    </span>
                                ))}
                            </div>
                        </div>
                    </div>

                    <button
                        onClick={generateStory}
                        className="generate-btn"
                        disabled={loading.story || memories.length === 0}
                    >
                        {loading.story ? (
                            <>
                                <span className="spinner"></span> Generating...
                            </>
                        ) : (
                            <>
                                <span role="img" aria-label="wand">✨</span> Generate Story
                            </>
                        )}
                    </button>
                    
                    {memories.length === 0 && (
                        <p className="hint">Add some memories first to generate a story</p>
                    )}
                </section>

                {/* Generated Story */}
                {story && (
                    <section className="generated-story">
                        <div className="story-header">
                            <h2>{story.title}</h2>
                            <div className="story-meta">
                                <span>Generated on {new Date().toLocaleDateString()}</span>
                                {story.tags_used.length > 0 && (
                                    <span>Tags: {story.tags_used.join(', ')}</span>
                                )}
                                {story.mood && (
                                    <span>Mood: {story.mood}</span>
                                )}
                            </div>
                        </div>
                        
                        <div className="story-content">
                            <p className="story-text">{story.story}</p>
                            
                            {story.image_url && (
                                <div className="story-media">
                                    <img 
                                        src={story.image_url} 
                                        alt="Memory visualization" 
                                        className="story-image"
                                    />
                                </div>
                            )}
                            
                            {story.audio_url && (
                                <div className="story-audio">
                                    <h3>Listen to your story</h3>
                                    <audio controls className="audio-player">
                                        <source src={story.audio_url} type="audio/mpeg" />
                                        Your browser does not support audio playback.
                                    </audio>
                                </div>
                            )}
                        </div>
                        
                        <div className="story-actions">
                            <button className="action-btn">Save Story</button>
                            <button className="action-btn">Share</button>
                            <button className="action-btn" onClick={() => setStory(null)}>Close</button>
                        </div>
                    </section>
                )}

                {/* Error Display */}
                {error && (
                    <div className="error-message">
                        <p>{error}</p>
                        <button onClick={() => setError("")} className="dismiss-btn">
                            Dismiss
                        </button>
                    </div>
                )}
            </main>

            <footer className="app-footer">
                <p>Memory Weaver © {new Date().getFullYear()}</p>
            </footer>
        </div>
    );
};

export default App;