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
//read worksheet rows using Summary Data Reader respecting limit
export async function readChunkRows(worksheet, requiredFieldsName, measureNames, limit) {
    const table = await worksheet.getSummaryDataAsync({
        ignoreSelection: true,
        maxRows:limit
    });

    const requiredSet = new Set(requiredFieldsName);
    const rows = [] ;
    let next = 0;

    table.data.forEach(row => {
        const obj = {};
        let measureName = null;
        let measureValue = null;

        row.forEach((cell,i) => {
            const fieldName = table.columns[i].fieldName;
            if (fieldName === "Measure Names") {
                measureName = cell.formattedValue;
            } else
            if (fieldName === "Measure Values") {
                measureValue = cell.value;
            } else
            if (requiredSet.has(fieldName)) {
                obj[fieldName] = cell.value;
            }
        });
        if (measureName && measureValue !== null) {
            obj[measureName] = measureValue;
        }
        if (Object.keys(obj).length > 0) {
            if (next > 0 && !rows[next-1].hasOwnProperty(measureName) ) { //так работает. с Map() не работает.
                rows[next-1][measureName] = measureValue;
            } else {
                rows.push(obj);
                next += 1
            }
        }

    });

    return { rows };
}
