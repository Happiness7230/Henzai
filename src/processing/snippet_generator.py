"""
Snippet Generator - Create highlighted snippets from documents
"""

import re
from typing import List, Tuple, Optional


class SnippetGenerator:
    """
    Generate search result snippets with query term highlighting
    """
    
    def __init__(self, 
                 snippet_length: int = 200,
                 context_words: int = 8,
                 highlight_start: str = "<b>",
                 highlight_end: str = "</b>"):
        """
        Initialize snippet generator
        
        Args:
            snippet_length: Target snippet length in characters
            context_words: Number of words around matched term
            highlight_start: HTML tag to start highlighting
            highlight_end: HTML tag to end highlighting
        """
        self.snippet_length = snippet_length
        self.context_words = context_words
        self.highlight_start = highlight_start
        self.highlight_end = highlight_end
    
    def generate_snippet(self, 
                        text: str, 
                        query_terms: List[str],
                        tokenizer = None) -> str:
        """
        Generate a snippet from text with highlighted query terms
        
        Args:
            text: Full document text
            query_terms: List of query terms to highlight
            tokenizer: Optional tokenizer for term matching
            
        Returns:
            Highlighted snippet string
        """
        if not text:
            return ""
        
        if not query_terms:
            # No query terms - just return beginning
            return self._truncate_text(text, self.snippet_length)
        
        # Find best snippet location
        best_position = self._find_best_position(text, query_terms)
        
        # Extract snippet around best position
        snippet = self._extract_snippet(text, best_position, query_terms)
        
        # Highlight query terms
        snippet = self._highlight_terms(snippet, query_terms, tokenizer)
        
        return snippet
    
    def _find_best_position(self, text: str, query_terms: List[str]) -> int:
        """
        Find the best position in text to extract snippet
        Prioritizes positions with more query term matches
        
        Args:
            text: Full text
            query_terms: Query terms to look for
            
        Returns:
            Character position to center snippet around
        """
        text_lower = text.lower()
        query_terms_lower = [term.lower() for term in query_terms]
        
        # Find all positions where query terms appear
        positions = []
        for term in query_terms_lower:
            # Find all occurrences of this term
            start = 0
            while True:
                pos = text_lower.find(term, start)
                if pos == -1:
                    break
                positions.append(pos)
                start = pos + 1
        
        if not positions:
            # No matches found - return beginning
            return 0
        
        # Find position with highest density of matches
        # Check each potential position
        best_pos = 0
        best_score = 0
        
        for pos in positions:
            # Count matches within snippet_length of this position
            score = sum(
                1 for p in positions
                if abs(p - pos) <= self.snippet_length // 2
            )
            
            if score > best_score:
                best_score = score
                best_pos = pos
        
        return best_pos
    
    def _extract_snippet(self, 
                        text: str, 
                        center_position: int, 
                        query_terms: List[str]) -> str:
        """
        Extract snippet around center position
        
        Args:
            text: Full text
            center_position: Position to center snippet around
            query_terms: Query terms (for context)
            
        Returns:
            Extracted snippet
        """
        # Calculate start and end positions
        half_length = self.snippet_length // 2
        
        start = max(0, center_position - half_length)
        end = min(len(text), center_position + half_length)
        
        # Try to break at word boundaries
        snippet = text[start:end]
        
        # Add ellipsis if truncated
        prefix = "..." if start > 0 else ""
        suffix = "..." if end < len(text) else ""
        
        # Break at word boundaries
        if prefix:
            # Find first space
            first_space = snippet.find(' ')
            if first_space != -1:
                snippet = snippet[first_space + 1:]
        
        if suffix:
            # Find last space
            last_space = snippet.rfind(' ')
            if last_space != -1:
                snippet = snippet[:last_space]
        
        return prefix + snippet.strip() + suffix
    
    def _highlight_terms(self, 
                        snippet: str, 
                        query_terms: List[str],
                        tokenizer = None) -> str:
        """
        Highlight query terms in snippet
        
        Args:
            snippet: Text snippet
            query_terms: Terms to highlight
            tokenizer: Optional tokenizer for stemmed matching
            
        Returns:
            Snippet with highlighted terms
        """
        if not query_terms:
            return snippet
        
        # Build pattern for all query terms
        # Match whole words only
        patterns = []
        
        for term in query_terms:
            # Escape special regex characters
            escaped = re.escape(term)
            # Match word boundaries
            patterns.append(f"\\b{escaped}\\w*\\b")
        
        # Combine all patterns
        combined_pattern = '|'.join(patterns)
        
        def replace_match(match):
            """Replace matched text with highlighted version"""
            matched_text = match.group(0)
            return f"{self.highlight_start}{matched_text}{self.highlight_end}"
        
        # Apply highlighting (case-insensitive)
        highlighted = re.sub(
            combined_pattern,
            replace_match,
            snippet,
            flags=re.IGNORECASE
        )
        
        return highlighted
    
    def _truncate_text(self, text: str, max_length: int) -> str:
        """
        Truncate text to max length at word boundary
        
        Args:
            text: Text to truncate
            max_length: Maximum length
            
        Returns:
            Truncated text
        """
        if len(text) <= max_length:
            return text
        
        # Truncate and find last space
        truncated = text[:max_length]
        last_space = truncated.rfind(' ')
        
        if last_space > 0:
            truncated = truncated[:last_space]
        
        return truncated.strip() + "..."
    
    def generate_multiple_snippets(self,
                                   text: str,
                                   query_terms: List[str],
                                   count: int = 3) -> List[str]:
        """
        Generate multiple snippets from different parts of text
        Useful for long documents
        
        Args:
            text: Full document text
            query_terms: Query terms to highlight
            count: Number of snippets to generate
            
        Returns:
            List of snippet strings
        """
        if not text or not query_terms:
            return [self._truncate_text(text, self.snippet_length)]
        
        text_lower = text.lower()
        query_terms_lower = [term.lower() for term in query_terms]
        
        # Find all positions where query terms appear
        positions = []
        for term in query_terms_lower:
            start = 0
            while True:
                pos = text_lower.find(term, start)
                if pos == -1:
                    break
                positions.append(pos)
                start = pos + len(term)
        
        if not positions:
            return [self._truncate_text(text, self.snippet_length)]
        
        # Sort positions
        positions.sort()
        
        # Select diverse positions (spread out)
        selected = []
        min_distance = self.snippet_length
        
        for pos in positions:
            # Check if far enough from existing selections
            if not selected or min(abs(pos - s) for s in selected) >= min_distance:
                selected.append(pos)
                if len(selected) >= count:
                    break
        
        # Generate snippets
        snippets = []
        for pos in selected:
            snippet = self._extract_snippet(text, pos, query_terms)
            snippet = self._highlight_terms(snippet, query_terms)
            snippets.append(snippet)
        
        return snippets
    
    def highlight_document(self, text: str, query_terms: List[str]) -> str:
        """
        Highlight query terms in full document (no truncation)
        
        Args:
            text: Full document text
            query_terms: Terms to highlight
            
        Returns:
            Full text with highlighted terms
        """
        return self._highlight_terms(text, query_terms)


def test_snippet_generator():
    """Test the snippet generator"""
    generator = SnippetGenerator()
    
    text = """
    Python is a high-level, interpreted programming language with dynamic semantics.
    Its high-level built in data structures, combined with dynamic typing and dynamic
    binding, make it very attractive for Rapid Application Development, as well as
    for use as a scripting or glue language to connect existing components together.
    Python's simple, easy to learn syntax emphasizes readability and therefore reduces
    the cost of program maintenance. Python supports modules and packages, which
    encourages program modularity and code reuse. The Python interpreter and the
    extensive standard library are available in source or binary form without charge
    for all major platforms, and can be freely distributed.
    """
    
    query_terms = ["python", "programming", "language"]
    
    snippet = generator.generate_snippet(text, query_terms)
    
    print("Original text:")
    print(text.strip())
    print("\nGenerated snippet:")
    print(snippet)
    print("\nMultiple snippets:")
    for i, snip in enumerate(generator.generate_multiple_snippets(text, query_terms, 2), 1):
        print(f"{i}. {snip}")


if __name__ == "__main__":
    test_snippet_generator()