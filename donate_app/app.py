from flask import Flask, render_template
from flask_cors import CORS
import os
import sys

# Add backend to path for shared utils (like db)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(port=5007, debug=True)
