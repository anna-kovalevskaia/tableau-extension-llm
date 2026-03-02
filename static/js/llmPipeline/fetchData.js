import { validateParams, readChunkRows, applyChunkFilter } from "../worksheet/worksheetChunkReader.js";
import { getWorksheet, getFilters } from "../worksheet/worksheetContext.js";

export async function fetchData({
    user_id,
    limit = 60000
}) {
    let next = await fetch("/api/nextFilter", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id })
    }).then(r => r.json());

    const worksheetName = next.worksheetName;
    const chunkField = next.chunkField; // "" or null → no chunk
    let chunkValues = next.chunkValues; // "" or null → no chunk
    const requiredFields = next.requiredFields;
    let lastChunk = next.done;

    const worksheet = getWorksheet(worksheetName);
    validateParams({ worksheet, requiredFields, limit });

    const requiredFieldsName = requiredFields.find(obj => obj.otherRequiredFieldNames)?.otherRequiredFieldNames || [];
    const measureNames = requiredFields.find(obj => obj.measureNames)?.measureNames || [];

    if (measureNames.length > 0) {
        await worksheet.applyFilterAsync(
            "Measure Names",
            measureNames,
            tableau.FilterUpdateType.Replace
        );
    }

    if (!chunkField) {
        const { rows } = await readChunkRows(worksheet, requiredFieldsName, measureNames, limit);
        await fetch("/api/saveChunk", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user_id, rows })
        });
        return;
    }

    while (!lastChunk) {
        await applyChunkFilter(worksheet, chunkField, chunkValues);
        const { rows } = await readChunkRows(worksheet, requiredFieldsName, measureNames, limit);

        const saveResp = await fetch("/api/saveChunk", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user_id, rows })
        }).then(r => r.json());
        if (saveResp.done) break;

        next = await fetch("/api/nextFilter", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user_id })
        }).then(r => r.json());
        chunkValues = next.chunkValues;
        lastChunk = next.done;
    }
}