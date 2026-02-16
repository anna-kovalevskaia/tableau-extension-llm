import { getWorksheet } from "./worksheet/worksheetContext.js";
import { addMessage, handleEnter } from "./ui/chatUtils.js";
import { sendQueryWithSchema } from "./llmPipeline/sendQueryWithSchema.js";
import { requestChunk } from "./llmPipeline/requestChunk.js";
import { getFinalAnswer } from "./llmPipeline/getFinalAnswer.js";

let input;
let btn;

tableau.extensions.initializeAsync({ configure: openConfigureDialog })
    .then(() => {
        console.log("Extension initialized");
    });

function openConfigureDialog() {
    tableau.extensions.ui.displayDialogAsync("configure.html", "", {
        height: 600,
        width: 500
    });
}

document.addEventListener("DOMContentLoaded", () => {

    input = document.getElementById("userQuestion");
    btn = document.getElementById("askBtn");

    input.focus();

    input.addEventListener("keydown", (event) =>
        handleEnter(event, handleAsk)
    );

    btn.addEventListener("click", handleAsk)
  });

  async function handleAsk() {
    const question = input.value.trim();
    if (!question) return;

    addMessage(question, "user");
    input.value = "";

    btn.disabled = true;
    btn.textContent = "Thinking...";

    try {
       // step 1
        const parsed = await sendQueryWithSchema(question);
       // step 2 chunking data
       // step 3 llm response

    } catch (error) {
        console.error(error);
        addMessage(JSON.stringify(error, Object.getOwnPropertyNames(error)), "bot");
    } finally {
        btn.disabled = false;
        btn.textContent = "Send";
    }
  }
