"""Mock search tools (documents and videos) for Maharashtra synthetic conversations."""

import random

# Mock document snippets — realistic agricultural content for Maharashtra
_DOCUMENT_SNIPPETS = [
    ("Soybean Cultivation Guide", "Soybean is a major kharif crop in Maharashtra. Recommended varieties include JS 335, JS 9560, and MAUS 71. Sowing period: June-July. Seed rate: 60-75 kg/hectare. Row spacing: 30-45 cm."),
    ("Onion Production Technology", "Maharashtra is the largest onion producer in India. Major varieties: N-53, Baswant-780, Phule Samarth. Planting: Kharif (June-July), Late Kharif (Sept-Oct), Rabi (Nov-Dec). Spacing: 15x10 cm."),
    ("Cotton Pest Management", "Major pests of cotton in Maharashtra include American Bollworm, Pink Bollworm, and Whitefly. IPM practices: Install pheromone traps (5/ha), use Trichogramma cards, spray Neem-based pesticide at ETL."),
    ("Pomegranate Disease Management", "Bacterial Blight (Oily Spot) is the major disease of pomegranate in Maharashtra. Symptoms: oily spots on leaves and fruit. Management: Spray Streptocycline 500 ppm + Copper Oxychloride 0.3%."),
    ("Drip Irrigation for Sugarcane", "Drip irrigation in sugarcane saves 30-40% water and increases yield by 20-25%. Lateral spacing: 150 cm. Dripper spacing: 60 cm. Water requirement: 4-6 litres/day/plant during grand growth phase."),
    ("Grape Cultivation Practices", "Thompson Seedless is the most popular grape variety in Maharashtra. Pruning: October (Fruit Pruning), April (Back Pruning). Key practices: Girdling, GA3 application, Ethephon dipping."),
    ("Jowar Rabi Cultivation", "Rabi jowar is important in Marathwada and Western Maharashtra. Varieties: M 35-1, Phule Vasudha, Phule Revati. Sowing: September end to October. Seed rate: 7.5-10 kg/ha."),
    ("Soil Health Management", "Soil testing is essential before every season. Maharashtra soils are predominantly Black Cotton (Vertisol) and Red Laterite. Maintain soil pH 6.5-7.5. Apply FYM @ 10-12 tonnes/hectare."),
    ("Turmeric Processing", "After harvest, turmeric fingers are boiled, dried, and polished. Boiling: 45-60 minutes in water with sodium bicarbonate. Sun drying: 10-15 days. Polishing: manual or drum polishing."),
    ("Government Scheme - NDKSP", "Nanaji Deshmukh Krishi Sanjivani Prakalp (NDKSP) focuses on climate-resilient agriculture in PoCRA villages. Benefits include farm ponds, drip irrigation, goat rearing, and horticulture support."),
    ("Banana Tissue Culture", "Tissue culture banana (Grand Naine, G9) is widely adopted in Jalgaon district. Planting density: 1800-2200 plants/hectare. Fertigation: N:P:K = 200:50:300 g/plant/year through drip."),
    ("Integrated Pest Management", "IPM in Maharashtra focuses on: Cultural practices (crop rotation, trap crops), Biological control (Trichoderma, Pseudomonas), Chemical control as last resort with recommended doses only."),
]

_VIDEO_SNIPPETS = [
    ("शेतकऱ्यांसाठी कांदा लागवड | Onion Planting Guide", "https://example.com/video/onion-planting", "Step-by-step onion planting technique for Rabi season in Maharashtra. Covers nursery raising, transplanting, and irrigation management."),
    ("सोयाबीन पीक संरक्षण | Soybean Crop Protection", "https://example.com/video/soybean-protection", "Common pests and diseases of soybean in Maharashtra. Demonstrates integrated pest management practices."),
    ("ठिबक सिंचन कसे करावे | Drip Irrigation Setup", "https://example.com/video/drip-irrigation", "Complete guide to installing drip irrigation system. Explains subsidy available under NDKSP scheme."),
    ("डाळिंब बागेचे व्यवस्थापन | Pomegranate Orchard Management", "https://example.com/video/pomegranate-mgmt", "Annual management calendar for pomegranate. Covers pruning, fertilization, pest control, and harvest."),
    ("कापूस पिकातील गुलाबी बोंडअळी | Pink Bollworm in Cotton", "https://example.com/video/pink-bollworm", "Identification and management of Pink Bollworm in Bt Cotton. Refuge management and IPM strategies."),
    ("MahaDBT पोर्टल अर्ज कसा करावा | How to Apply on MahaDBT", "https://example.com/video/mahadbt-apply", "Step-by-step guide to apply for government schemes through MahaDBT portal."),
]


async def search_documents(query: str, top_k: int = 10) -> str:
    """
    Semantic search for documents. Use this tool to search for relevant documents.

    Args:
        query: The search query in *English* (required)
        top_k: Maximum number of results to return (default: 10)

    Returns:
        search_results: Formatted list of documents
    """
    # Pick random documents (simulating search relevance)
    num_results = min(top_k, random.randint(2, min(6, len(_DOCUMENT_SNIPPETS))))
    selected = random.sample(_DOCUMENT_SNIPPETS, num_results)

    if not selected:
        return f"No results found for `{query}`"

    results = []
    for name, text in selected:
        results.append(f"**{name}**\n```\n{text}\n```")

    return f"> Search Results for `{query}`\n\n" + "\n\n----\n\n".join(results)


async def search_videos(query: str, top_k: int = 3) -> str:
    """
    Semantic search for videos. Use this tool when recommending videos to the farmer.

    Args:
        query: The search query in *English* (required)
        top_k: Maximum number of results to return (default: 3)

    Returns:
        search_results: Formatted list of videos
    """
    num_results = min(top_k, random.randint(1, min(3, len(_VIDEO_SNIPPETS))))
    selected = random.sample(_VIDEO_SNIPPETS, num_results)

    if not selected:
        return f"No videos found for `{query}`"

    results = []
    for name, url, text in selected:
        results.append(f"**[{name}]({url})**\n```\n{text}\n```")

    return f"> Videos for `{query}`\n\n" + "\n\n----\n\n".join(results)
