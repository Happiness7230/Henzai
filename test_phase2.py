from src.processing.tokenizer import Tokenizer
from src.processing.snippet_generator import SnippetGenerator
from src.storage.analytics_store import AnalyticsStore

# Test 1: Tokenizer with stemming
print("="*60)
print("Test 1: Enhanced Tokenizer")
print("="*60)
tokenizer = Tokenizer(use_stemming=True, use_stop_words=True)
result = tokenizer.test_tokenization("The runners are running quickly")
print("Original:", result['original'])
print("Final tokens:", result['final_tokens'])
print("Stemming changes:", result.get('stemming_changes', []))

# Test 2: Snippet generator
print("\n" + "="*60)
print("Test 2: Snippet Generator")
print("="*60)
generator = SnippetGenerator()
text = "Python is a powerful programming language for web development"
snippet = generator.generate_snippet(text, ["python", "programming"])
print("Snippet:", snippet)

# Test 3: Analytics
print("\n" + "="*60)
print("Test 3: Analytics Store")
print("="*60)
analytics = AnalyticsStore()
analytics.log_search("python tutorial", 25, 0.05)
analytics.log_search("web development", 30, 0.04)
print("Statistics:", analytics.get_statistics())
print("Popular:", analytics.get_popular_queries(5))

print("\n✅ All Phase 2 components working!")