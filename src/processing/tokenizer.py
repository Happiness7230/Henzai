"""Processing module: handles tokenization and text normalization."""

import re

class Tokenizer:
      def tokenize(self, text):
          # Lowercase, remove punctuation, split into words
          text = text.lower()
          words = re.findall(r'\b\w+\b', text)
          return words
  