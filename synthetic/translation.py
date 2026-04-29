"""Translation Class
- Handles translation of data structures while preserving non-string values -> using Depth First Search (DFS)
- Supports Google and Bhashini APIs.
- Can exclude specific keys from translation.
"""
import os
import re
import json
import asyncio
import httpx
import logging
from dotenv import load_dotenv
from typing import Any, Dict, List, Tuple, Union, Set

logger = logging.getLogger(__name__)

load_dotenv(override=True)

term_pairs = json.load(open('assets/glossary_terms.json', 'r', encoding='utf-8'))

def fix_underscores(text):
    """Normalize spaced underscores to a double underscore."""
    if isinstance(text, str):
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
    """Translator implementation using the Bhashini API with chunking and paragraph-aware stitching."""

    BHILI_SERVICE_ID = "bhashini/ai4b/bhili-nmt"
    DEFAULT_SERVICE_ID = "bhashini/ai4bharat/indictrans-v3"

    MAX_CHUNK_SIZE = 400

    def __init__(self, source_lang='en', target_lang='hi', batch_size=4, term_pairs=None):
        super().__init__(source_lang, target_lang, batch_size, term_pairs)
        self.api_key = os.getenv("MEITY_API_KEY_VALUE")
        self.base_url = 'https://dhruva-api.bhashini.gov.in/services/inference/pipeline'

    def _get_service_id(self, source_lang: str, target_lang: str) -> str:
        if source_lang == "bhb" or target_lang == "bhb":
            return self.BHILI_SERVICE_ID
        return self.DEFAULT_SERVICE_ID

    # ---------------------------
    # Sentence splitting (Latin + Devanagari / danda)
    # ---------------------------
    def _split_into_sentences(self, text: str) -> List[str]:
        if not text:
            return []

        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z0-9])', text)
        if len(sentences) <= 1:
            sentences = re.split(r'(?<=[.!?।॥])\s+', text)
        if len(sentences) <= 1:
            sentences = text.split("\n")

        return [s.strip() for s in sentences if s.strip()]

    # ---------------------------
    # Chunking (no overlap — overlap caused duplicated translated spans)
    # ---------------------------
    def _chunk_text(self, text: str) -> List[Tuple[str, Dict[str, Any]]]:
        if not text or len(text) <= self.MAX_CHUNK_SIZE:
            return [(text, {"type": "full"})]

        chunks: List[Tuple[str, Dict[str, Any]]] = []
        paragraphs = re.split(r'\n\s*\n', text)

        for para_idx, paragraph in enumerate(paragraphs):
            if not paragraph.strip():
                continue

            sentences = self._split_into_sentences(paragraph.strip())
            current_chunk: List[str] = []

            for sentence in sentences:
                while len(sentence) > self.MAX_CHUNK_SIZE:
                    if current_chunk:
                        chunks.append((" ".join(current_chunk), {"para_idx": para_idx}))
                        current_chunk = []
                    chunks.append((sentence[: self.MAX_CHUNK_SIZE], {"para_idx": para_idx}))
                    sentence = sentence[self.MAX_CHUNK_SIZE :].lstrip()
                if not sentence:
                    continue
                if current_chunk and len(" ".join(current_chunk + [sentence])) > self.MAX_CHUNK_SIZE:
                    chunks.append((" ".join(current_chunk), {"para_idx": para_idx}))
                    current_chunk = []
                current_chunk.append(sentence)

            if current_chunk:
                chunks.append((" ".join(current_chunk), {"para_idx": para_idx}))

        return chunks if chunks else [(text, {"type": "fallback"})]

    def _reconstruct_translated_chunks(
        self,
        translated_chunks: List[str],
        chunks_with_metadata: List[Tuple[str, Dict[str, Any]]],
    ) -> str:
        """Join translated pieces with spaces inside a paragraph and blank lines between paragraphs."""
        if not translated_chunks or not chunks_with_metadata:
            return ""
        if len(translated_chunks) != len(chunks_with_metadata):
            logger.warning(
                "Translated chunk count mismatch (%d vs %d); joining naively.",
                len(translated_chunks),
                len(chunks_with_metadata),
            )
            return " ".join(translated_chunks)

        meta0 = chunks_with_metadata[0][1]
        if meta0.get("type") in ("full", "fallback"):
            return translated_chunks[0]

        paragraph_parts: List[str] = []
        current_para: int | None = None
        buf: List[str] = []

        for translated, (_, meta) in zip(translated_chunks, chunks_with_metadata):
            pidx = meta.get("para_idx", 0)
            t = translated.strip()
            if current_para is None:
                current_para = pidx
            if pidx != current_para:
                paragraph_parts.append(" ".join(x for x in buf if x))
                buf = []
                current_para = pidx
            if t:
                buf.append(t)
        if buf:
            paragraph_parts.append(" ".join(buf))

        return "\n\n".join(p for p in paragraph_parts if p)

    # ---------------------------
    # Batch Translation API
    # ---------------------------
    async def translate_texts(self, texts: List[str]) -> List[str]:
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

    # ---------------------------
    # Single Chunk Translation
    # ---------------------------
    async def _translate_chunk(self, text: str, source_lang: str, target_lang: str, max_retries: int) -> str:
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
                "input": [{"source": text}]
            }
        }

        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(self.base_url, headers=headers, json=data)
                    response.raise_for_status()

                    result = response.json()
                    translated = result['pipelineResponse'][0]['output'][0]['target']
                    if translated is not None and str(translated).strip():
                        return str(translated)

            except Exception as exc:
                logger.warning("Chunk translation attempt failed: %s", exc)
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)

        return text

    # ---------------------------
    # Batch Chunk Translation
    # ---------------------------
    async def _translate_chunks_batch(self, chunks: List[str], source_lang: str, target_lang: str, max_retries: int) -> List[str]:
        tasks = [
            self._translate_chunk(chunk, source_lang, target_lang, max_retries)
            for chunk in chunks
        ]

        translated = []
        for i in range(0, len(tasks), self.batch_size):
            batch = tasks[i:i + self.batch_size]
            batch_results = await asyncio.gather(*batch)
            translated.extend(batch_results)

        return translated

    # ---------------------------
    # Main Translation Entry
    # ---------------------------
    async def translate_text(self, text: str, source_lang: str, target_lang: str, max_retries: int = 3) -> str:
        if source_lang == target_lang or not text:
            return text

        # Strip light markdown for Bhili NMT — punctuation noise for the pipeline
        if source_lang == "bhb" or target_lang == "bhb":
            text = re.sub(r'[*_`#]', '', text)

        chunks_with_metadata = self._chunk_text(text)
        chunk_texts = [chunk for chunk, _ in chunks_with_metadata]

        if len(chunk_texts) == 1:
            return await self._translate_chunk(chunk_texts[0], source_lang, target_lang, max_retries)

        translated_chunks = await self._translate_chunks_batch(
            chunk_texts, source_lang, target_lang, max_retries
        )

        return self._reconstruct_translated_chunks(translated_chunks, chunks_with_metadata)