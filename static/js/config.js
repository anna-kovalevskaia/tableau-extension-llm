import { initializeWorksheetSelection } from "./ui/initWorksheetSelection.js";

document.addEventListener("DOMContentLoaded", () => {
    tableau.extensions.initializeDialogAsync().then(() => {
        initializeWorksheetSelection();
    })
});