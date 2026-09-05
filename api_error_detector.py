#!/usr/bin/env python3
"""
API Error Detection Module for ISEE Framework

This module provides sophisticated error detection to distinguish between
API failures and legitimate responses, preventing error messages from being
scored as content.
"""

import re
import json
from typing import Dict, Any, Tuple, Optional

class APIErrorDetector:
    """Detects and classifies API errors vs legitimate responses."""
    
    def __init__(self):
        # Common error patterns in API responses
        self.error_patterns = [
            # OpenRouter specific errors
            r'{"error":\s*{[^}]*"message":\s*"[^"]*"[^}]*}}',
            r'"error":\s*{[^}]*"code":\s*\d+[^}]*}',
            r'Provider returned error',
            r'OpenAI is requiring a key',
            r'is not a valid model ID',
            r'Your organization must be verified',
            
            # Globant Enterprise AI specific errors
            r'Globant Enterprise AI error',
            r'Organization ID not found',
            r'Invalid organization credentials',
            r'Enterprise API access denied',
            r'Globant API key invalid',
            r'Organization quota exceeded',
            r'Enterprise model not available',
            r'Unauthorized organization access',
            # Phrase-level, not word-level. Removing 'organization' and 'enterprise'
            # from the keyword list stopped the detector discarding ordinary prose --
            # and took this real Globant refusal with it, which the Globant test
            # caught immediately. The shape of the sentence is what identifies it;
            # the individual words never did.
            r'organization does not have access',
            r'does not have access to this enterprise',
            r'organization .{0,40}not (?:have|been granted) access',
            
            # HTTP error patterns
            r'Error \d{3}:',
            r'HTTP \d{3}',
            r'status code \d{3}',
            
            # Generic API error patterns
            r'API error:',
            r'Request failed:',
            r'Authentication failed',
            r'Rate limit exceeded',
            r'Quota exceeded',
            r'Invalid request',
            r'Service unavailable',
            r'Internal server error',
            
            # Exception patterns
            r'Exception:',
            r'Traceback',
            r'Error generating response:',
            
            # Short suspicious responses (likely errors)
            r'^.{1,200}$',  # Very short responses are often errors
        ]
        
        # Compile patterns for efficiency
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE | re.DOTALL) 
                                for pattern in self.error_patterns]
        
        # Known error message characteristics
        self.error_indicators = [
            'error',
            'failed',
            'invalid',
            'unauthorized', 
            'forbidden',
            'timeout',
            'exception',
            'not found',
            'bad request',
            'service unavailable',
            # Globant-specific error indicators.
            #
            # 'organization' and 'enterprise' used to sit here. They are not error
            # terms — they are ordinary business vocabulary, and Globant's actual
            # error strings ("Organization ID not found", "Enterprise API access
            # denied") already have their own explicit patterns above, which match
            # the whole phrase rather than one word out of it.
            'globant',
            'quota exceeded',
            'access denied',
            'credentials'
        ]
        
        # Whole words only. `'organizational'` must not count as `'organization'`,
        # and `'errors'` must not count as `'error'`.
        self._indicator_patterns = [
            re.compile(r"\b" + re.escape(indicator) + r"\b", re.IGNORECASE)
            for indicator in self.error_indicators
        ]

        # Response length thresholds
        self.min_valid_length = 50  # Responses shorter than this are suspect
        self.max_error_length = 500  # Error messages are usually short

    #: A response is treated as prose -- and therefore exempt from the vocabulary
    #: heuristic -- once it carries this many sentences and this many words. Both
    #: are deliberately low: the point is to exclude fragments, not to require an
    #: essay. A provider error body clears neither.
    PROSE_MIN_SENTENCES = 2
    PROSE_MIN_WORDS = 15

    @classmethod
    def _reads_as_prose(cls, text: str) -> bool:
        """Does this look like something a model wrote, rather than an error body?

        Error bodies are fragments: a status line, a JSON object, a single clause.
        Answers are sentences. This is a coarse test on purpose -- it decides only
        whether the error-vocabulary count is allowed to apply, and everything
        structural (JSON errors, provider patterns, HTTP status) runs before it and
        is unaffected.
        """
        sentences = len(re.findall(r"[.!?](?:\s|$)", text))
        words = len(re.findall(r"\b\w+\b", text))
        return sentences >= cls.PROSE_MIN_SENTENCES and words >= cls.PROSE_MIN_WORDS
        
    def is_api_error(self, response_text: str, metadata: Optional[Dict[str, Any]] = None) -> Tuple[bool, str]:
        """
        Determine if a response is an API error rather than legitimate content.
        
        Args:
            response_text: The response text to analyze
            metadata: Optional metadata about the API call
            
        Returns:
            Tuple of (is_error: bool, reason: str)
        """
        if not response_text or not isinstance(response_text, str):
            return True, "Empty or invalid response"
        
        response_lower = response_text.lower().strip()
        response_length = len(response_text.strip())
        
        # Check for JSON error structures
        if self._is_json_error(response_text):
            return True, "JSON error structure detected"
        
        # Check for explicit error patterns
        for i, pattern in enumerate(self.compiled_patterns[:-1]):  # Exclude length pattern
            if pattern.search(response_text):
                return True, f"Error pattern match: {self.error_patterns[i][:50]}..."
        
        # Check response length (very short responses are often errors)
        if response_length < self.min_valid_length:
            # But allow short responses if they don't contain error indicators
            if any(p.search(response_lower) for p in self._indicator_patterns):
                return True, f"Short response ({response_length} chars) with error indicators"
            elif response_length < 20:  # Extremely short responses are almost always errors
                return True, f"Extremely short response ({response_length} chars)"
        
        # Check for a high concentration of error keywords -- but only in text that
        # does not read as prose.
        #
        # A provider's error body is a fragment: a status line, a JSON blob, a clause
        # without a subject. A model's answer is prose, and this tool explicitly
        # commissions prose about what goes wrong -- the critical, contrarian and
        # first-principles frameworks ask for exactly that. Counting error vocabulary
        # in prose therefore measures the topic, not the outcome.
        #
        # Measured on 03.09.2026, before this gate: "A blameless post-mortem culture
        # reduces repeat failures. When an error occurs, the team documents the
        # timeout and the failed request without assigning blame." was reported as an
        # API error on three keywords -- and main.py:1480 turns that verdict into a
        # recorded failure, so the answer never reaches scoring or the synthesis.
        if not self._reads_as_prose(response_text):
            error_keyword_count = sum(
                1 for pattern in self._indicator_patterns
                if pattern.search(response_lower)
            )
            if error_keyword_count >= 2 and response_length < self.max_error_length:
                return True, f"Multiple error keywords ({error_keyword_count}) in short response"
        
        # Check for metadata indicators
        if metadata:
            if metadata.get('status_code', 200) != 200:
                return True, f"HTTP error status: {metadata.get('status_code')}"
            
            if metadata.get('error', False):
                return True, "Metadata indicates error"
        
        return False, "Response appears to be legitimate content"
    
    def _is_json_error(self, response_text: str) -> bool:
        """Check if response is a JSON error structure."""
        try:
            parsed = json.loads(response_text.strip())
            
            # Check for common error structures
            if isinstance(parsed, dict):
                # OpenRouter/OpenAI style errors
                if 'error' in parsed:
                    return True
                
                # Generic error structures
                if any(key in parsed for key in ['error_message', 'error_code', 'message', 'detail']):
                    error_values = [str(v).lower() for k, v in parsed.items() 
                                  if k in ['error_message', 'error_code', 'message', 'detail']]
                    if any(indicator in ' '.join(error_values) 
                          for indicator in self.error_indicators):
                        return True
            
            return False
            
        except (json.JSONDecodeError, TypeError):
            # Not valid JSON, continue with other checks
            return False
    
    def get_error_summary(self, response_text: str) -> Dict[str, Any]:
        """Get a detailed analysis of potential error response."""
        is_error, reason = self.is_api_error(response_text)
        
        return {
            'is_error': is_error,
            'reason': reason,
            'response_length': len(response_text.strip()),
            'contains_json': self._looks_like_json(response_text),
            'error_keywords_found': [indicator for indicator in self.error_indicators 
                                   if indicator in response_text.lower()],
            'response_preview': response_text[:100] + ('...' if len(response_text) > 100 else '')
        }
    
    def _looks_like_json(self, text: str) -> bool:
        """Check if text looks like JSON."""
        text = text.strip()
        return (text.startswith('{') and text.endswith('}')) or \
               (text.startswith('[') and text.endswith(']'))

def test_error_detector():
    """Test the error detector with known examples."""
    detector = APIErrorDetector()
    
    test_cases = [
        # Known errors from our analysis
        ('{"error":{"message":"deepseek/r1 is not a valid model ID","code":400}}', True),
        ('{"error":{"message":"OpenAI is requiring a key to access this model","code":403}}', True),
        ('Error 403: Forbidden', True),
        ('Exception: Request failed', True),
        
        # Valid responses
        ('This is a legitimate response about quantum computing and blockchain security that contains substantial content and analysis.', False),
        ('The answer to your question involves several considerations...', False),
        
        # Edge cases
        ('OK', True),  # Too short
        ('Error', True),  # Error keyword + short
        ('This response mentions an error but is otherwise legitimate content about error handling in software development.', False),
    ]
    
    print("🧪 Testing API Error Detector")
    print("=" * 50)
    
    for i, (text, expected) in enumerate(test_cases, 1):
        is_error, reason = detector.is_api_error(text)
        status = "✅ PASS" if is_error == expected else "❌ FAIL"
        
        print(f"Test {i}: {status}")
        print(f"  Text: {text[:60]}{'...' if len(text) > 60 else ''}")
        print(f"  Expected: {expected}, Got: {is_error}")
        print(f"  Reason: {reason}")
        print()

if __name__ == "__main__":
    test_error_detector()