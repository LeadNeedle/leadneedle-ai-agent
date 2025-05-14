# website.py

from flask import Blueprint, render_template

website_bp = Blueprint('website_bp', __name__, template_folder='templates')

@website_bp.route('/')
def home():
    return render_template("index.html")
