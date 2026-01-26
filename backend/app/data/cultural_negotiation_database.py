"""
Cultural Negotiation Database for Indian Regions.

This module contains comprehensive cultural negotiation guidance data
for different Indian states and regions, supporting the multilingual
mandi platform's cultural sensitivity requirements.
"""

from typing import Dict, List, Any
from enum import Enum


class IndianRegion(str, Enum):
    """Indian regions for cultural guidance."""
    NORTH = "north"
    SOUTH = "south"
    WEST = "west"
    EAST = "east"
    CENTRAL = "central"
    NORTHEAST = "northeast"


class NegotiationStyle(str, Enum):
    """Regional negotiation styles."""
    RELATIONSHIP_FIRST = "relationship_first"
    DIRECT_BUSINESS = "direct_business"
    HIERARCHICAL = "hierarchical"
    COLLABORATIVE = "collaborative"
    PATIENT_DELIBERATIVE = "patient_deliberative"
    EXPRESSIVE_ANIMATED = "expressive_animated"


class CommunicationStyle(str, Enum):
    """Communication styles by region."""
    HIGH_CONTEXT = "high_context"
    LOW_CONTEXT = "low_context"
    INDIRECT = "indirect"
    DIRECT = "direct"
    FORMAL = "formal"
    INFORMAL = "informal"


# Comprehensive cultural negotiation database
CULTURAL_NEGOTIATION_DATABASE = {
    # North Indian States
    "Punjab": {
        "region": IndianRegion.NORTH,
        "primary_languages": ["pa", "hi", "en"],
        "negotiation_style": NegotiationStyle.RELATIONSHIP_FIRST,
        "communication_style": CommunicationStyle.DIRECT,
        "greeting_customs": {
            "formal": "Sat Sri Akal ji / Namaste ji",
            "business": "Sat Sri Akal, kaise hain aap?",
            "casual": "Sat Sri Akal"
        },
        "relationship_building": {
            "importance": "very_high",
            "approach": "Share tea/lassi, discuss family and farming",
            "time_investment": "30-45 minutes before business",
            "trust_indicators": ["Family connections", "Community reputation", "Agricultural knowledge"]
        },
        "negotiation_approach": {
            "style": "Direct but respectful",
            "pace": "Moderate to fast",
            "decision_making": "Consultative with family/community",
            "bargaining_expected": True,
            "starting_position": "15-20% above/below target"
        },
        "cultural_sensitivities": [
            "Respect for Sikh religious practices",
            "Importance of honor and reputation",
            "Strong agricultural traditions",
            "Value of hard work and prosperity",
            "Community-oriented decision making"
        ],
        "recommended_phrases": {
            "en": "Let's find a fair deal that benefits both our families",
            "hi": "आइए एक उचित सौदा करते हैं जो हमारे दोनों परिवारों के लिए फायदेमंद हो",
            "pa": "ਆਓ ਇੱਕ ਨਿਰਪੱਖ ਸੌਦਾ ਲੱਭੀਏ ਜੋ ਸਾਡੇ ਦੋਵਾਂ ਪਰਿਵਾਰਾਂ ਲਈ ਲਾਭਦਾਇਕ ਹੋਵੇ"
        },
        "taboo_topics": [
            "Political tensions with neighboring states",
            "Religious conflicts",
            "Personal financial struggles",
            "Family disputes"
        ],
        "gift_giving": {
            "appropriate": ["Sweets", "Dry fruits", "Religious items"],
            "avoid": ["Leather products", "Alcohol (unless confirmed acceptable)"],
            "occasions": ["Deal closure", "Festival times", "First meeting"]
        },
        "time_orientation": "flexible",
        "hierarchy_respect": "moderate",
        "bargaining_tactics": [
            "Emphasize mutual benefit",
            "Reference community standards",
            "Use agricultural analogies",
            "Appeal to family welfare"
        ]
    },
    
    "Haryana": {
        "region": IndianRegion.NORTH,
        "primary_languages": ["hi", "en"],
        "negotiation_style": NegotiationStyle.DIRECT_BUSINESS,
        "communication_style": CommunicationStyle.DIRECT,
        "greeting_customs": {
            "formal": "Namaste ji, kaise hain aap?",
            "business": "Namaste, vyavasaya kaisa chal raha hai?",
            "casual": "Namaste"
        },
        "relationship_building": {
            "importance": "high",
            "approach": "Discuss farming, sports (especially wrestling), local issues",
            "time_investment": "20-30 minutes",
            "trust_indicators": ["Agricultural success", "Local connections", "Straightforward dealing"]
        },
        "negotiation_approach": {
            "style": "Straightforward and practical",
            "pace": "Moderate",
            "decision_making": "Quick, often individual",
            "bargaining_expected": True,
            "starting_position": "10-15% above/below target"
        },
        "cultural_sensitivities": [
            "Pride in agricultural achievements",
            "Respect for physical strength and sports",
            "Value of plain speaking",
            "Importance of land ownership",
            "Traditional gender roles in business"
        ],
        "recommended_phrases": {
            "en": "Let's make a straightforward deal that works for both of us",
            "hi": "आइए एक सीधा-सादा सौदा करते हैं जो हम दोनों के लिए काम करे"
        },
        "taboo_topics": [
            "Caste issues",
            "Water disputes",
            "Land acquisition problems",
            "Political corruption"
        ],
        "time_orientation": "punctual",
        "hierarchy_respect": "moderate",
        "bargaining_tactics": [
            "Be direct and honest",
            "Use practical examples",
            "Emphasize value for money",
            "Reference local market rates"
        ]
    },

    # South Indian States
    "Tamil Nadu": {
        "region": IndianRegion.SOUTH,
        "primary_languages": ["ta", "en", "hi"],
        "negotiation_style": NegotiationStyle.PATIENT_DELIBERATIVE,
        "communication_style": CommunicationStyle.FORMAL,
        "greeting_customs": {
            "formal": "Vanakkam sir/madam",
            "business": "Vanakkam, eppadi irukkireenga?",
            "casual": "Vanakkam"
        },
        "relationship_building": {
            "importance": "very_high",
            "approach": "Discuss culture, education, family traditions",
            "time_investment": "45-60 minutes",
            "trust_indicators": ["Educational background", "Cultural knowledge", "Respectful behavior"]
        },
        "negotiation_approach": {
            "style": "Thoughtful and methodical",
            "pace": "Slow and deliberate",
            "decision_making": "Consultative, involves family elders",
            "bargaining_expected": True,
            "starting_position": "20-25% above/below target"
        },
        "cultural_sensitivities": [
            "Deep respect for Tamil language and culture",
            "Importance of education and intellectual discourse",
            "Traditional values and customs",
            "Respect for age and experience",
            "Pride in regional identity"
        ],
        "recommended_phrases": {
            "en": "Let us discuss this matter with proper consideration for all aspects",
            "ta": "எல்லா விஷயங்களையும் சரியாக யோசித்து இந்த விஷயத்தைப் பற்றி பேசுவோம்",
            "hi": "आइए इस मामले पर सभी पहलुओं को ध्यान में रखते हुए चर्चा करते हैं"
        },
        "taboo_topics": [
            "Language politics",
            "North-South cultural differences",
            "Caste-related issues",
            "Political party affiliations"
        ],
        "gift_giving": {
            "appropriate": ["Books", "Traditional items", "Sweets", "Flowers"],
            "avoid": ["Leather products", "Non-vegetarian items (unless confirmed)"],
            "occasions": ["Festival times", "Successful negotiations", "Respect gestures"]
        },
        "time_orientation": "flexible",
        "hierarchy_respect": "high",
        "bargaining_tactics": [
            "Show respect for tradition",
            "Use logical arguments",
            "Reference cultural values",
            "Allow time for consideration"
        ]
    },

    "Karnataka": {
        "region": IndianRegion.SOUTH,
        "primary_languages": ["kn", "en", "hi"],
        "negotiation_style": NegotiationStyle.COLLABORATIVE,
        "communication_style": CommunicationStyle.INDIRECT,
        "greeting_customs": {
            "formal": "Namaskara sir/madam",
            "business": "Namaskara, hegiddira?",
            "casual": "Namaskara"
        },
        "relationship_building": {
            "importance": "high",
            "approach": "Discuss technology, agriculture, local culture",
            "time_investment": "30-40 minutes",
            "trust_indicators": ["Professional competence", "Cultural sensitivity", "Fair dealing"]
        },
        "negotiation_approach": {
            "style": "Balanced and diplomatic",
            "pace": "Moderate",
            "decision_making": "Collaborative with stakeholders",
            "bargaining_expected": True,
            "starting_position": "15-20% above/below target"
        },
        "cultural_sensitivities": [
            "Blend of traditional and modern values",
            "Respect for Kannada language",
            "Importance of technology and innovation",
            "Agricultural heritage",
            "Cosmopolitan outlook in urban areas"
        ],
        "recommended_phrases": {
            "en": "Let's work together to find a solution that benefits everyone",
            "kn": "ಎಲ್ಲರಿಗೂ ಪ್ರಯೋಜನವಾಗುವ ಪರಿಹಾರವನ್ನು ಕಂಡುಕೊಳ್ಳಲು ಒಟ್ಟಾಗಿ ಕೆಲಸ ಮಾಡೋಣ",
            "hi": "आइए मिलकर एक ऐसा समाधान खोजते हैं जो सभी के लिए फायदेमंद हो"
        },
        "taboo_topics": [
            "Inter-state water disputes",
            "Language imposition issues",
            "Regional politics",
            "Caste discrimination"
        ],
        "time_orientation": "punctual",
        "hierarchy_respect": "moderate",
        "bargaining_tactics": [
            "Emphasize win-win outcomes",
            "Use technology analogies",
            "Reference innovation benefits",
            "Show cultural appreciation"
        ]
    },

    # Western Indian States
    "Gujarat": {
        "region": IndianRegion.WEST,
        "primary_languages": ["gu", "hi", "en"],
        "negotiation_style": NegotiationStyle.DIRECT_BUSINESS,
        "communication_style": CommunicationStyle.DIRECT,
        "greeting_customs": {
            "formal": "Namaste sir/ben",
            "business": "Namaste, kem cho?",
            "casual": "Kem cho?"
        },
        "relationship_building": {
            "importance": "high",
            "approach": "Discuss business, family, community service",
            "time_investment": "20-30 minutes",
            "trust_indicators": ["Business acumen", "Community involvement", "Ethical practices"]
        },
        "negotiation_approach": {
            "style": "Business-focused and efficient",
            "pace": "Fast",
            "decision_making": "Quick, often individual or small group",
            "bargaining_expected": True,
            "starting_position": "10-15% above/below target"
        },
        "cultural_sensitivities": [
            "Strong business and entrepreneurial culture",
            "Vegetarian preferences",
            "Importance of community and charity",
            "Respect for Gujarati language",
            "Value of frugality and efficiency"
        ],
        "recommended_phrases": {
            "en": "Let's make a profitable deal that creates value for both parties",
            "gu": "ચાલો એક નફાકારક સોદો કરીએ જે બંને પક્ષો માટે મૂલ્ય બનાવે",
            "hi": "आइए एक लाभदायक सौदा करते हैं जो दोनों पक्षों के लिए मूल्य बनाए"
        },
        "taboo_topics": [
            "Non-vegetarian food",
            "Alcohol consumption",
            "Wasteful spending",
            "Religious conflicts"
        ],
        "gift_giving": {
            "appropriate": ["Sweets", "Business books", "Charitable donations"],
            "avoid": ["Non-vegetarian items", "Leather products", "Alcohol"],
            "occasions": ["Business success", "Festivals", "Community events"]
        },
        "time_orientation": "punctual",
        "hierarchy_respect": "moderate",
        "bargaining_tactics": [
            "Focus on mutual profit",
            "Use business case studies",
            "Emphasize efficiency gains",
            "Reference market opportunities"
        ]
    },

    "Maharashtra": {
        "region": IndianRegion.WEST,
        "primary_languages": ["mr", "hi", "en"],
        "negotiation_style": NegotiationStyle.COLLABORATIVE,
        "communication_style": CommunicationStyle.DIRECT,
        "greeting_customs": {
            "formal": "Namaskar sir/madam",
            "business": "Namaskar, kasa ahaat?",
            "casual": "Namaskar"
        },
        "relationship_building": {
            "importance": "high",
            "approach": "Discuss culture, business, social issues",
            "time_investment": "25-35 minutes",
            "trust_indicators": ["Professional reputation", "Cultural awareness", "Social responsibility"]
        },
        "negotiation_approach": {
            "style": "Professional and systematic",
            "pace": "Moderate to fast",
            "decision_making": "Structured, involves key stakeholders",
            "bargaining_expected": True,
            "starting_position": "12-18% above/below target"
        },
        "cultural_sensitivities": [
            "Pride in Marathi culture and language",
            "Respect for education and arts",
            "Importance of social justice",
            "Business and industrial heritage",
            "Balance of tradition and modernity"
        ],
        "recommended_phrases": {
            "en": "Let's create a partnership that honors our mutual interests",
            "mr": "आपल्या परस्पर हितसंबंधांचा आदर करणारी भागीदारी निर्माण करूया",
            "hi": "आइए एक साझेदारी बनाते हैं जो हमारे पारस्परिक हितों का सम्मान करे"
        },
        "taboo_topics": [
            "Regional political tensions",
            "Language controversies",
            "Caste-based discrimination",
            "Economic inequality"
        ],
        "time_orientation": "punctual",
        "hierarchy_respect": "moderate",
        "bargaining_tactics": [
            "Use structured approach",
            "Reference cultural values",
            "Emphasize long-term benefits",
            "Show social consciousness"
        ]
    },

    # Eastern Indian States
    "West Bengal": {
        "region": IndianRegion.EAST,
        "primary_languages": ["bn", "hi", "en"],
        "negotiation_style": NegotiationStyle.EXPRESSIVE_ANIMATED,
        "communication_style": CommunicationStyle.HIGH_CONTEXT,
        "greeting_customs": {
            "formal": "Namaskar sir/didi",
            "business": "Namaskar, kemon achhen?",
            "casual": "Namaskar"
        },
        "relationship_building": {
            "importance": "very_high",
            "approach": "Discuss literature, culture, politics, food",
            "time_investment": "45-60 minutes",
            "trust_indicators": ["Cultural sophistication", "Intellectual discourse", "Emotional connection"]
        },
        "negotiation_approach": {
            "style": "Emotional and relationship-based",
            "pace": "Slow, with extensive discussion",
            "decision_making": "Consensus-building, involves community",
            "bargaining_expected": True,
            "starting_position": "20-30% above/below target"
        },
        "cultural_sensitivities": [
            "Deep appreciation for arts and literature",
            "Importance of Bengali language and culture",
            "Emotional expressiveness in communication",
            "Respect for intellectual achievements",
            "Strong community bonds"
        ],
        "recommended_phrases": {
            "en": "Let us build a relationship of trust and mutual understanding",
            "bn": "আসুন আমরা বিশ্বাস এবং পারস্পরিক বোঝাপড়ার সম্পর্ক গড়ে তুলি",
            "hi": "आइए विश्वास और पारस्परिक समझ का रिश्ता बनाते हैं"
        },
        "taboo_topics": [
            "Political violence",
            "Economic decline",
            "Migration issues",
            "Religious tensions"
        ],
        "gift_giving": {
            "appropriate": ["Books", "Cultural items", "Sweets", "Flowers"],
            "avoid": ["Expensive items (may cause discomfort)", "Non-vegetarian items (unless confirmed)"],
            "occasions": ["Cultural festivals", "Successful negotiations", "Relationship building"]
        },
        "time_orientation": "very_flexible",
        "hierarchy_respect": "high",
        "bargaining_tactics": [
            "Build emotional connection",
            "Use cultural references",
            "Allow extensive discussion",
            "Appeal to community benefit"
        ]
    },

    # Central Indian States
    "Madhya Pradesh": {
        "region": IndianRegion.CENTRAL,
        "primary_languages": ["hi", "en"],
        "negotiation_style": NegotiationStyle.PATIENT_DELIBERATIVE,
        "communication_style": CommunicationStyle.FORMAL,
        "greeting_customs": {
            "formal": "Namaste ji",
            "business": "Namaste, kaise hain aap?",
            "casual": "Namaste"
        },
        "relationship_building": {
            "importance": "high",
            "approach": "Discuss agriculture, local traditions, family",
            "time_investment": "30-45 minutes",
            "trust_indicators": ["Local connections", "Agricultural knowledge", "Respectful behavior"]
        },
        "negotiation_approach": {
            "style": "Traditional and respectful",
            "pace": "Slow and thoughtful",
            "decision_making": "Consultative with elders",
            "bargaining_expected": True,
            "starting_position": "15-25% above/below target"
        },
        "cultural_sensitivities": [
            "Strong agricultural traditions",
            "Respect for age and experience",
            "Importance of family honor",
            "Traditional values and customs",
            "Community-oriented thinking"
        ],
        "recommended_phrases": {
            "en": "Let us find a solution that respects our traditions and benefits our families",
            "hi": "आइए एक ऐसा समाधान खोजते हैं जो हमारी परंपराओं का सम्मान करे और हमारे परिवारों को लाभ पहुंचाए"
        },
        "taboo_topics": [
            "Caste issues",
            "Land disputes",
            "Political corruption",
            "Religious conflicts"
        ],
        "time_orientation": "flexible",
        "hierarchy_respect": "high",
        "bargaining_tactics": [
            "Show respect for tradition",
            "Use agricultural analogies",
            "Reference family welfare",
            "Allow time for consultation"
        ]
    }
}


# Regional negotiation patterns and preferences
REGIONAL_NEGOTIATION_PATTERNS = {
    IndianRegion.NORTH: {
        "typical_duration": "30-60 minutes",
        "relationship_importance": "high",
        "bargaining_intensity": "moderate_to_high",
        "decision_speed": "moderate",
        "hierarchy_sensitivity": "moderate",
        "common_tactics": ["relationship_building", "community_reference", "honor_appeal"]
    },
    IndianRegion.SOUTH: {
        "typical_duration": "45-90 minutes",
        "relationship_importance": "very_high",
        "bargaining_intensity": "moderate",
        "decision_speed": "slow",
        "hierarchy_sensitivity": "high",
        "common_tactics": ["respect_demonstration", "cultural_reference", "logical_argument"]
    },
    IndianRegion.WEST: {
        "typical_duration": "20-45 minutes",
        "relationship_importance": "moderate_to_high",
        "bargaining_intensity": "high",
        "decision_speed": "fast",
        "hierarchy_sensitivity": "moderate",
        "common_tactics": ["business_focus", "efficiency_emphasis", "profit_sharing"]
    },
    IndianRegion.EAST: {
        "typical_duration": "60-120 minutes",
        "relationship_importance": "very_high",
        "bargaining_intensity": "low_to_moderate",
        "decision_speed": "very_slow",
        "hierarchy_sensitivity": "high",
        "common_tactics": ["emotional_appeal", "cultural_bonding", "consensus_building"]
    },
    IndianRegion.CENTRAL: {
        "typical_duration": "45-75 minutes",
        "relationship_importance": "high",
        "bargaining_intensity": "moderate",
        "decision_speed": "slow",
        "hierarchy_sensitivity": "high",
        "common_tactics": ["tradition_respect", "elder_consultation", "community_benefit"]
    }
}


# Seasonal and festival considerations
SEASONAL_CULTURAL_FACTORS = {
    "harvest_season": {
        "negotiation_mood": "optimistic",
        "price_flexibility": "high",
        "relationship_focus": "celebration_oriented",
        "gift_giving": "appropriate",
        "decision_speed": "faster"
    },
    "festival_season": {
        "negotiation_mood": "generous",
        "price_flexibility": "moderate",
        "relationship_focus": "community_oriented",
        "gift_giving": "expected",
        "decision_speed": "variable"
    },
    "monsoon": {
        "negotiation_mood": "cautious",
        "price_flexibility": "low",
        "relationship_focus": "support_oriented",
        "gift_giving": "thoughtful",
        "decision_speed": "slower"
    },
    "off_season": {
        "negotiation_mood": "practical",
        "price_flexibility": "moderate",
        "relationship_focus": "business_oriented",
        "gift_giving": "minimal",
        "decision_speed": "normal"
    }
}


def get_cultural_data(state: str) -> Dict[str, Any]:
    """Get cultural negotiation data for a specific state."""
    return CULTURAL_NEGOTIATION_DATABASE.get(state, {})


def get_regional_patterns(region: IndianRegion) -> Dict[str, Any]:
    """Get regional negotiation patterns."""
    return REGIONAL_NEGOTIATION_PATTERNS.get(region, {})


def get_seasonal_factors(season: str) -> Dict[str, Any]:
    """Get seasonal cultural factors."""
    return SEASONAL_CULTURAL_FACTORS.get(season, {})


def get_all_supported_states() -> List[str]:
    """Get list of all supported states."""
    return list(CULTURAL_NEGOTIATION_DATABASE.keys())


def get_states_by_region(region: IndianRegion) -> List[str]:
    """Get states belonging to a specific region."""
    return [
        state for state, data in CULTURAL_NEGOTIATION_DATABASE.items()
        if data.get("region") == region
    ]