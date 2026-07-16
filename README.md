# Quotation Generation Agent

## Overview

The **Quotation Generation Agent** is a Python-based web application that automates the process of generating professional quotations. It allows users to create quotations from product information stored in a database and export them as PDF documents through an easy-to-use web interface.

## Features

* Generate quotations automatically
* Store and manage product information using SQLite
* Generate downloadable PDF quotations
* User-friendly web interface
* Organized project structure
* Fast and efficient quotation creation

## Project Structure

```text
quotation-agent/
│
├── app.py                 # Main application
├── chatbot.py             # Chatbot functionality
├── database.py            # Database operations
├── models.py              # Database models
├── pdf_generator.py       # PDF quotation generation
├── products.db            # SQLite database
├── utils.py               # Utility functions
├── requirements.txt       # Project dependencies
├── README.md              # Project documentation
├── templates/             # HTML templates
├── static/                # CSS, JavaScript and images
├── pdfs/                  # Generated quotation PDFs
└── .gitignore
```

## Prerequisites

* Python 3.8 or later
* pip (Python Package Manager)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/AgentRoomAI/Quotation-Generation-Agent.git
cd Quotation-Generation-Agent
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
```

### 3. Activate the Virtual Environment

**Windows**

```bash
.venv\Scripts\activate
```

**Linux/macOS**

```bash
source .venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

## Running the Application

Start the application by running:

```bash
python app.py
```

After the server starts, open the URL displayed in the terminal (typically `http://127.0.0.1:5000`) in your web browser.

## How to Use

1. Launch the application.
2. Enter customer and quotation details.
3. Select the required products.
4. Generate the quotation.
5. Download the quotation as a PDF.

## Technologies Used

* Python
* Flask
* SQLite
* HTML
* CSS
* JavaScript
* ReportLab (for PDF generation)

## Dependencies

Install all required packages using:

```bash
pip install -r requirements.txt
```

## Author

**Aman V**

## License

This project is developed for educational and internship purposes.
