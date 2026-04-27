"""Translation Class
- Handles translation of data structures while preserving non-string values -> using Depth First Search (DFS)
- Supports Google and Bhashini APIs.
- Can exclude specific keys from translation.
"""
import os
import re
import json
import time
import asyncio
import httpx
import logging
from dotenv import load_dotenv
from typing import Any, Dict, List, Tuple, Union, Set

logger = logging.getLogger(__name__)

load_dotenv(override=True)

term_pairs = json.load(open('assets/glossary_terms.json', 'r', encoding='utf-8'))

def fix_underscores(text):
    """Replace underscores with spaces -> underscores."""
    if isinstance(text, str):
        text = re.sub(r'[_] [_]', '__', text)
        text = re.sub(r'[_] [_]', '__', text)
    return text





def add_marathi_terms(text: str, term_pairs=term_pairs) -> str:
    """
    Add Marathi translations in brackets for matching English terms in the text.
    Example: "Click the button" -> "Click (क्लिक) the button (बटण)"
    
    Args:
        text: English text to process
        term_pairs: List of dictionaries with 'en' and 'mr' keys for term pairs
        
    Returns:
        Text with Marathi translations added in brackets for matching terms
    """
    if not text or not term_pairs:
        return text

    # Extract valid English-Marathi pairs and sort by length
    valid_terms = []
    for term in term_pairs:
        en_term = term.get('en', '').strip()
        mr_term = term.get('mr', '').strip()
        
        if not en_term or not mr_term:
            continue
            
        # Normalize whitespace
        en_term = ' '.join(en_term.split())
        mr_term = ' '.join(mr_term.split())
        valid_terms.append((en_term, mr_term))
    
    # Sort by length (longest first) to handle overlapping terms
    valid_terms.sort(key=lambda x: len(x[0]), reverse=True)
    
    if not valid_terms:
        return text

    # Create pattern parts and mapping
    pattern_parts = []
    term_mapping = {}  # English lowercase -> Marathi
    case_mapping = {}  # English lowercase -> English original case
    
    for en_term, mr_term in valid_terms:
        try:
            # Escape special regex characters
            escaped_term = re.escape(en_term)
            pattern_parts.append(escaped_term)
            
            # Store mappings
            term_mapping[en_term.lower()] = mr_term
            case_mapping[en_term.lower()] = en_term
        except Exception:
            continue

    if not pattern_parts:
        return text

    try:
        # Compile pattern with word boundaries
        pattern = r'(?:(?<=\s)|^)(?:' + '|'.join(pattern_parts) + r')(?=\s|$)'
        compiled_pattern = re.compile(pattern, re.IGNORECASE)
    except re.error:
        # Fallback to simpler pattern
        pattern = r'\b(?:' + '|'.join(pattern_parts) + r')\b'
        compiled_pattern = re.compile(pattern, re.IGNORECASE)

    def replace_match(match):
        """Replace matched English term with "term (मराठी शब्द)" """
        term = match.group(0)
        lookup_term = term.strip().lower()
        
        marathi = term_mapping.get(lookup_term, '')
        if marathi:
            original_case = case_mapping.get(lookup_term, term)
            return f"{original_case} ({marathi})"
        return term

    try:
        return compiled_pattern.sub(replace_match, text)
    except Exception:
        return text

class BaseTranslator:
    """Base translator class with common data handling methods."""
    def __init__(self, source_lang='en', target_lang='hi', batch_size=4, term_pairs=None):
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.batch_size = batch_size
        self.term_pairs = term_pairs or []
        self._compiled_pattern = None
        self._term_mapping = {}
        self._case_mapping = {}  # Maps lowercase to original case
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Pre-compile regex patterns and build term mapping for efficient replacements."""
        if not self.term_pairs:
            return

        # Filter valid terms and sort by length (longest first)
        valid_terms = []
        for term in self.term_pairs:
            source = term.get(self.source_lang, '').strip()
            target = term.get(self.target_lang, '').strip()
            
            # Skip invalid or empty terms
            if not source or not target:
                continue
                
            # Handle potential Unicode characters and normalize whitespace
            source = ' '.join(source.split())  # Normalize whitespace
            target = ' '.join(target.split())  # Normalize whitespace
            
            valid_terms.append((source, target))
            
        # Sort by length (longest first) to handle overlapping terms correctly
        valid_terms.sort(key=lambda x: len(x[0]), reverse=True)
        
        if not valid_terms:
            return

        # Create pattern parts and mapping
        pattern_parts = []
        for source, target in valid_terms:
            try:
                # Double escape backslashes first to handle Windows paths or similar
                source_escaped = source.replace('\\', '\\\\')
                # Then escape all regex special characters
                escaped_source = re.escape(source_escaped)
                pattern_parts.append(escaped_source)
                
                # Store lowercase version in term_mapping
                self._term_mapping[source.lower()] = target
                # Store original case in case_mapping
                self._case_mapping[source.lower()] = source
            except Exception as e:
                # Skip problematic patterns but continue processing others
                continue

        # Compile single pattern with word boundaries
        if pattern_parts:
            try:
                # Use lookaround assertions for better word boundary handling with case insensitive flag
                pattern = r'(?:(?<=\s)|^)(?:' + '|'.join(pattern_parts) + r')(?=\s|$)'
                self._compiled_pattern = re.compile(pattern, re.IGNORECASE)
            except re.error:
                # Fallback to simpler pattern if complex one fails
                pattern = r'\b(?:' + '|'.join(pattern_parts) + r')\b'
                self._compiled_pattern = re.compile(pattern, re.IGNORECASE)

    def _should_skip_path(self, path: List[Union[str, int]], exclude_keys: Set[str] = None) -> bool:
        """
        Determine if a path should be skipped based on excluded keys.
        """
        if not exclude_keys:
            return False
        return any(str(key) in exclude_keys for key in path)
        
    def _should_translate_string(self, text: str) -> bool:
        """
        Determine if a string should be translated based on its content.
        Skip strings that only contain whitespace or non-alphanumeric characters.
        """
        # Skip empty strings
        if not text or text.isspace():
            return False
            
        # Check if the string contains any alphanumeric characters
        return any(char.isalnum() for char in text)

    def _add_paired_translations(self, text: str) -> str:
        """Add translations in parentheses for dictionary terms using pre-compiled pattern."""
        if not self._compiled_pattern or not self._term_mapping:
            return text

        def replace_match(match):
            """Replace matched term with term (translation)"""
            term = match.group(0)
            # Handle potential leading/trailing whitespace
            lookup_term = term.strip().lower()
            
            translation = self._term_mapping.get(lookup_term, '')
            if translation:
                # Use original case if available, otherwise use matched case
                original_case = self._case_mapping.get(lookup_term, term)
                return f"{original_case} ({translation})"
            return term

        try:
            return self._compiled_pattern.sub(replace_match, text)
        except Exception:
            # Fallback to original text if replacement fails
            return text

    async def translate_texts(self, texts: List[str]) -> List[str]:
        """Abstract method to be implemented by concrete translators."""
        raise NotImplementedError("translate_texts method must be implemented by subclasses.")

    def _collect_translatable_strings(self, data: Any, exclude_keys: Set[str] = None) -> List[Tuple[List[Union[str, int]], str]]:
        """First pass: Collect all translatable strings with their paths."""
        strings_to_translate = []
        
        def dfs(current_data: Any, current_path: List[Union[str, int]]) -> None:
            # Skip this branch if the current path contains an excluded key
            if self._should_skip_path(current_path, exclude_keys):
                return

            if isinstance(current_data, str):
                # Only add strings that should be translated
                if self._should_translate_string(current_data):
                    strings_to_translate.append((current_path.copy(), current_data))
            elif isinstance(current_data, dict):
                for key, value in current_data.items():
                    current_path.append(key)
                    dfs(value, current_path)
                    current_path.pop()
            elif isinstance(current_data, list):
                for idx, item in enumerate(current_data):
                    current_path.append(idx)
                    dfs(item, current_path)
                    current_path.pop()

        dfs(data, [])
        return strings_to_translate

    def _reconstruct_data(self, original_data: Any, translated_strings: List[str], 
                         paths: List[List[Union[str, int]]]) -> Any:
        """Second pass: Reconstruct the original structure with translated strings."""
        if not paths:  # If no paths, return original data unchanged
            return original_data

        # Create a deep copy of the original data
        result = self._deep_copy(original_data)
        
        # Create a mapping of translations - convert paths to tuples for hashing
        translations = dict(zip(map(tuple, paths), translated_strings))
        
        # Reconstruct the data structure
        for path, translated_text in translations.items():
            current = result
            for i, key in enumerate(path[:-1]):
                current = current[key]
            current[path[-1]] = translated_text
            
        return result

    def _deep_copy(self, data: Any) -> Any:
        """Create a deep copy of the data structure."""
        if isinstance(data, dict):
            return {k: self._deep_copy(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._deep_copy(item) for item in data]
        else:
            return data

    async def translate(self, data: Any, exclude_keys: Set[str] = None, use_term_pairs: bool = False) -> Any:
        """
        Translate any data structure while preserving structure and non-string values.
        Handles single strings, lists, dictionaries, and nested structures.
        
        Args:
            data: The data to translate
            exclude_keys: Set of keys to exclude from translation
            use_term_pairs: Whether to add paired translations before translation
        """
        # Handle simple string case directly
        if isinstance(data, str):
            if not exclude_keys and self._should_translate_string(data):
                text = self._add_paired_translations(data) if use_term_pairs else data
                return (await self.translate_texts([text]))[0]
            return data
            
        # Collect all translatable strings with their paths
        paths_and_strings = self._collect_translatable_strings(data, exclude_keys)
        
        if not paths_and_strings:
            return data
            
        # Separate paths and strings
        paths, strings = zip(*paths_and_strings)
        
        # Apply paired translations if requested
        if use_term_pairs:
            strings = [self._add_paired_translations(text) for text in strings]
        
        # Batch translate all strings at once
        translated_strings = await self.translate_texts(list(strings))
        
        # Reconstruct the data structure with translations
        return self._reconstruct_data(data, translated_strings, paths)


class BhashiniTranslator(BaseTranslator):
    """Translator implementation using the Bhashini API."""

    BHILI_SERVICE_ID = "bhashini/ai4b/bhili-nmt"
    DEFAULT_SERVICE_ID = "bhashini/ai4bharat/indictrans-v3"

    def __init__(self, source_lang='en', target_lang='hi', batch_size=4, term_pairs=None):
        super().__init__(source_lang, target_lang, batch_size, term_pairs)
        self.api_key = os.getenv("MEITY_API_KEY_VALUE")
        self.base_url = 'https://dhruva-api.bhashini.gov.in/services/inference/pipeline'

    def _get_service_id(self, source_lang: str, target_lang: str) -> str:
        if source_lang == "bhb" or target_lang == "bhb":
            return self.BHILI_SERVICE_ID
        return self.DEFAULT_SERVICE_ID

    async def translate_texts(self, texts: List[str]) -> List[str]:
        """Translate a list of texts using the Bhashini API."""
        headers = {
            'Authorization': self.api_key,
            'Content-Type': 'application/json'
        }
        service_id = self._get_service_id(self.source_lang, self.target_lang)
        data = {
            "pipelineTasks": [
                {
                    "taskType": "translation",
                    "config": {
                        "serviceId": service_id,
                        "language": {
                            "sourceLanguage": self.source_lang,
                            "targetLanguage": self.target_lang
                        }
                    }
                }
            ],
            "inputData": {
                "input": [{"source": text} for text in texts]
            }
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(self.base_url, headers=headers, json=data)

        if response.status_code != 200:
            raise Exception(f"Error: {response.status_code} {response.text}")

        response_json = response.json()
        return [item['target'] for item in response_json['pipelineResponse'][0]['output']]

    async def translate_text(self, text: str, source_lang: str, target_lang: str, max_retries: int = 3) -> str:
        """Translate a single text with per-call language pair and retry logic, handling markdown."""
        if source_lang == target_lang or not text:
            return text

        # 1. Clean markdown formatting that causes Bhili NMT to hallucinate
        if source_lang == "bhb" or target_lang == "bhb":
            text = re.sub(r'[*_`#]', '', text)

        # 2. Split into lines to preserve structure and avoid long-text NMT drops
        lines = text.split('\n')
        texts_to_translate = []
        prefixes = []

        for line in lines:
            if not line.strip():
                continue
            # Preserve bullet points/numbering by extracting prefix
            match = re.match(r'^(\s*(?:[-+]|\d+\.)\s+)(.*)', line)
            prefix, content = match.groups() if match else ("", line)
            
            if content.strip():
                texts_to_translate.append(content.strip())
                prefixes.append(prefix)

        if not texts_to_translate:
            return text

        headers = {
            'Authorization': self.api_key,
            'Content-Type': 'application/json'
        }
        service_id = self._get_service_id(source_lang, target_lang)
        data = {
            "pipelineTasks": [
                {
                    "taskType": "translation",
                    "config": {
                        "serviceId": service_id,
                        "language": {
                            "sourceLanguage": source_lang,
                            "targetLanguage": target_lang
                        }
                    }
                }
            ],
            "inputData": {
                "input": [{"source": t} for t in texts_to_translate]
            }
        }

        last_error = None
        translated_texts = texts_to_translate # fallback
        
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(self.base_url, headers=headers, json=data)
                    response.raise_for_status()
                    result = response.json()
                    translated_texts = [item['target'] for item in result['pipelineResponse'][0]['output']]
                    break
            except (httpx.HTTPError, KeyError, IndexError) as e:
                last_error = e
                if attempt < max_retries - 1:
                    delay = 2 ** attempt
                    logger.warning(
                        "Translation attempt %d/%d failed for %s→%s: %s. Retrying in %ds...",
                        attempt + 1, max_retries, source_lang, target_lang, e, delay,
                    )
                    await asyncio.sleep(delay)
        else:
            logger.error(
                "Translation failed after %d retries for %s→%s: %s. Returning original text.",
                max_retries, source_lang, target_lang, last_error,
            )

        # 3. Reconstruct
        result_lines = []
        t_idx = 0
        for line in lines:
            if not line.strip():
                result_lines.append(line)
                continue
                
            match = re.match(r'^(\s*(?:[-+]|\d+\.)\s+)(.*)', line)
            _, content = match.groups() if match else ("", line)
            
            if content.strip():
                translated = translated_texts[t_idx] if t_idx < len(translated_texts) else content
                result_lines.append(f"{prefixes[t_idx]}{translated}")
                t_idx += 1
            else:
                result_lines.append(line)

        return '\n'.join(result_lines)


translation_service = BhashiniTranslator()