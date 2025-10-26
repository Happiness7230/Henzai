"""Flask web application entry point for the search engine API."""

from flask import Flask, render_template, request
from src.processing.tokenizer import Tokenizer
from src.ranking.ranker import Ranker
from src.storage.database import Database

app = Flask(__name__)
tokenizer = Tokenizer()
database = Database()
ranker = Ranker(database)

@app.route('/')
def home():
      return render_template('search.html')

@app.route('/search', methods=['POST'])
def search():
      query = request.form['query']
      query_tokens = tokenizer.tokenize(query)
      index = database.load_index()
      results = ranker.rank(query_tokens, index)
      return render_template('search.html', results=results)

if __name__ == "__main__":
      app.run()
