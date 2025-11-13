"""
Advanced Query Parser
Supports boolean operators, phrases, wildcards, and filters
"""

import re
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum


class QueryOperator(Enum):
    """Query operators"""
    AND = "AND"
    OR = "OR"
    NOT = "NOT"


@dataclass
class ParsedQuery:
    """
    Parsed query with all components
    """
    original: str
    terms: List[str]                    # Regular terms
    phrases: List[str]                  # Exact phrases
    must_have: List[str]                # AND terms (must include)
    must_not_have: List[str]            # NOT terms (must exclude)
    should_have: List[str]              # OR terms (optional)
    wildcards: List[str]                # Wildcard patterns
    filters: Dict[str, str]             # Filters (site:, filetype:, etc.)
    is_simple: bool                     # True if no advanced features
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'original': self.original,
            'terms': self.terms,
            'phrases': self.phrases,
            'must_have': self.must_have,
            'must_not_have': self.must_not_have,
            'should_have': self.should_have,
            'wildcards': self.wildcards,
            'filters': self.filters,
            'is_simple': self.is_simple
        }


class QueryParser:
    """
    Advanced query parser with boolean operators and filters
    """
    
    def __init__(self, tokenizer=None):
        """
        Initialize query parser
        
        Args:
            tokenizer: Optional tokenizer for term processing
        """
        self.tokenizer = tokenizer
        
        # Supported filters
        self.supported_filters = {
            'site': 'Domain filter',
            'filetype': 'File type filter',
            'ext': 'File extension filter',
            'date': 'Date filter',
            'before': 'Before date',
            'after': 'After date',
            'lang': 'Language filter'
        }
    
    def parse(self, query: str) -> ParsedQuery:
        """
        Parse query into structured components
        
        Args:
            query: Raw query string
            
        Returns:
            ParsedQuery object with all components
        """
        original = query
        
        # Extract filters first (site:, filetype:, etc.)
        query, filters = self._extract_filters(query)
        
        # Extract phrases ("exact match")
        query, phrases = self._extract_phrases(query)
        
        # Extract wildcards (python*)
        query, wildcards = self._extract_wildcards(query)
        
        # Parse boolean operators
        must_have, must_not_have, should_have, remaining = self._parse_boolean(query)
        
        # Process remaining terms
        terms = self._tokenize_terms(remaining)
        
        # Determine if simple query
        is_simple = (
            not phrases and 
            not wildcards and 
            not filters and
            not must_have and 
            not must_not_have and 
            not should_have
        )
        
        return ParsedQuery(
            original=original,
            terms=terms,
            phrases=phrases,
            must_have=must_have,
            must_not_have=must_not_have,
            should_have=should_have,
            wildcards=wildcards,
            filters=filters,
            is_simple=is_simple
        )
    
    def _extract_filters(self, query: str) -> Tuple[str, Dict[str, str]]:
        """
        Extract filters like site:example.com, filetype:pdf
        
        Args:
            query: Query string
            
        Returns:
            (cleaned_query, filters_dict)
        """
        filters = {}
        
        # Pattern: filter:value
        pattern = r'(\w+):([^\s]+)'
        matches = re.finditer(pattern, query)
        
        for match in matches:
            filter_name = match.group(1).lower()
            filter_value = match.group(2)
            
            # Only extract known filters
            if filter_name in self.supported_filters:
                filters[filter_name] = filter_value
                # Remove from query
                query = query.replace(match.group(0), '')
        
        return query.strip(), filters
    
    def _extract_phrases(self, query: str) -> Tuple[str, List[str]]:
        """
        Extract exact phrases in quotes
        
        Args:
            query: Query string
            
        Returns:
            (cleaned_query, phrases_list)
        """
        phrases = []
        
        # Find all quoted phrases
        pattern = r'"([^"]+)"'
        matches = re.finditer(pattern, query)
        
        for match in matches:
            phrase = match.group(1).strip()
            if phrase:
                phrases.append(phrase)
                # Remove from query
                query = query.replace(match.group(0), '')
        
        return query.strip(), phrases
    
    def _extract_wildcards(self, query: str) -> Tuple[str, List[str]]:
        """
        Extract wildcard patterns (python*, *script)
        
        Args:
            query: Query string
            
        Returns:
            (cleaned_query, wildcards_list)
        """
        wildcards = []
        
        # Find wildcard patterns
        pattern = r'\b[\w*]+\*[\w*]*\b|\b\*[\w*]+\b'
        matches = re.finditer(pattern, query)
        
        for match in matches:
            wildcard = match.group(0)
            wildcards.append(wildcard)
            # Remove from query
            query = query.replace(wildcard, '')
        
        return query.strip(), wildcards
    
    def _parse_boolean(self, query: str) -> Tuple[List[str], List[str], List[str], str]:
        """
        Parse boolean operators (AND, OR, NOT)
        
        Args:
            query: Query string
            
        Returns:
            (must_have, must_not_have, should_have, remaining)
        """
        must_have = []
        must_not_have = []
        should_have = []
        
        # Split by operators (case insensitive)
        # Handle: term1 AND term2 OR term3 NOT term4
        
        # NOT terms (must exclude)
        not_pattern = r'NOT\s+(\w+)'
        not_matches = re.finditer(not_pattern, query, re.IGNORECASE)
        for match in not_matches:
            must_not_have.append(match.group(1).lower())
            query = query.replace(match.group(0), '')
        
        # Explicit AND terms
        and_pattern = r'(\w+)\s+AND\s+(\w+)'
        and_matches = re.finditer(and_pattern, query, re.IGNORECASE)
        for match in and_matches:
            must_have.extend([match.group(1).lower(), match.group(2).lower()])
            query = query.replace(match.group(0), '')
        
        # Explicit OR terms
        or_pattern = r'(\w+)\s+OR\s+(\w+)'
        or_matches = re.finditer(or_pattern, query, re.IGNORECASE)
        for match in or_matches:
            should_have.extend([match.group(1).lower(), match.group(2).lower()])
            query = query.replace(match.group(0), '')
        
        # Plus sign means must have (+term)
        plus_pattern = r'\+(\w+)'
        plus_matches = re.finditer(plus_pattern, query)
        for match in plus_matches:
            must_have.append(match.group(1).lower())
            query = query.replace(match.group(0), '')
        
        # Minus sign means must not have (-term)
        minus_pattern = r'-(\w+)'
        minus_matches = re.finditer(minus_pattern, query)
        for match in minus_matches:
            must_not_have.append(match.group(1).lower())
            query = query.replace(match.group(0), '')
        
        return must_have, must_not_have, should_have, query.strip()
    
    def _tokenize_terms(self, text: str) -> List[str]:
        """
        Tokenize remaining terms
        
        Args:
            text: Text to tokenize
            
        Returns:
            List of tokens
        """
        if not text:
            return []
        
        if self.tokenizer:
            return self.tokenizer.tokenize(text)
        else:
            # Simple tokenization
            return [
                word.lower() 
                for word in re.findall(r'\b\w+\b', text)
                if len(word) > 1
            ]
    
    def validate_query(self, query: str) -> Tuple[bool, Optional[str]]:
        """
        Validate query syntax
        
        Args:
            query: Query string
            
        Returns:
            (is_valid, error_message)
        """
        # Check for empty query
        if not query or not query.strip():
            return False, "Query cannot be empty"
        
        # Check for unmatched quotes
        if query.count('"') % 2 != 0:
            return False, "Unmatched quotes in query"
        
        # Check for valid filter syntax
        filter_pattern = r'(\w+):([^\s]+)'
        matches = re.finditer(filter_pattern, query)
        for match in matches:
            filter_name = match.group(1).lower()
            if filter_name not in ['and', 'or', 'not'] and filter_name not in self.supported_filters:
                return False, f"Unknown filter: {filter_name}"
        
        return True, None
    
    def explain_query(self, parsed: ParsedQuery) -> str:
        """
        Generate human-readable explanation of parsed query
        
        Args:
            parsed: ParsedQuery object
            
        Returns:
            Explanation string
        """
        parts = []
        
        if parsed.is_simple:
            return f"Simple search for: {' '.join(parsed.terms)}"
        
        if parsed.terms:
            parts.append(f"Search for: {', '.join(parsed.terms)}")
        
        if parsed.phrases:
            parts.append(f"Exact phrases: {', '.join([f'{p}' for p in parsed.phrases])}")

        
        if parsed.must_have:
            parts.append(f"Must include: {', '.join(parsed.must_have)}")
        
        if parsed.must_not_have:
            parts.append(f"Must NOT include: {', '.join(parsed.must_not_have)}")
        
        if parsed.should_have:
            parts.append(f"Should include (OR): {', '.join(parsed.should_have)}")
        
        if parsed.wildcards:
            parts.append(f"Wildcards: {', '.join(parsed.wildcards)}")
        
        if parsed.filters:
            filter_strs = [f"{k}:{v}" for k, v in parsed.filters.items()]
            parts.append(f"Filters: {', '.join(filter_strs)}")
        
        return " | ".join(parts)


# Example usage
if __name__ == "__main__":
    parser = QueryParser()
    
    # Test queries
    test_queries = [
        'python programming',
        '"machine learning" tutorial',
        'python AND tutorial NOT beginner',
        'site:github.com python',
        'python* tutorial',
        'python OR java AND tutorial',
        '+python -java tutorial',
        '"exact phrase" site:example.com filetype:pdf',
        'machine learning date:2024 lang:en'
    ]
    
    print("="*60)
    print("Query Parser Examples")
    print("="*60)
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        
        # Validate
        is_valid, error = parser.validate_query(query)
        if not is_valid:
            print(f"  ✗ Invalid: {error}")
            continue
        
        # Parse
        parsed = parser.parse(query)
        
        # Explain
        print(f"  Explanation: {parser.explain_query(parsed)}")
        
        if not parsed.is_simple:
            if parsed.must_have:
                print(f"  Must have: {parsed.must_have}")
            if parsed.must_not_have:
                print(f"  Must NOT have: {parsed.must_not_have}")
            if parsed.filters:
                print(f"  Filters: {parsed.filters}")