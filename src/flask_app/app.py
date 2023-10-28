from flask import Flask, render_template, request, redirect, url_for
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import playlist_functions as pf

app = Flask(__name__)

# ... [rest of your functions here] ...

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
