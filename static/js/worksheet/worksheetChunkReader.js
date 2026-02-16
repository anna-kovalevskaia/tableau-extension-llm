// validate required parameters before reading chunk data
export function validateParams({ worksheet, neededFields, limit }) {
    if (!worksheet) {
        throw new Error("requestChunk: 'worksheet' is required");
    }
    if (!Array.isArray(neededFields) || neededFields.length === 0) {
        throw new Error("requestChunk: 'neededFields' must be a non-empty array");
    }
    if (typeof limit !== "number" || limit <= 0) {
        throw new Error("requestChunk: 'limit' must be a positive number");
    }
}
// apply chunk filter on the worksheet if filtering is enabled
export async function applyChunkFilter(worksheet, chunkField, chunkValues) {
    if (!chunkField || !chunkValues) {
        return;
    }

    await worksheet.applyFilterAsync(
        chunkField,
        chunkValues,
        tableau.FilterUpdateType.REPLACE
    );
}
//read worksheet rows using Summary Data Reader respecting limit
export async function readChunkRows(worksheet, neededFields, limit) {
    const reader = await worksheet.getSummaryDataReaderAsync({
        ignoreSelection: true
    });

    const rows = [];
    let row;
    let count = 0;
    let partial = false;

    while ((row = await reader.readAsync()) !== null) {
        count++;

        if (count > limit) {
            partial = true;
            break;
        }

        const obj = {};

        row.forEach((cell, i) => {
            const fieldName = reader.columns[i].fieldName;
            if (neededFields.includes(fieldName)) {
                obj[fieldName] = cell.value;
            }
        });

        rows.push(obj);
    }

    await reader.closeAsync();

    return { rows, partial };
}
