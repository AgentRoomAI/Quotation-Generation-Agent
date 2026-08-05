# Quotation Generation Agent with AI Tool-Calling Architecture

## 1. Introduction
The Quotation Generation Agent is an intelligent Flask-based web application that helps users browse products, add items to a cart, and generate professional quotation PDFs. The system combines a local Hugging Face language model with Python business logic to create a conversational agent experience.

## 2. Project Objective
The main objective of this project is to automate quotation generation using AI while keeping the workflow simple for end users. The system allows users to:
- search for products
- add products to a cart
- remove or update cart items
- generate quotation summaries
- create downloadable PDF quotations
- interact with the system using conversational AI

## 3. Problem Statement
Traditional quotation systems often require manual steps such as searching products, adding items, and generating quotations separately. This project solves that by combining product management, cart handling, PDF generation, and AI-based interaction into one integrated workflow.

## 4. Proposed Solution
The solution uses:
- Flask for the web application
- SQLite for product storage
- ReportLab for PDF generation
- Hugging Face Transformers for local LLM integration
- A custom agent architecture that can call Python tools automatically

## 5. System Architecture
The system follows a layered architecture:

1. User Interface
   - Flask web pages and forms
   - Product browsing and cart management

2. Application Layer
   - Flask routes for search, cart, quotation, and PDF generation
   - Session management for cart state

3. AI Layer
   - Local LLM powered by Hugging Face Transformers
   - Agent loop that decides when to use tools

4. Tool Layer
   - search_products
   - add_to_cart
   - remove_from_cart
   - update_quantity
   - show_cart
   - generate_quotation
   - generate_pdf
   - clear_cart

5. Data Layer
   - SQLite database for product records
   - Session-based cart storage

## 6. Main Modules
### app.py
This is the core Flask application. It contains the main routes for:
- homepage and product listing
- AI search
- cart operations
- quotation generation
- PDF download

### chatbot.py
This module acts as the interface between the Flask app and the LLM layer. It helps wrap the AI response flow for the application.

### llm.py
This module contains the local LLM integration. It supports:
- model loading
- prompt construction
- agent-compatible generation flow
- tool-calling interaction

### agent.py
This module implements the agent loop. The agent:
- receives user messages
- sends them to the LLM
- decides whether a tool is needed
- executes the requested tool
- feeds the result back to the LLM
- continues until a final response is produced

### tools.py
This file contains the actual business-logic implementations for the tools. Each tool handles a specific action such as cart updates or quotation generation.

### tool_registry.py
This module stores the available tools and exposes them to the agent in a structured format.

### database.py
This module manages the SQL database and seed data for the product catalog.

### models.py
This file defines the core data models such as Product and CartItem.

### pdf_generator.py
This file generates professional quotation PDFs using ReportLab.

### templates/
The templates folder contains the HTML pages for:
- home page
- cart page
- quotation page

## 7. Features Implemented
### Product Search
Users can search products by name, description, or keyword.

### AI Search
Users can type natural-language requests and the agent can help with product lookup and cart operations.

### Cart Management
Users can:
- add items
- update quantity
- remove items
- clear the cart

### Quotation Generation
The app generates quotation summaries and creates downloadable PDF files.

### Local AI Integration
The system uses a Hugging Face model locally through Transformers instead of relying on an external API.

## 8. Agent Workflow
The agent follows this flow:
1. User sends a request.
2. The LLM receives the message and tool list.
3. The LLM decides if a tool is needed.
4. If yes, the tool is executed.
5. The tool result is given back to the LLM.
6. The process repeats until the LLM gives a final answer.

This creates an automated tool-calling experience similar to modern AI agent systems.

## 9. Example Use Cases
### Example 1: Add a Product to Cart
User: “Add a laptop to my cart”

System behavior:
- identifies the product
- adds it to the cart
- returns a confirmation response

### Example 2: Show Cart
User: “Show my cart”

System behavior:
- calls the show_cart tool
- returns cart contents and totals

### Example 3: Generate Quotation
User: “Generate quotation”

System behavior:
- calls the generate_quotation tool
- returns the quotation summary

## 10. Technologies Used
- Python
- Flask
- SQLite
- HTML/CSS/JavaScript
- Hugging Face Transformers
- ReportLab
- Werkzeug session management

## 11. Advantages
- Easy to use web interface
- Conversational AI support
- Automated quotation workflow
- Modular and extendable architecture
- Local LLM support without depending only on cloud APIs

## 12. Challenges Faced
- Local model loading can be slow depending on hardware
- Tool-calling behavior depends on the model’s ability to choose tools correctly
- Need for careful session management with Flask
- Need for modular separation between UI, AI logic, and business logic

## 13. Future Enhancements
- Add richer product filtering
- Add customer profile management
- Add better multi-step tool planning
- Improve the AI prompt for more accurate tool selection
- Add authentication and role-based access
- Add support for more advanced quotation templates

## 14. Conclusion
The Quotation Generation Agent demonstrates how a local LLM can be used to automate quotation-related tasks through an agent-style tool-calling architecture. The system successfully combines AI, web development, and business logic into a practical solution for quotation generation.
