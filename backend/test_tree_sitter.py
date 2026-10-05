#!/usr/bin/env python3
"""
Test to understand tree_sitter_languages API.
"""

import sys
from tree_sitter_languages import get_parser, get_language

print("Testing tree_sitter_languages API...")

# Try to get parser for different languages
languages = ['cpp', 'c', 'java', 'python']

for lang in languages:
    print(f"\nTrying to get parser for '{lang}':")
    try:
        parser = get_parser(lang)
        print(f"  Success: Got parser for {lang}")

        # Try to get language
        language = get_language(lang)
        print(f"  Language object: {language}")

        # Test parsing simple code
        test_code = b"int main() { return 0; }"
        if lang == 'python':
            test_code = b"def main(): pass"

        tree = parser.parse(test_code)
        print(f"  Parse successful: {tree.root_node.type}")

    except Exception as e:
        print(f"  Error: {e}")
        import traceback
        traceback.print_exc()

print("\nChecking available methods...")
try:
    import inspect
    print("get_parser signature:", inspect.signature(get_parser))
    print("get_language signature:", inspect.signature(get_language))
except:
    print("Could not inspect signatures")

print("\nTesting direct tree_sitter import...")
from tree_sitter import Parser, Language

try:
    # Try to load C++ language directly
    print("Trying to create parser directly...")
    parser = Parser()

    # Try to set language
    try:
        # This is the old way - may not work
        Language.build_library('build/my-languages.so', ['tree-sitter-cpp'])
    except Exception as e:
        print(f"  Build library error: {e}")

except Exception as e:
    print(f"  Direct import error: {e}")
    import traceback
    traceback.print_exc()