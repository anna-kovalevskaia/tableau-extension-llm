import  { getWorksheet, getSchema, getFilters } from "../worksheet/worksheetContext.js";

export async function populateChunkFieldSelect(worksheetName, fieldForChunk) {
    const worksheet = getWorksheet(worksheetName);
    // get worksheet data schema
    const schema = await getSchema(worksheet);

    const filters = await getFilters(worksheet);
    // leave only allowed filter fields
    const allowedFields = schema.filter(col =>
        (col.dataType === "int" || col.dataType === "date") &&
        filters.find(f => f.fieldName === col.fieldName)?.type === "categorical"
    );

    fieldForChunk.innerHTML = "";
    // add the "None" option to allow disabling chunk-based filtering
    const noneOption = document.createElement("option");
    noneOption.value = "";
    noneOption.textContent = "None";
    fieldForChunk.appendChild(noneOption);
    // populate the dropdown with allowed filter/chunk fields
    allowedFields.forEach(col => {
        const option = document.createElement("option");
        option.value = col.fieldName;
        option.textContent = `${col.fieldName} (${col.dataType})`;
        fieldForChunk.appendChild(option);
    });
}
