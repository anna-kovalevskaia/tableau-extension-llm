import { getWorksheet } from "./worksheet/worksheetContext.js";
import { addMessage, handleEnter } from "./ui/chatUtils.js";
import { sendQueryWithSchema } from "./llmPipeline/sendQueryWithSchema.js";
import { fetchData } from "./llmPipeline/fetchData.js";
import { getFinalAnswer } from "./llmPipeline/runAnalysis.js";

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

    input.addEventListener("keydown", (event) => {
        if (btn.disabled) return;
        handleEnter(event, handleAsk)
    });

    btn.addEventListener("click", handleAsk)
  });

  async function handleAsk() {
    const question = input.value.trim();
    if (!question) return;

    addMessage(question, "user");
    input.value = "";

    btn.disabled = true;

    try {
       // step 1 getting query and data structure
       btn.textContent = "Retrieving data structure and analyzing the query…";
       const user_id = await sendQueryWithSchema(question);
       // step 2 chunking data
       btn.textContent = "Loading all required data...";
       await fetchData(user_id);
       // step 3 llm response
       btn.textContent = "Analysing data...";
       const finalResult = await getFinalAnswer(user_id);
       const formattedResult = finalResult
          .replace(/\\n/g, '\n')
          .replace(/\\t/g, '\t')
          .replace(/\\r/g, '\r')
          .replace(/\\"/g, '"')
          .replace(/\\\\/g, '\\');
       addMessage(formattedResult, "bot");
    } catch (error) {
        console.error(error);
        addMessage(JSON.stringify(error, Object.getOwnPropertyNames(error)), "bot");
    } finally {
        btn.disabled = false;
        btn.textContent = "Send";
    }
  }
