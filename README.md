# AI-Powered Quotation Generation Agent

This project is a simple Flask-based quotation generation app that allows B2B customers to chat, browse products from a SQLite database, build a cart, and generate a professional PDF quotation.

## Features
- Chat-based product request entry
- Product search from SQLite database
- Shopping cart management
- Subtotal, GST, shipping, and grand total calculation
- Quotation PDF generation with ReportLab
- Responsive Bootstrap UI

## Project Structure
- app.py - Main Flask application
- database.py - SQLite setup and seed data
- models.py - Data models
- utils.py - Cart logic
- chatbot.py - Simple NLP parsing for message intent and product extraction
- pdf_generator.py - PDF quotation generation
- templates/ - HTML templates
- static/ - CSS, JS, images
- pdfs/ - Generated quotation PDFs

## Installation
1. Open the project folder in VS Code.
2. Create a virtual environment (optional but recommended).
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Run the app
```bash
python app.py
```
Then open http://127.0.0.1:5000 in your browser.

## Notes
- The database file products.db is created automatically on first run.
- Sample products are seeded into the database.
