# app/main/routes.py
import json, os
from flask import Blueprint, render_template

json_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'content', 'cv_data.json')

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/cv')
def cv():
    try:
        #opening json with data:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            cv_data = json.load(f)
    except FileNotFoundError:
        return "Error: cv_data.json not found", 404

    # render cv template
    return render_template('cv.html', **cv_data)

@main_bp.route('/contact')
def contact():
    return render_template('contact.html')

