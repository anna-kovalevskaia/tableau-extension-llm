export async function getFinalAnswer({ user_id }) {
    const response = await fetch("/api/runAnalysis", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify( { user_id })
        });
    if (!response.ok) {
        const errorBody = await response.text();
        throw new Error(`Server error (${response.status}): ${errorBody}`);
    }

    const data = await response.json();
    return data;
}