# Tableau LLM Assistant 

A local Tableau Extension that lets you ask natural‑language questions and receive analytical answers based on the data from the selected worksheet. It runs entirely on your machine, does not require Tableau Server or Tableau Cloud.
**[Video installation guide](https://www.youtube.com/watch?v=slbN9J2fC3w)**
## Feature
- Can run entirely locally in Tableau Desktop or inside Tableau Server/Cloud.
- Does not require elevated permissions, service user. Works as a standard Dashboard Extension.
- The LLM never sees raw data.
- Automatically detects which fields are required for analysis


## How Tableau LLM Assistant works
It is a Tableau Dashboard Extension that:  
- connects to the selected worksheet,  
- retrieves the worksheet’s data structure,  
- loads the worksheet’s data in chunks,  
- generates Python code for analysis,  
- executes that code inside a secure sandbox,  
- and returns an interpreted answer from the LLM.

This is **not a production‑grade** solution but an **open‑source tool**.


## Requirements
**Mandatory**

- Tableau Desktop or Tableau Server/Cloud (via External Extensions)
- Python 3.10+
- Redis (Memurai for Windows)
- Git

**LLM configuration**
- API keys for the chosen remote LLM provider (OpenRouter, Gemini, OpenAI, etc.) required only if you use a cloud‑based model
- Ollama installed locally - optional, used when running an entirely local LLM without any API keys


## Installation (backend)

### 1. Clone the Tableau LLM Assistant
```bash
git clone https://github.com/anna-kovalevskaia/tableau-extension-llm.git
cd tableau-extension-llm
```

### 2. Create and activate Virtual Environment
```bash
python -m venv .venv
```
#### **Windows**

```bash
.venv\Scripts\activate
```
#### **macOS/Linux**

```bash
source .venv/bin/activate
```
**Tip:** You should see `(.venv)` at the beginning of your command prompt when the virtual environment is active.

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Setting up .env

```bash
cp .env_template .env
```
Fill in keys:

```env
OPENROUTER_API_KEY=...
GOOGLE_API_KEY=...
SERVER=localhost
TEMP_FILES_DIR=_temp_files
```

### 5. Running Redis

**Windows** (using Memurai) https://www.memurai.com/get-memurai

On Windows, Redis can be run via Memurai, a fully Redis‑compatible server for Windows. Install Memurai and start the service before launching the extension.

Checking if Redis is running
```bash
netstat -ano | findstr 6379
```
If you see a line containing:```LISTENING``` - then redis is running.

**macOS**
```bash
brew install redis
redis-cli ping
```

**Linux**
```bash
sudo apt install redis-server
redis-cli ping
```
If it returns ```PONG```, Redis is active.

### 6. Running dashboard_app.py
```bash
uvicorn backend.dashboard_app:app --reload --port 8888
```

It will be accessible at this address
```bash
http://localhost:8888
```

## Instruction on the Tableau side
### ⚠️ 1. Preparing the data

✔️ Create measure field named **SERVICE_FIELD** (Mandatory)
This is needed due to a Tableau Extensions API limitation:
when all Measure Names are selected, the API returns an empty filter

Create a calculated field:

```
SERVICE_VALUE = 0
```
✔️ (Optional) Create a dimension field for chunking
If your worksheet is large (100k+ rows), create an INT field, or select from your datasource.
Create a calculated field (example):
```
ChunkID = int(row_number%100)+1
```
  Requirements:
  - starts at 1
  - increments by 1
  - 3,000-10,000 rows per value.  This improves data‑loading performance.


### 2. Configuring the extension in Tableau

- Open the Dashboard
- Go to: **Objects → Extension → My Extensions**
- Select the file:
dashboard_extension/tableau_llm_assistant.trex

In the Configure window:
- choose the worksheet the extension will work with
- choose the chunk field (if you created one)

### 3. Important Tableau limitations
- The extension can only work with worksheets that are present on the Dashboard.
- If you need to analyze another worksheet:
- add it to the Dashboard
- configure the extension
- then **hide it using Control Visibility**

## ⚠️ Important Notice

This extension is distributed as an open‑source project.
It runs entirely locally, does not send any data to the internet, and does not require Tableau Server or Tableau Cloud.

The project **is not** positioned as a **commercial Tableau product** and does not include enterprise guarantees, so teams that choose to use it in production should independently assess whether it meets their requirements and security policies.



## Optional: Exporting Redis‑stored history for analytics

Since Redis is already used to temporarily store the conversation history (user ↔ assistant messages), LLM‑generated code, and internal execution states, it is possible to configure an additional process that periodically exports this data into a persistent storage system (for example, a database or a data lake).
Such exports can be useful for several purposes:
- analyzing user questions to understand which topics the dashboard does not answer well
- identifying common failure patterns in LLM‑generated code
- improving prompt design and model selection
- monitoring how users interact with the extension over time
The extension itself does not perform this export, but the Redis data model is intentionally simple, so teams can implement their own ingestion pipeline if needed.



### License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


### Related projects
-[tableau_mcp_starter_kit](https://github.com/TheInformationLab/tableau_mcp_starter_kit) - an alternative approach to using LLMs with Tableau based on the MCP server.
