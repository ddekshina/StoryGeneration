import { useEffect, useState } from "react";

const RememberWhen = ({ userId }) => {
    const [story, setStory] = useState(null);

    useEffect(() => {
        fetch(`http://localhost:8000/generate_story/${userId}`)
            .then((res) => res.json())
            .then((data) => setStory(data))
            .catch((err) => console.error(err));
    }, [userId]);

    return (
        <div>
            <h2>📖 {story?.title}</h2>
            <p>{story?.story || "Loading story..."}</p>
        </div>
    );
};

export default RememberWhen;
