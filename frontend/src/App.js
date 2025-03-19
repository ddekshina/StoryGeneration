import { useEffect, useState } from "react";

const App = () => {
    const [userId, setUserId] = useState("123");
    const [date, setDate] = useState("");
    const [description, setDescription] = useState("");
    const [story, setStory] = useState(null);
    const [incidents, setIncidents] = useState([]); // ✅ Ensuring it starts as an array

    // Fetch incidents
    const fetchIncidents = () => {
        fetch(`http://localhost:8000/incidents/${userId}`)
            .then(res => res.json())
            .then(data => {
                if (Array.isArray(data)) {
                    setIncidents(data);
                } else {
                    setIncidents([]);  // ✅ Default to empty array if response is invalid
                }
            })
            .catch(err => {
                console.error("Error fetching incidents:", err);
                setIncidents([]);  // ✅ Ensure it's always an array
            });
    };

    // Upload incident
    const uploadIncident = (e) => {
        e.preventDefault();
        fetch("http://localhost:8000/incidents/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user_id: userId, date, description })
        })
        .then(res => res.json())
        .then(() => {
            fetchIncidents();
            setDate("");
            setDescription("");
        })
        .catch(err => console.error("Error uploading incident:", err));
    };

    // Generate Story
    const generateStory = () => {
        fetch(`http://localhost:8000/generate_story/${userId}`)
            .then(res => res.json())
            .then(data => setStory(data))
            .catch(err => console.error("Error generating story:", err));
    };

    useEffect(() => {
        fetchIncidents();
    }, [userId]);

    return (
        <div>
            <h2>📖 Remember When...</h2>

            {/* Upload Incident Form */}
            <form onSubmit={uploadIncident}>
                <input type="date" value={date} onChange={(e) => setDate(e.target.value)} required />
                <input type="text" placeholder="Describe your memory" value={description} onChange={(e) => setDescription(e.target.value)} required />
                <button type="submit">Add Memory</button>
            </form>

            {/* Display Incidents */}
            <h3>Your Memories:</h3>
            <ul>
                {incidents.length > 0 ? (
                    incidents.map((incident, index) => (
                        <li key={index}>{incident.date}: {incident.description}</li>
                    ))
                ) : (
                    <p>No memories found.</p> // ✅ Fallback if no incidents are found
                )}
            </ul>

            {/* Generate Story Button */}
            <button onClick={generateStory}>Generate Story</button>

            {/* Display Story */}
            {story && (
                <div>
                    <h2>{story.title}</h2>
                    <p>{story.story}</p>
                </div>
            )}
        </div>
    );
};

export default App;
