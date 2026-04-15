"""
Marqo client implementation for vector search.
"""
import os
import re
import marqo
from typing import Optional, Literal
from pydantic import BaseModel, Field
from pydantic_ai import ModelRetry, RunContext
from agents.deps import FarmerContext
from helpers.utils import get_logger
from agents.tools.terms import normalize_text_with_glossary

logger = get_logger(__name__)

DocumentType = Literal['video', 'document']

# Mapping of English document/source names to Devanagari equivalents
# Used so source citations appear in the response language, not English
DOCUMENT_NAME_DEVANAGARI = {
    # Maharashtra Agricultural Universities
    "Dr. Panjabrao Deshmukh Krishi Vidyapeeth": "डॉ. पंजाबराव देशमुख कृषी विद्यापीठ, अकोला",
    "Dr. Panjabrao Deshmukh Krishi Vidyapeeth, Akola": "डॉ. पंजाबराव देशमुख कृषी विद्यापीठ, अकोला",
    "MPKV Krishi Darshani": "महात्मा फुले कृषी विद्यापीठ (MPKV) कृषी दर्शनी",
    "MPKV Research Recommendation 2023 Rahuri": "MPKV संशोधन शिफारसी २०२३, राहुरी",
    "MPKV Research Recommendation 2024 Rahuri": "MPKV संशोधन शिफारसी २०२४, राहुरी",
    "MPKV": "महात्मा फुले कृषी विद्यापीठ (MPKV), राहुरी",
    "Krushi VNMAU": "वसंतराव नाईक मराठवाडा कृषी विद्यापीठ (VNMAU)",
    "VNMAU": "वसंतराव नाईक मराठवाडा कृषी विद्यापीठ (VNMAU)",
    "VNMKV Parbhani": "वसंतराव नाईक मराठवाडा कृषी विद्यापीठ, परभणी",
    "VNMKV": "वसंतराव नाईक मराठवाडा कृषी विद्यापीठ, परभणी",
    "Krishi Darshani Dr BSKKV, Dapoli 2025": "डॉ. बाळासाहेब सावंत कोकण कृषी विद्यापीठ, दापोली — कृषी दर्शनी २०२५",
    "Dr BSKKV, Dapoli 2025": "डॉ. बाळासाहेब सावंत कोकण कृषी विद्यापीठ, दापोली २०२५",
    "Sugarcane MPKV Rahuri": "ऊस — MPKV राहुरी",
    "Wheat MPKV Rahuri": "गहू — MPKV राहुरी",

    # Maharashtra State Projects & Departments
    "NDKSP": "नानाजी देशमुख कृषी संजीवनी प्रकल्प (NDKSP)",
    "Department of Animal Husbandry,Maharashtra": "पशुसंवर्धन विभाग, महाराष्ट्र",
    "Department of Education, Maharashtra": "शिक्षण विभाग, महाराष्ट्र",
    "Department of Animal Husbandry and Dairying GOM": "पशुसंवर्धन व दुग्धव्यवसाय विभाग, महाराष्ट्र शासन",

    # Central Government Departments
    "Department of Agriculture & Cooperation, Government of India ": "कृषी व सहकार विभाग, भारत सरकार",
    "Department of Agriculture & Cooperation, Government of India": "कृषी व सहकार विभाग, भारत सरकार",
    "Department of Animal Husbandry and Dairying ,Government of India ": "पशुसंवर्धन व दुग्धव्यवसाय विभाग, भारत सरकार",
    "Department of Animal Husbandry and Dairying ,Government of India": "पशुसंवर्धन व दुग्धव्यवसाय विभाग, भारत सरकार",
    "Department of Agriculture and Farmers Welfare (DAFW)": "कृषी व शेतकरी कल्याण विभाग (DAFW)",
    "Department of Agriculture & Farmers Welfare, Government of India ": "कृषी व शेतकरी कल्याण विभाग, भारत सरकार",
    "Department of Agriculture & Farmers Welfare, Government of India": "कृषी व शेतकरी कल्याण विभाग, भारत सरकार",
    "Department of Agriculture, Cooperation & Farmers Welfare, Government of India ": "कृषी, सहकार व शेतकरी कल्याण विभाग, भारत सरकार",
    "Department of Agriculture, Cooperation & Farmers Welfare, Government of India": "कृषी, सहकार व शेतकरी कल्याण विभाग, भारत सरकार",
    "Department of Agriculture & Cooperation and Department of Information Technology , Government of India ": "कृषी व सहकार विभाग आणि माहिती तंत्रज्ञान विभाग, भारत सरकार",
    "Department of Animal Husbandry, Dairying & Fisheries, Ministry of Agriculture & Farmers Welfare, Government of India": "पशुसंवर्धन, दुग्धव्यवसाय व मत्स्यव्यवसाय विभाग, कृषी व शेतकरी कल्याण मंत्रालय, भारत सरकार",
    "Department of Agriculture & Farmers Welfare \nMinistry of Agriculture & Farmers Welfare \nGovernment of India  ": "कृषी व शेतकरी कल्याण विभाग, कृषी व शेतकरी कल्याण मंत्रालय, भारत सरकार",
    "GOVERNMENT OF INDIA Ministry of Commerce & Industry Department of Commerce": "भारत सरकार, वाणिज्य व उद्योग मंत्रालय, वाणिज्य विभाग",
    "GOI": "भारत सरकार",
    "Krishi Bhavan, New Delhi": "कृषी भवन, नवी दिल्ली",

    # ICAR & Research Centres
    "Indian Council of Agricultural Research, New Delhi": "भारतीय कृषी संशोधन परिषद (ICAR), नवी दिल्ली",
    "Indian Council of Agricultural Research": "भारतीय कृषी संशोधन परिषद (ICAR)",
    "ICAR": "भारतीय कृषी संशोधन परिषद (ICAR)",
    "ICAR DOGR": "ICAR — कांदा व लसूण संशोधन संचालनालय (DOGR)",
    "Central Research Centre on Goats (CIRG), Makhdoom": "केंद्रीय शेळी संशोधन संस्था (CIRG), मखदूम",
    "Directorate of Poultry Research, Hyderabad": "कुक्कुटपालन संशोधन संचालनालय, हैदराबाद",
    "GAVASU, Ludhiana": "गुरू अंगद देव पशुवैद्यकीय व प्राणी विज्ञान विद्यापीठ (GAVASU), लुधियाना",

    # National Boards & Missions
    "National Dairy Development Board": "राष्ट्रीय दुग्ध विकास मंडळ (NDDB)",
    "National Dairy Development Board website": "राष्ट्रीय दुग्ध विकास मंडळ (NDDB)",
    "National Bee Board, New Delhi": "राष्ट्रीय मधुमक्षिका मंडळ, नवी दिल्ली",
    "National Bamboo Mission, New Delhi": "राष्ट्रीय बांबू मिशन, नवी दिल्ली",
    "National Biodiversity Authority": "राष्ट्रीय जैवविविधता प्राधिकरण",
    "Rashtriya Krishi Vikas Yojana": "राष्ट्रीय कृषी विकास योजना (RKVY)",
    "NFDB, Hyderabad": "राष्ट्रीय मत्स्यव्यवसाय विकास मंडळ (NFDB), हैदराबाद",

    # Training & Other
    "MANAGE, Hyderabad": "राष्ट्रीय कृषी विस्तार व्यवस्थापन संस्था (MANAGE), हैदराबाद",
    "Aquaculture Department Southeast Asian Fisheries Development Center": "जलचर संवर्धन विभाग, आग्नेय आशियाई मत्स्यव्यवसाय विकास केंद्र",
    "Multi-sourced": "बहु-स्रोत",
}


class SearchHit(BaseModel):
    """Individual search hit from elasticsearch"""
    name: str
    text: str
    doc_id: str
    type: str
    source: str
    score: float = Field(alias="_score")
    id: str = Field(alias="_id")
    lang_code: str = Field(default="mr")

    @property
    def processed_name(self) -> str:
        """Returns the document name in Devanagari if a mapping exists, otherwise as-is."""
        return DOCUMENT_NAME_DEVANAGARI.get(self.name, self.name)

    @property
    def processed_text(self) -> str:
        """Returns the text with cleaned up whitespace and newlines"""
        cleaned = re.sub(r'\n{2,}', '\n\n', self.text)
        cleaned = re.sub(r'\t+', '\t', cleaned)
        if self.lang_code != "en":
            cleaned = normalize_text_with_glossary(cleaned, target_lang="hi")
        return cleaned

    def __str__(self) -> str:
        if self.type == 'document':
            return f"**{self.processed_name}**\n" + "```\n" + self.processed_text + "\n```\n"
        else:
            return f"**[{self.processed_name}]({self.source})**\n" + "```\n" + self.processed_text + "\n```\n"


async def search_documents(
    ctx: RunContext[FarmerContext],
    query: str,
    top_k: int = 10,
) -> str:
    """
    Semantic search for documents. Use this tool to search for relevant documents.
    
    Args:
        query: The search query in *English* (required)
        top_k: Maximum number of results to return (default: 10)
        
    Returns:
        search_results: Formatted list of documents
    """
    try:
        # Initialize Marqo client
        endpoint_url = os.getenv('MARQO_ENDPOINT_URL')
        if not endpoint_url:
            raise ValueError("Marqo endpoint URL is required")
        
        index_name = os.getenv('MARQO_INDEX_NAME', 'sunbird-va-index')
        if not index_name:
            raise ValueError("Marqo index name is required")
        
        client = marqo.Client(url=endpoint_url)
        logger.info(f"Searching for '{query}' in index '{index_name}'")

        search_params = {
            "q": query,
            "limit": top_k,
            "filter_string": "type:document",
            "search_method": "hybrid",
            "hybrid_parameters": {
                "retrievalMethod": "disjunction",
                "rankingMethod": "rrf",
                "alpha": 0.5,
                "rrfK": 60,
            },        
        }
        
        results = client.index(index_name).search(**search_params)['hits']
        
        if len(results) == 0:
            return f"No results found for `{query}`"
        else:
            lang_code = ctx.deps.lang_code
            search_hits = [SearchHit(**hit, lang_code=lang_code) for hit in results]
            document_string = '\n\n----\n\n'.join([str(document) for document in search_hits])
            return "> Search Results for `" + query + "`\n\n" + document_string
    except Exception as e:
        logger.error(f"Error searching documents: {e} for query: {query}")
        raise ModelRetry(f"Error searching documents, please try again")


async def search_videos(
    ctx: RunContext[FarmerContext],
    query: str,
    top_k: int = 3,
) -> str:
    """
    Semantic search for videos. Use this tool when recommending videos to the farmer.
    
    Args:
        query: The search query in *English* (required)
        top_k: Maximum number of results to return (default: 3)
        
    Returns:
        search_results: Formatted list of videos
    """
    try:
        # Initialize Marqo client
        endpoint_url = os.getenv('MARQO_ENDPOINT_URL')
        if not endpoint_url:
            raise ValueError("Marqo endpoint URL is required")
        
        index_name = os.getenv('MARQO_INDEX_NAME', 'sunbird-va-index')
        if not index_name:
            raise ValueError("Marqo index name is required")
        
        client = marqo.Client(url=endpoint_url)
        logger.info(f"Searching for '{query}' in index '{index_name}'")
        
        # Perform search using just tensor search
        search_params = {
            "q": query,
            "limit": top_k,
            "filter_string": "type:video",
            "search_method": "tensor",
        }
        
        results = client.index(index_name).search(**search_params)['hits']
        
        if len(results) == 0:
            return f"No videos found for `{query}`"
        else:
            lang_code = ctx.deps.lang_code
            search_hits = [SearchHit(**hit, lang_code=lang_code) for hit in results]
            video_string = '\n\n----\n\n'.join([str(document) for document in search_hits])
            return "> Videos for `" + query + "`\n\n" + video_string
        
    except Exception as e:
        logger.error(f"Error searching documents: {e} for query: {query}")
        raise ModelRetry(f"Error searching documents, please try again")