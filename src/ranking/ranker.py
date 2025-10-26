"""Raking module: calculates document scores based on TF-IDF or BM25."""

import math

class Ranker:
      def __init__(self, database):
          self.database = database

      def rank(self, query_tokens, index):
          scores = {}
          N = len(set(doc for postings in index.values() for doc, _ in postings))  # Total docs
          for term in query_tokens:
              if term in index:
                  df = len(index[term])  # Document frequency
                  idf = math.log(N / df) if df > 0 else 0
                  for doc, tf in index[term]:
                      scores[doc] = scores.get(doc, 0) + (tf * idf)
          return sorted(scores.items(), key=lambda x: x[1], reverse=True)
