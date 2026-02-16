export async function getFinalAnswer() {
    const response = await fetch("/api/getFinalAnswer");

    if (!response.ok) {
        throw new Error("LLM final answer failed");
    }

    const data = await response.json();
    return data.answer;
}