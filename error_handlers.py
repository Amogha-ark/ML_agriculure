from app import app
from flask import render_template,request

@app.errorhandler(500)
def unique(e):
    return render_template('error.html')