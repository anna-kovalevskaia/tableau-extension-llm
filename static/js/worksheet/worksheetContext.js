export function getWorksheet(worksheetName) {
    const dashboard = tableau.extensions.dashboardContent.dashboard;
    return dashboard.worksheets.find(ws => ws.name === worksheetName);
}

export async function getSchema(worksheet) {
    const summary = await worksheet.getSummaryDataAsync({
        maxRows: 1,
        ignoreSelection: true
    });
    return summary.columns;
}

export async function getFilters(worksheet) {
    const filters = await worksheet.getFiltersAsync();

    return filters.map(f => ({
        fieldName: f.fieldName,
        type: f.filterType,
        values: extractFilterValues(f)
    }));
}

function extractFilterValues(filter) {
    if (filter.filterType === "categorical") {
        return filter.appliedValues.map(v => v.formattedValue);
    }
    if (filter.filterType === "range") {
        return {
            min: filter.minValue,
            max: filter.maxValue
        };
    }
    return null;
}

function normalizeSchema(columns) {
    return columns.map(col => ({
        name: col.fieldName,
        type: mapTableauType(col.dataType),
        isDiscrete: isDiscreteField(col.dataType)
    }));
}

function mapTableauType(t) {
    if (t === "string") return "string";
    if (t === "float") return "float";
    if (t === "integer") return "integer";
    if (t === "int") return "integer";
    if (t === "date" || t === "datetime") return "date";
    return "string";
}

function isDiscreteField(t) {
    return (
        t === "string" ||
        t === "bool" ||
        t === "date" ||
        t === "datetime"
    );
}

export async function getWorksheetContext(worksheetName) {
    const worksheet = getWorksheet(worksheetName);
    const rawSchema = await getSchema(worksheet);
    const schema = normalizeSchema(rawSchema);
    const filters = await getFilters(worksheet);
    const chunkField = tableau.extensions.settings.get("chunkField") || null;

    return {
        worksheetName,
        schema,
        filters,
        chunkField
    };
}