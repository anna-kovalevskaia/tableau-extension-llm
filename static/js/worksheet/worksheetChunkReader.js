// validate required parameters before reading chunk data
export function validateParams({ worksheet, requiredFields, limit }) {
    if (!worksheet) {
        throw new Error("requestChunk: 'worksheet' is required");
    }
    if (!Array.isArray(requiredFields) || requiredFields.length === 0) {
        throw new Error("requestChunk: 'requiredFields' must be a non-empty array");
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
        [chunkValues],
        tableau.FilterUpdateType.Replace
    );
}
// read worksheet rows using Summary Data Reader respecting limit
export async function readChunkRows(worksheet, requiredFieldsName, measureNames, limit) {
    const table = await worksheet.getSummaryDataAsync({
        ignoreSelection: true,
        maxRows: limit
    });

    const requiredSet = new Set(requiredFieldsName);
    const rowMap = new Map(); // key -> aggregated row

    table.data.forEach(row => {
        const dimsObj = {};
        const keyParts = [];

        let measureName = null;
        let measureValue = null;

        row.forEach((cell, i) => {
            const fieldName = table.columns[i].fieldName;
            if (fieldName === "Measure Names") {
                measureName = cell.formattedValue;
            } else
             if (fieldName === "Measure Values") {
                measureValue = cell.value;
            } else {
                // Warning: use ALL NOT-measure fields as key
                const value = cell.value;
                dimsObj[fieldName] = value;
                keyParts.push(`${fieldName}:${value}`);
            }
        });

        if (!measureName || measureValue === null) return;

        const key = keyParts.join("|");

        let obj = rowMap.get(key);
        if (!obj) {
            obj = { ...dimsObj };
            rowMap.set(key, obj);
        }

        obj[measureName] = measureValue;
    });

    return { rows: Array.from(rowMap.values()) };
}