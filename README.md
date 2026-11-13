# CampusConnect: A University Student-Support Agent for CoCIS Freshers

## 1. Introduction

CampusConnect is an AI-Native student-support agent designed to assist freshers in the College of Computing and Information Sciences (CoCIS) at Makerere University.

New students often have difficulties accessing reliable information about registration procedures, academic programmes, lecture venues, fees, university facilities, and student-support services. This information may be distributed across different documents and sources.

CampusConnect addresses this challenge by providing a centralised platform where students can ask questions and receive responses grounded in the available CoCIS documents. It also supports controlled student-support requests through an agentic workflow that uses tools, memory, and human approval.

## 2. Key Features

- **Retrieval-Augmented Generation (RAG):** Retrieves relevant information from the CoCIS knowledge base to support accurate responses.
- **AI-Native student assistance:** Allows students to ask questions using natural language.
- **Tool integration:** Enables the agent to perform specific operations, such as looking up lecture venues and managing support requests.
- **Memory:** Retains relevant support-request context to help students continue previously started tasks.
- **Human approval:** Requires approval before carrying out support-request submissions that need authorisation.
- **Guardrails:** Includes controls for unauthorised data access, unapproved actions, invalid tool arguments, database connection failures, and excessive execution steps.
- **Observability:** Captures execution events and agent activity for monitoring and evaluation.

## 3. Technologies Used

| Technology | Purpose |
|---|---|
| Python | Main programming language |
| LangChain | AI model integration and tool calling |
| LangGraph | Managing the agent's workflow |
| Groq | AI model provider |
| Gemini | Alternative model implementation retained in the code |
| FAISS | Local vector storage and similarity search |
| Sentence Transformers | Generating document embeddings |
| SQLite | Storing application data and support requests |
| JSON Schema | Validating tool arguments |
| PyPDF | Extracting text from PDF documents |
| Python-dotenv | Loading environment variables |

## 4. Project Structure

The project is organised into different directories, with each directory responsible for a particular part of the application.

```text
CampusConnect-David/
│
├── app/
│   ├── campusconnect.py
│   ├── agent_graph.py
│   ├── orchestrator.py
│   ├── memory.py
│   ├── models.py
│   ├── state.py
│   ├── capture_live_trace.py
│   │
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── loader.py
│   │   ├── chunker.py
│   │   ├── embeddings.py
│   │   ├── retriever.py
│   │   └── vectorstore.py
│   │
│   └── tools/
│       ├── __init__.py
│       ├── common.py
│       ├── definitions.py
│       ├── errors.py
│       ├── executor.py
│       ├── store.py
│       ├── create_support_request_draft.py
│       ├── submit_support_request.py
│       ├── get_support_request_status.py
│       └── lookup_lecture_venue.py
│
├── data/
│   └── campusconnect.db
│
├── docs/
│
├── evaluation/
│
├── evidence/
│
├── knowledge/
│   ├── Corpus/
│   └── faiss_index/
│       ├── index.faiss
│       └── index.pkl
│
├── scripts/
│   └── demo_week4.py
│
├── tests/
│   └── test_failure_authorization.py
│
├── requirements.txt
├── .env
├── .gitignore
└── README.md
```

## 5. Description of Important Files and Directories

### 5.1 Application Directory (`app/`)

This directory contains the main application code and the components responsible for running CampusConnect.

**`campusconnect.py`**

This is the main entry point of the application. It loads environment variables, initialises the database, memory service, tool executor, and AI model, and creates the CampusConnect agent.

It also manages the interactive terminal session through which students submit questions and receive responses.

**`agent_graph.py`**

This file defines the LangGraph workflow used by CampusConnect. It organises the agent's operations into four main stages:

1. **Sense:** Receives the student's question, retrieves relevant CoCIS information using RAG, and checks whether relevant support-request context is available in memory.
2. **Decide:** Sends the student's question, retrieved evidence, and available tool descriptions to the AI model. The model decides whether to answer directly or request a tool.
3. **Act:** Executes the tools requested by the model. Actions that require approval are presented for human approval before execution.
4. **Stop:** Produces the final response and ends the workflow when the task is complete or an execution limit or safety condition is reached.

The file also manages workflow state, memory interactions, tool execution, approval checks, and execution limits.

**`orchestrator.py`**

This file provides shared functionality used by the agent workflow. It contains:

- **RAG evidence retrieval:** Retrieves relevant information from the CoCIS knowledge base.
- **Tool declarations:** Provides the AI model with descriptions of available tools and their expected arguments.
- **Approval descriptions:** Prepares explanations of actions that require human approval.
- **System and tool instructions:** Defines the instructions that guide the agent's behaviour and tool usage.
- **Maximum execution steps:** Defines the maximum number of decision steps the agent can take before stopping.

The orchestrator does not communicate directly with a specific AI provider. Instead, it works through the `ModelClient` interface defined in `models.py`.

**`models.py`**

This file defines the common interface used to communicate with AI models. It contains the model client implementations that allow CampusConnect to work with different AI providers.

The active implementation uses Groq through LangChain's `ChatGroq` integration. The Gemini implementation has been retained in comments as an alternative, allowing the model provider to be changed without redesigning the main agent workflow.

**`memory.py`**

Handles the agent's memory operations. It allows CampusConnect to retain and retrieve relevant student support-request context so that a student can continue a previously started task.

**`state.py`**

Defines the workflow state used to track the progress of agent operations.

**`capture_live_trace.py`**

Provides functionality for capturing the agent's execution trace during a live session.

### 5.2 How the Main Agent Files Work Together

The three files `agent_graph.py`, `orchestrator.py`, and `models.py` have separate responsibilities but work together to run the agent.

- `agent_graph.py` controls the LangGraph workflow and determines how the agent moves between its stages.
- `orchestrator.py` provides shared functionality, including evidence retrieval, tool declarations, instructions, approval descriptions, and execution limits.
- `models.py` provides the interface through which the workflow communicates with the selected AI model.

When a student submits a question, the agent workflow retrieves relevant evidence and passes the question and context to the AI model. The model can either generate a response or request a tool. When a tool is requested, the workflow executes it and provides the result back to the model before producing the final response.

This separation makes it possible to change the AI model provider without having to redesign the entire LangGraph workflow.

### 5.3 Retrieval-Augmented Generation Directory (`app/rag/`)

This directory contains the components responsible for processing and retrieving information from the CoCIS knowledge base.

| File | Responsibility |
|---|---|
| `loader.py` | Loads and extracts text from PDF documents. |
| `chunker.py` | Splits extracted documents into smaller text sections. |
| `embeddings.py` | Generates numerical representations of text using Sentence Transformers. |
| `vectorstore.py` | Manages the FAISS vector store. |
| `retriever.py` | Retrieves relevant document sections based on a student's question. |

### 5.4 Tools Directory (`app/tools/`)

This directory contains the tools that allow the agent to perform specific operations.

| File | Responsibility |
|---|---|
| `definitions.py` | Defines the available tools and their input schemas. |
| `executor.py` | Validates and executes tool requests. |
| `common.py` | Contains shared tool functionality. |
| `errors.py` | Defines tool-related error codes. |
| `store.py` | Handles database operations. |
| `create_support_request_draft.py` | Creates a draft student-support request. |
| `submit_support_request.py` | Handles support-request submission. |
| `get_support_request_status.py` | Retrieves the status of a support request. |
| `lookup_lecture_venue.py` | Looks up lecture venue information. |

### 5.5 Other Directories

**`data/`**

Contains the SQLite database used to store application data. The main database file is `campusconnect.db`.

**`docs/`**

Contains project documentation.

**`evaluation/`**

Contains materials used to evaluate the agent's performance.

**`evidence/`**

Contains project evidence and supporting materials.

**`knowledge/`**

Contains the CoCIS PDF documents used as the agent's knowledge base. It also contains the FAISS index files used for document retrieval.

**`scripts/`**

Contains additional scripts used for demonstrations and other project operations.

**`tests/`**

Contains test files used to check application behaviour. For example, `test_failure_authorization.py` tests failure and authorisation-related behaviour.

## 6. Installation and Setup

### 6.1 Prerequisites

Before running CampusConnect, ensure that the following are installed:

- Python
- Git
- A Groq API key

### 6.2 Clone the Repository

Clone the project repository:

```bash
git clone https://github.com/DavidMakwetta/CampusConnect-David-Backup-.git
```

Navigate into the project directory:

```bash
cd CampusConnect-David-Backup-
```

### 6.3 Create a Virtual Environment

Create a Python virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows Command Prompt:

```cmd
.venv\Scripts\activate
```

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### 6.4 Install Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

### 6.5 Configure Environment Variables

Create a `.env` file in the root directory of the project and add your Groq API key:

```env
GROQ_API_KEY=your_groq_api_key
```

Replace `your_groq_api_key` with your actual API key.

Do not upload the `.env` file or expose your API key on GitHub.

## 7. Running the Application

After completing the installation and configuration steps, run the application from the project root directory:

```bash
python -m app.campusconnect
```

CampusConnect will initialise the required services and start an interactive terminal session.

Students can then enter questions and receive responses from the agent.

### Available Terminal Commands

| Command | Purpose |
|---|---|
| `exit` | Ends the application session. |
| `memory` | Displays the demo student's stored memory. |
| `forget` | Requests deletion of the demo student's stored memory. |

## 8. AI Model Configuration

CampusConnect uses a model-independent interface called `ModelClient`, defined in `models.py`.

The current application configuration uses Groq with the `llama-3.3-70b-versatile` model.

The Groq implementation communicates with the model through LangChain's `ChatGroq` integration and supports tool calling.

The previous Gemini implementation has been retained in commented code. This provides an alternative implementation that can be restored if required.

The model configuration is managed in:

- `app/models.py` – Contains the model client implementations.
- `app/campusconnect.py` – Selects the model implementation and configures the API key.

## 9. Agent Safety and Guardrails

CampusConnect includes guardrails to control how the agent handles operations and protects application data.

The main controls include:

1. **Unauthorised Data Access:** Prevents access to student information that the current session is not authorised to access.
2. **Unapproved High-Impact Writes:** Requires human approval before carrying out sensitive operations such as support-request submission.
3. **Database Connection Drops:** Handles database connection failures without allowing them to go unnoticed.
4. **Malformed Model Arguments:** Validates tool arguments before execution.
5. **Maximum Execution Steps:** Limits the number of decision steps to prevent the agent from running indefinitely.

## 10. Testing

The project includes automated tests for checking important application behaviour.

To run the authorisation and failure-handling tests from the project root, use:

```bash
python -m tests.test_failure_authorization
```

## 11. Important Notes

- CampusConnect uses the available CoCIS documents as its primary source of information.
- Responses should be grounded in retrieved evidence rather than unsupported assumptions.
- The agent uses tools to carry out specific operations instead of relying only on conversational responses.
- Support-request submissions that require authorisation must receive human approval.
- The current terminal setup uses a demo student session. It should not be treated as a complete production authentication system.
- The FAISS index and SQLite database are important application resources and should be preserved when backing up the project.

## 12. Contributors

**Project:** CampusConnect: A University Student-Support Agent for CoCIS Freshers.

**Institution:** Makerere University

**College:** College of Computing and Information Sciences (CoCIS)

**Programme:** Bachelor of Science in Software Engineering