import { populateChunkFieldSelect } from "../ui/populateChunkFieldSelect.js";

export async function initializeWorksheetSelection() {
    const dashboard = tableau.extensions.dashboardContent.dashboard;

    const worksheetSelect = document.getElementById("worksheetSelect");
    const fieldForChunk = document.getElementById("fieldForChunk")
    // populate worksheets list
    dashboard.worksheets.forEach(ws => {
        const option = document.createElement("option");
        option.value = ws.name;
        option.textContent = ws.name;
        worksheetSelect.appendChild(option);
    });
    // restore saved state
    const savedWorksheet = tableau.extensions.settings.get("chosenWorksheet");
    if (savedWorksheet) {
        worksheetSelect.value = savedWorksheet;
        await populateChunkFieldSelect(savedWorksheet, fieldForChunk);

        const savedField = tableau.extensions.settings.get("chunkField");
        if (savedField) {
            fieldForChunk.value = savedField
        }
    } else {
        if (dashboard.worksheets.length > 0) {
            const first_worksheet = dashboard.worksheets[0].name;
            worksheetSelect.value = first_worksheet;
            tableau.extensions.settings.set("chosenWorksheet",first_worksheet);
            await populateChunkFieldSelect(first_worksheet, fieldForChunk)
            const value = fieldForChunk.value;
            tableau.extensions.settings.set("chunkField",value);
            await tableau.extensions.settings.saveAsync();
        }
    }
    // handle worksheet selection for llm
    worksheetSelect.addEventListener("change", async () => {
        const chosenWorksheet = worksheetSelect.value;
        tableau.extensions.settings.set("chosenWorksheet",chosenWorksheet);
        await populateChunkFieldSelect(chosenWorksheet, fieldForChunk)
        const value = fieldForChunk.value;
        tableau.extensions.settings.set("chunkField",value);
        await tableau.extensions.settings.saveAsync();
    });
    // handle chunk-field selection
    fieldForChunk.addEventListener("change", async () => {
        const value = fieldForChunk.value;
        if (value === "") {
            tableau.extensions.settings.erase("chunkField");
        } else {
            tableau.extensions.settings.set("chunkField", value);
        }
        await tableau.extensions.settings.saveAsync();
    })

}
