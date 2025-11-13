"""
Enhanced Ranker with BM25 Algorithm
Provides better ranking than TF-IDF by handling document length and term saturation
"""

import math
from typing import List, Tuple, Dict
from collections import defaultdict


class Ranker:
    """
    Document ranker using BM25 algorithm
    BM25 is superior to TF-IDF for search ranking
    """
    
    def __init__(self, indexer, k1: float = 1.5, b: float = 0.75):
        """
        Initialize ranker with BM25 parameters
        
        Args:
            indexer: Indexer instance with inverted index
            k1: Controls term frequency saturation (1.2-2.0, default 1.5)
            b: Controls document length normalization (0-1, default 0.75)
        """
        self.indexer = indexer
        self.k1 = k1  # Term frequency saturation parameter
        self.b = b    # Document length normalization parameter
        
        # Cache for document lengths and average
        self._doc_lengths: Dict[str, int] = {}
        self._avg_doc_length: float = 0.0
        self._total_docs: int = 0
        self._cache_valid = False
    
    def _update_cache(self) -> None:
        """Update document length cache"""
        if self._cache_valid:
            return
        
        self._doc_lengths.clear()
        
        # Calculate document lengths from inverted index
        for term, postings in self.indexer.index.items():
            for doc_id, term_freq in postings:  # postings is a list of [doc_id, freq] pairs
                self._doc_lengths[doc_id] = self._doc_lengths.get(doc_id, 0) + term_freq
        
        # Calculate average document length
        self._total_docs = len(self._doc_lengths)
        if self._total_docs > 0:
            self._avg_doc_length = sum(self._doc_lengths.values()) / self._total_docs
        else:
            self._avg_doc_length = 0.0
        
        self._cache_valid = True
    
    def _calculate_idf(self, term: str) -> float:
        """
        Calculate Inverse Document Frequency (IDF) for a term
        
        IDF = log((N - df + 0.5) / (df + 0.5) + 1)
        Where N = total documents, df = document frequency of term
        
        Args:
            term: The term to calculate IDF for
            
        Returns:
            IDF score (higher = more discriminative)
        """
        self._update_cache()
        
        # Get document frequency (number of docs containing this term)
        df = len(self.indexer.index.get(term, {}))
        
        # BM25 IDF formula
        # Adding 1 ensures IDF is never negative
        idf = math.log((self._total_docs - df + 0.5) / (df + 0.5) + 1)
        
        return max(0, idf)  # Ensure non-negative
    
    def _calculate_bm25_score(self, term: str, doc_id: str, term_freq: int) -> float:
        """
        Calculate BM25 score for a term in a document
        
        BM25 = IDF(term) * (f(term,doc) * (k1 + 1)) / (f(term,doc) + k1 * (1 - b + b * |doc|/avgdl))
        
        Args:
            term: Query term
            doc_id: Document identifier
            term_freq: Frequency of term in document
            
        Returns:
            BM25 score for this term-document pair
        """
        self._update_cache()
        
        # Get IDF for the term
        idf = self._calculate_idf(term)
        
        # Get document length
        doc_length = self._doc_lengths.get(doc_id, 0)
        
        # Avoid division by zero
        if self._avg_doc_length == 0:
            return 0.0
        
        # Calculate document length normalization
        # b=0: no length normalization
        # b=1: full length normalization
        length_norm = 1 - self.b + self.b * (doc_length / self._avg_doc_length)
        
        # BM25 formula
        # k1 controls how quickly additional occurrences of a term
        # stop contributing to the score (saturation)
        numerator = term_freq * (self.k1 + 1)
        denominator = term_freq + self.k1 * length_norm
        
        score = idf * (numerator / denominator)
        
        return score
    
    def rank(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """
        Rank documents using BM25 algorithm
        
        Args:
            query: Search query string
            top_k: Number of top results to return
            
        Returns:
            List of (doc_id, score) tuples, sorted by score descending
        """
        # Tokenize query
        query_tokens = self.indexer.tokenizer.tokenize(query)
        
        if not query_tokens:
            return []
        
        # Update document length cache
        self._update_cache()
        
        if self._total_docs == 0:
            return []
        
        # Calculate scores for each document
        doc_scores: Dict[str, float] = defaultdict(float)
        
        for term in query_tokens:
            # Get document scores for each term
            postings = self.indexer.index.get(term, {})            # Calculate BM25 score for each document containing this term
            for doc_id, term_freq in postings:
                bm25_score = self._calculate_bm25_score(term, doc_id, term_freq)
                doc_scores[doc_id] += bm25_score
        
        # Sort by score (descending)
        ranked_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Return top K results
        return ranked_docs[:top_k]
    
    def rank_tfidf(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """
        Rank documents using traditional TF-IDF (for comparison)
        
        Args:
            query: Search query string
            top_k: Number of top results to return
            
        Returns:
            List of (doc_id, score) tuples, sorted by score descending
        """
        query_tokens = self.indexer.tokenizer.tokenize(query)
        
        if not query_tokens:
            return []
        
        self._update_cache()
        
        if self._total_docs == 0:
            return []
        
        doc_scores: Dict[str, float] = defaultdict(float)
        
        for term in query_tokens:
            postings = self.indexer.inverted_index.get(term, {})
            
            if not postings:
                continue
            
            # Calculate IDF
            idf = math.log(self._total_docs / len(postings))
            
            # Calculate TF-IDF for each document
            for doc_id, term_freq in postings.items():
                doc_length = self._doc_lengths.get(doc_id, 1)
                
                # TF = term_freq / doc_length (normalized)
                tf = term_freq / doc_length
                
                # TF-IDF score
                tfidf_score = tf * idf
                doc_scores[doc_id] += tfidf_score
        
        # Sort and return top K
        ranked_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)
        return ranked_docs[:top_k]
    
    def compare_algorithms(self, query: str, top_k: int = 10) -> Dict:
        """
        Compare BM25 vs TF-IDF results (for analysis)
        
        Args:
            query: Search query
            top_k: Number of results
            
        Returns:
            Dictionary with both rankings
        """
        bm25_results = self.rank(query, top_k)
        tfidf_results = self.rank_tfidf(query, top_k)
        
        return {
            'query': query,
            'bm25': bm25_results,
            'tfidf': tfidf_results,
            'bm25_top_doc': bm25_results[0][0] if bm25_results else None,
            'tfidf_top_doc': tfidf_results[0][0] if tfidf_results else None,
            'agreement': bm25_results[0][0] == tfidf_results[0][0] if bm25_results and tfidf_results else False
        }
    
    def invalidate_cache(self) -> None:
        """Invalidate document length cache (call after indexing new documents)"""
        self._cache_valid = False
    
    def get_statistics(self) -> Dict:
        """
        Get ranking statistics
        
        Returns:
            Dictionary with ranking stats
        """
        self._update_cache()
        
        return {
            'total_documents': self._total_docs,
            'average_document_length': round(self._avg_doc_length, 2),
            'total_terms': len(self.indexer.index),
            'bm25_parameters': {
                'k1': self.k1,
                'b': self.b
            }
        }
    
    def tune_parameters(self, k1: float, b: float) -> None:
        """
        Tune BM25 parameters
        
        Args:
            k1: Term frequency saturation (1.2-2.0 recommended)
            b: Length normalization (0-1, where 0=none, 1=full)
        """
        if not (0 <= k1 <= 3):
            raise ValueError("k1 should be between 0 and 3 (recommended: 1.2-2.0)")
        if not (0 <= b <= 1):
            raise ValueError("b should be between 0 and 1")
        
        self.k1 = k1
        self.b = b
        self.invalidate_cache()


# Backward compatibility: keep old class name if needed
TFIDFRanker = Ranker  # Alias for backward compatibility