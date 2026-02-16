import { getWorksheetContext } from "../worksheet/worksheetContext.js";

export async function sendQueryWithSchema(question) {
    const worksheetName = tableau.extensions.settings.get("chosenWorksheet");
    if (!worksheetName) throw new Error("No worksheet selected");

    const context = await getWorksheetContext(worksheetName);

    const payload = {
        question,
        worksheet: context
    };

    const response = await fetch("/api/llm-query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    });

    if (!response.ok) {
        const text = await response.text();
        console.error("Backend error body:", text);
        throw new Error(`Backend error: ${response.status}`);
    }
    const json = await response.json();
    console.log("parsed json:", json);
    return json;
}