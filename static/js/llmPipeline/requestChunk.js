import { validateParams, readChunkRows, applyChunkFilter } from "../worksheet/worksheetChunkReader.js";

export async function requestChunk({
    worksheet,
    chunkField = null,
    chunkValues = null,
    neededFields,
    limit = 3000
}) {
    validateParams({ worksheet, neededFields, limit });

    await applyChunkFilter(worksheet, chunkField, chunkValues);

    const { rows, partial } = await readChunkRows(
        worksheet,
        neededFields,
        limit
    );

    await fetch("/api/saveChunk", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            rows
        })
    });

    return {
        rows: rows.length
    };
}