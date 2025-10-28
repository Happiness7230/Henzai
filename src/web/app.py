"""Flask web application entry point for the search engine API."""

import os
import logging
from flask import Flask, render_template, request, jsonify
from src.config import Config
from src.processing.tokenizer import Tokenizer
from src.ranking.ranker import Ranker
from src.storage.database import Database

# Load configuration
config = Config.load()

# Initialize Flask app
app = Flask(__name__)
app.config['DEBUG'] = config.flask_debug

# Initialize components
tokenizer = Tokenizer()
database = Database(os.path.join(config.storage_dir, config.index_file))
ranker = Ranker(database)

@app.route('/')
def home():
    """Render search page."""
    return render_template('search.html')

@app.route('/search', methods=['POST'])
def search():
    """Handle search requests."""
    try:
        query = request.form['query']
        if not query:
            return render_template('search.html', error="Please enter a search query")

        query_tokens = tokenizer.tokenize(query)
        if not query_tokens:
            return render_template('search.html', error="No valid search terms found")

        index = database.load_index()
        if not index:
            return render_template('search.html', error="Search index is empty")

        results = ranker.rank(query_tokens, index)
        results = results[:config.max_results]  # Limit results per config

        return render_template('search.html', 
                            query=query,
                            results=results,
                            result_count=len(results))

    except Exception as e:
        logging.error(f"Search error: {str(e)}")
        return render_template('search.html', error="An error occurred during search")

@app.route('/status')
def status():
    """Return system status."""
    try:
        index = database.load_index()
        return jsonify({
            'status': 'ok',
            'index_size': len(index) if index else 0,
            'index_path': database.filename,
            'max_results': config.max_results
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=config.flask_port)
