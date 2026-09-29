# 📄 Quotation Generation Agent with AI Tool-Calling Architecture

An intelligent, autonomous Quotation Generation Agent built with **Flask**, **Local Hugging Face LLMs**, **SQLite**, and **ReportLab**.

The system demonstrates a robust **AI Tool-Calling Architecture**: the language model does not directly calculate prices or hallucinate inventory. Instead, it acts as an **orchestrator** that selects appropriate Python tools, executes business actions against the SQLite catalog and user session, and renders professional, downloadable PDF quotations.

---

## 🌟 Architecture & Core Workflow

```
User ──► Flask UI / API ──► QuotationAgent ──► Local Hugging Face LLM
                                   │
                                   ▼
                              ToolRegistry
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        ▼                          ▼                          ▼
  search_products            add_to_cart                generate_pdf
   (SQLite DB)              (Session Cart)           (ReportLab Engine)
```

### Execution Flow:
1. **User Request:** The user interacts conversationally (e.g., *"Search for laptops under $1000 and add the first one to my cart"*).
2. **Orchestration:** `QuotationAgent` passes the conversation history and OpenAI-compatible tool definitions to the LLM (`Qwen/Qwen3-1.7B` or offline fallback).
3. **Tool Invocation:** The LLM responds with structured tool calls (e.g., `search_products(category='laptop', budget=1000)`).
4. **Deterministic Execution:** `ToolRegistry` invokes the Python function with the active `ToolContext` (connecting the session, SQLite database, and PDF generator).
5. **Observation Loop:** The deterministic result is fed back into the agent history (`role: "tool"`).
6. **Final Synthesis:** The agent produces a natural-language confirmation and quotation download link.

---

## 🚀 Key Features

* **AI Tool-Calling Agent Loop:** Autonomous multi-step ReAct loop (up to 8 steps) with JSON normalization and error recovery.
* **Zero Financial Hallucinations:** Product prices, inventory levels, GST/tax rates, and shipping calculations are 100% deterministic, governed by Python and SQLite.
* **On-Premise / Local Inference:** Runs with Hugging Face Transformers (`Qwen/Qwen3-1.7B`) with graceful fallback mode when offline.
* **Dynamic PDF Generation:** Automatically outputs structured B2B/B2C PDF quotations using ReportLab with unique IDs (e.g., `QT-20260909-XXXXXX`).
* **Session-Based Cart Management:** Stateful cart persistence across multi-turn interactions.
* **Dual Interface:** Web interface (`/`, `/search`, `/ai-search`, `/cart`, `/quotation`) plus JSON REST API (`/api/agent`).

---

## 📁 Project Structure

```text
chatbot/
├── app.py                 # Core Flask application, web routes & REST API (/api/agent)
├── agent.py               # Autonomous QuotationAgent loop and response normalization
├── tool_registry.py       # ToolRegistry and ToolSpec dataclass (OpenAI schema converter)
├── tools.py               # Business tools (search_products, add_to_cart, generate_pdf, etc.)
├── llm.py                 # Hugging Face local LLM adapter & smart heuristic fallback
├── chatbot.py             # Deterministic NLP parser and conversation memory summarizer
├── database.py            # SQLite DatabaseManager with seed product catalog
├── models.py              # Product and CartItem data models
├── pdf_generator.py       # ReportLab PDF compilation engine
├── products.db            # SQLite database file
├── requirements.txt       # Project dependencies
├── templates/             # HTML Templates (index.html, cart.html, quotation.html)
├── pdfs/                  # Generated PDF quotation documents
└── tests/                 # Automated unit and integration test suite
    ├── test_agent_loop.py
    ├── test_conversation_memory.py
    └── test_tools_and_api.py
```

---

## 🛠️ Tool Registry Reference

All tools are registered in `tool_registry.py` and exposed via standard OpenAI JSON schemas:

| Tool Name | Parameters | Description |
| :--- | :--- | :--- |
| `search_products` | `category` *(str)*, `filters` *(dict)*, `budget` *(float)* | Searches the catalog for matching items within budget |
| `add_to_cart` | `product_id` *(int)*, `quantity` *(int)* | Adds or consolidates product quantity in the session cart |
| `remove_from_cart` | `product_id` *(int)* | Removes specified item from the shopping cart |
| `update_quantity` | `product_id` *(int)*, `quantity` *(int)* | Modifies quantity; removes item if quantity is set to 0 |
| `show_cart` | *None* | Returns items, subtotal, GST (tax), and shipping estimates |
| `generate_quotation` | *None* | Formulates complete quotation breakdown |
| `generate_pdf` | *None* | Generates a styled ReportLab PDF quotation in `/pdfs/` |
| `clear_cart` | *None* | Clears all items from the current session cart |

---

## ⚡ Quickstart & Installation

### 1. Prerequisites
- Python 3.9, 3.10, or 3.11 installed.

### 2. Setup Virtual Environment
```bash
# Clone the repository
git clone https://github.com/AgentRoomAI/Quotation-Generation-Agent.git
cd Quotation-Generation-Agent/chatbot

# Create virtual environment
py -3.11 -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Run Automated Tests
Verify that all 14 unit and integration tests pass:
```bash
pytest tests -v
```

### 4. Launch the Web Application
```bash
python app.py
```
Open your browser at `http://127.0.0.1:5000`.

---

## 🔌 REST API Usage

You can interact with the agent programmatically via `POST /api/agent`:

### Request
```bash
curl -X POST http://127.0.0.1:5000/api/agent \
  -H "Content-Type: application/json" \
  -d '{"message": "search laptop"}'
```

### Response
```json
{
  "status": "success",
  "reply": "I found the following products: #18 Acer Aspire 7 ($75999.0); #20 Apple MacBook Air M2 ($119999.0)...",
  "cart": [],
  "summary": {"subtotal": 0.0, "gst_total": 0.0, "shipping": 0.0, "grand_total": 0.0},
  "quotation_id": null,
  "quotation_pdf": null
}
```

---

## 📜 License
Developed for educational, research, and business automation purposes.

