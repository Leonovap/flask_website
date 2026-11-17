# Flask Website

A personal website built with **Flask**, featuring user authentication, a blog, and static pages.
Designed as a learning project and fully open-source.
## Features
- User registration and login
- Blog with posts
- Static pages (CV, contact, etc.)
- Docker & Docker Compose support for easy setup
- SQLite for local development

## Tech Stack
- Python 3.12 / Flask
- Jinja2 templates
- SQLite
- Docker & Docker Compose
- HTML, CSS, JavaScript

## Getting Started

### Clone the repository
```bash
git clone https://github.com/Leonovap/flask_website.git
cd flask_website

## Install dependencies
pip install -r requirements.txt

### Run locally

python run.py
### or with docker
docker-compose up --build

## Project structure
app/        # Flask application code
static/     # CSS, JS, images
templates/  # HTML templates
content/    # JSON data for pages
run.py      # Entry point
Dockerfile  # Docker setup



