"""
Cultural Guidance Service for Negotiation Assistant.

This service provides comprehensive cultural guidance for negotiations
between users from different Indian regions, supporting the multilingual
mandi platform's cultural sensitivity requirements.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.models.negotiation import (
    CulturalGuidance, CulturalContext, NegotiationStrategy,
    SeasonalFactor, MarketCondition
)
from app.data.cultural_negotiation_database import (
    CULTURAL_NEGOTIATION_DATABASE,
    REGIONAL_NEGOTIATION_PATTERNS,
    SEASONAL_CULTURAL_FACTORS,
    IndianRegion,
    NegotiationStyle,
    CommunicationStyle,
    get_cultural_data,
    get_regional_patterns,
    get_seasonal_factors,
    get_states_by_region
)
from app.db.mongodb import Collections

logger = logging.getLogger(__name__)


class CulturalGuidanceService:
    """Service for providing cultural negotiation guidance."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.cultural_interactions_collection = db[Collections.CULTURAL_INTERACTIONS]
        self.negotiation_outcomes_collection = db[Collections.NEGOTIATIONS]
    
    async def get_comprehensive_cultural_guidance(
        self,
        buyer_region: str,
        seller_region: str,
        commodity: str = None,
        seasonal_factor: SeasonalFactor = None,
        market_condition: MarketCondition = None,
        negotiation_history: List[Dict] = None
    ) -> CulturalGuidance:
        """
        Get comprehensive cultural guidance for negotiation.
        
        Args:
            buyer_region: Buyer's state/region
            seller_region: Seller's state/region
            commodity: Type of commodity being negotiated
            seasonal_factor: Current seasonal context
            market_condition: Current market conditions
            negotiation_history: Previous negotiation patterns
        
        Returns:
            Comprehensive cultural guidance
        """
        try:
            # Get cultural data for both regions
            buyer_data = get_cultural_data(buyer_region)
            seller_data = get_cultural_data(seller_region)
            
            # Determine cultural context
            cultural_context = self._determine_cultural_context(
                buyer_region, seller_region, buyer_data, seller_data
            )
            
            # Generate region-specific guidance
            guidance_data = await self._generate_regional_guidance(
                buyer_region, seller_region, buyer_data, seller_data
            )
            
            # Add seasonal and market considerations
            seasonal_guidance = self._get_seasonal_guidance(seasonal_factor)
            market_guidance = self._get_market_condition_guidance(market_condition)
            
            # Enhance with historical patterns
            historical_insights = await self._get_historical_insights(
                buyer_region, seller_region, commodity
            )
            
            # Build comprehensive cultural guidance
            cultural_guidance = CulturalGuidance(
                buyer_region=buyer_region,
                seller_region=seller_region,
                cultural_context=cultural_context,
                greeting_style=guidance_data["greeting_style"],
                negotiation_approach=guidance_data["negotiation_approach"],
                cultural_sensitivities=guidance_data["cultural_sensitivities"],
                recommended_phrases=guidance_data["recommended_phrases"],
                taboo_topics=guidance_data["taboo_topics"],
                gift_giving_customs=guidance_data.get("gift_giving_customs"),
                time_orientation=guidance_data["time_orientation"],
                relationship_importance=guidance_data["relationship_importance"]
            )
            
            # Add enhanced attributes
            cultural_guidance.seasonal_considerations = seasonal_guidance
            cultural_guidance.market_considerations = market_guidance
            cultural_guidance.historical_insights = historical_insights
            cultural_guidance.communication_style = guidance_data["communication_style"]
            cultural_guidance.bargaining_tactics = guidance_data["bargaining_tactics"]
            cultural_guidance.hierarchy_sensitivity = guidance_data["hierarchy_sensitivity"]
            cultural_guidance.decision_making_pattern = guidance_data["decision_making_pattern"]
            
            # Log cultural guidance generation
            await self._log_cultural_interaction(
                buyer_region, seller_region, cultural_context, commodity
            )
            
            return cultural_guidance
            
        except Exception as e:
            logger.error(f"Error generating cultural guidance: {e}")
            return self._get_fallback_guidance(buyer_region, seller_region)
    
    async def get_cultural_sensitivity_indicators(
        self,
        buyer_region: str,
        seller_region: str,
        negotiation_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Get cultural sensitivity indicators for the negotiation.
        
        Returns:
            Dictionary with sensitivity indicators and recommendations
        """
        try:
            buyer_data = get_cultural_data(buyer_region)
            seller_data = get_cultural_data(seller_region)
            
            # Calculate cultural distance
            cultural_distance = self._calculate_cultural_distance(buyer_data, seller_data)
            
            # Identify potential friction points
            friction_points = self._identify_friction_points(buyer_data, seller_data)
            
            # Generate sensitivity recommendations
            sensitivity_recommendations = self._generate_sensitivity_recommendations(
                buyer_data, seller_data, friction_points
            )
            
            # Calculate success probability based on cultural factors
            cultural_success_probability = self._calculate_cultural_success_probability(
                buyer_data, seller_data, cultural_distance
            )
            
            return {
                "cultural_distance": cultural_distance,
                "compatibility_score": 1.0 - cultural_distance,
                "friction_points": friction_points,
                "sensitivity_level": self._get_sensitivity_level(cultural_distance),
                "recommendations": sensitivity_recommendations,
                "success_probability": cultural_success_probability,
                "adaptation_strategies": self._get_adaptation_strategies(
                    buyer_data, seller_data
                ),
                "communication_preferences": {
                    "buyer": self._get_communication_preferences(buyer_data),
                    "seller": self._get_communication_preferences(seller_data)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting cultural sensitivity indicators: {e}")
            return {
                "cultural_distance": 0.5,
                "compatibility_score": 0.5,
                "sensitivity_level": "moderate",
                "recommendations": ["Be respectful and patient"],
                "success_probability": 0.7
            }
    
    async def get_region_specific_tips(
        self,
        target_region: str,
        user_role: str,  # "buyer" or "seller"
        commodity: str = None
    ) -> Dict[str, Any]:
        """
        Get region-specific negotiation tips.
        
        Args:
            target_region: The region to get tips for
            user_role: Whether user is buyer or seller
            commodity: Type of commodity (optional)
        
        Returns:
            Region-specific tips and strategies
        """
        try:
            region_data = get_cultural_data(target_region)
            if not region_data:
                return self._get_generic_tips(user_role)
            
            # Get role-specific tips
            role_tips = self._get_role_specific_tips(region_data, user_role)
            
            # Get commodity-specific considerations
            commodity_tips = self._get_commodity_specific_tips(
                region_data, commodity
            ) if commodity else []
            
            # Get timing and approach recommendations
            timing_recommendations = self._get_timing_recommendations(region_data)
            
            # Get language and communication tips
            communication_tips = self._get_communication_tips(region_data)
            
            return {
                "region": target_region,
                "role_specific_tips": role_tips,
                "commodity_considerations": commodity_tips,
                "timing_recommendations": timing_recommendations,
                "communication_tips": communication_tips,
                "do_and_donts": {
                    "do": self._get_dos(region_data, user_role),
                    "dont": self._get_donts(region_data, user_role)
                },
                "success_factors": self._get_success_factors(region_data),
                "common_mistakes": self._get_common_mistakes(region_data, user_role)
            }
            
        except Exception as e:
            logger.error(f"Error getting region-specific tips: {e}")
            return self._get_generic_tips(user_role)
    
    async def analyze_cultural_compatibility(
        self,
        buyer_region: str,
        seller_region: str
    ) -> Dict[str, Any]:
        """
        Analyze cultural compatibility between buyer and seller regions.
        
        Returns:
            Detailed compatibility analysis
        """
        try:
            buyer_data = get_cultural_data(buyer_region)
            seller_data = get_cultural_data(seller_region)
            
            # Analyze different compatibility dimensions
            compatibility_analysis = {
                "overall_compatibility": self._calculate_overall_compatibility(
                    buyer_data, seller_data
                ),
                "communication_compatibility": self._analyze_communication_compatibility(
                    buyer_data, seller_data
                ),
                "negotiation_style_compatibility": self._analyze_negotiation_compatibility(
                    buyer_data, seller_data
                ),
                "time_orientation_compatibility": self._analyze_time_compatibility(
                    buyer_data, seller_data
                ),
                "relationship_importance_compatibility": self._analyze_relationship_compatibility(
                    buyer_data, seller_data
                ),
                "hierarchy_compatibility": self._analyze_hierarchy_compatibility(
                    buyer_data, seller_data
                ),
                "potential_challenges": self._identify_potential_challenges(
                    buyer_data, seller_data
                ),
                "bridging_strategies": self._get_bridging_strategies(
                    buyer_data, seller_data
                ),
                "success_predictors": self._get_success_predictors(
                    buyer_data, seller_data
                )
            }
            
            return compatibility_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing cultural compatibility: {e}")
            return {
                "overall_compatibility": 0.7,
                "potential_challenges": ["Communication differences"],
                "bridging_strategies": ["Be patient and respectful"]
            }
    
    # Helper methods
    
    def _determine_cultural_context(
        self,
        buyer_region: str,
        seller_region: str,
        buyer_data: Dict,
        seller_data: Dict
    ) -> CulturalContext:
        """Determine the cultural context for the negotiation."""
        if not buyer_data or not seller_data:
            return CulturalContext.MODERN
        
        buyer_region_type = buyer_data.get("region")
        seller_region_type = seller_data.get("region")
        
        # Same region
        if buyer_region == seller_region:
            return CulturalContext.TRADITIONAL
        
        # Same regional group
        if buyer_region_type == seller_region_type:
            if buyer_region_type == IndianRegion.NORTH:
                return CulturalContext.NORTH_INDIAN
            elif buyer_region_type == IndianRegion.SOUTH:
                return CulturalContext.SOUTH_INDIAN
            elif buyer_region_type == IndianRegion.WEST:
                return CulturalContext.WESTERN_INDIAN
            elif buyer_region_type == IndianRegion.EAST:
                return CulturalContext.EASTERN_INDIAN
            else:
                return CulturalContext.CENTRAL_INDIAN
        
        # Different regions - determine if urban/rural or traditional/modern
        buyer_style = buyer_data.get("negotiation_style")
        seller_style = seller_data.get("negotiation_style")
        
        if (buyer_style == NegotiationStyle.DIRECT_BUSINESS and 
            seller_style == NegotiationStyle.DIRECT_BUSINESS):
            return CulturalContext.MODERN
        elif (buyer_style in [NegotiationStyle.RELATIONSHIP_FIRST, NegotiationStyle.PATIENT_DELIBERATIVE] or
              seller_style in [NegotiationStyle.RELATIONSHIP_FIRST, NegotiationStyle.PATIENT_DELIBERATIVE]):
            return CulturalContext.TRADITIONAL
        else:
            return CulturalContext.MODERN
    
    async def _generate_regional_guidance(
        self,
        buyer_region: str,
        seller_region: str,
        buyer_data: Dict,
        seller_data: Dict
    ) -> Dict[str, Any]:
        """Generate comprehensive regional guidance."""
        if not buyer_data or not seller_data:
            return self._get_default_guidance_data()
        
        # Merge and adapt guidance from both regions
        guidance = {
            "greeting_style": self._merge_greeting_styles(buyer_data, seller_data),
            "negotiation_approach": self._merge_negotiation_approaches(buyer_data, seller_data),
            "cultural_sensitivities": self._merge_cultural_sensitivities(buyer_data, seller_data),
            "recommended_phrases": self._merge_recommended_phrases(buyer_data, seller_data),
            "taboo_topics": self._merge_taboo_topics(buyer_data, seller_data),
            "time_orientation": self._determine_time_orientation(buyer_data, seller_data),
            "relationship_importance": self._determine_relationship_importance(buyer_data, seller_data),
            "communication_style": self._determine_communication_style(buyer_data, seller_data),
            "bargaining_tactics": self._merge_bargaining_tactics(buyer_data, seller_data),
            "hierarchy_sensitivity": self._determine_hierarchy_sensitivity(buyer_data, seller_data),
            "decision_making_pattern": self._determine_decision_making_pattern(buyer_data, seller_data)
        }
        
        # Add gift giving customs if applicable
        gift_customs = self._merge_gift_giving_customs(buyer_data, seller_data)
        if gift_customs:
            guidance["gift_giving_customs"] = gift_customs
        
        return guidance
    
    def _get_seasonal_guidance(self, seasonal_factor: SeasonalFactor) -> Dict[str, Any]:
        """Get seasonal considerations for cultural guidance."""
        if not seasonal_factor:
            return {}
        
        seasonal_data = get_seasonal_factors(seasonal_factor.value)
        return {
            "mood_context": seasonal_data.get("negotiation_mood", "neutral"),
            "flexibility_level": seasonal_data.get("price_flexibility", "moderate"),
            "relationship_focus": seasonal_data.get("relationship_focus", "balanced"),
            "gift_appropriateness": seasonal_data.get("gift_giving", "optional"),
            "decision_pace": seasonal_data.get("decision_speed", "normal"),
            "cultural_activities": self._get_seasonal_activities(seasonal_factor),
            "conversation_topics": self._get_seasonal_topics(seasonal_factor)
        }
    
    def _get_market_condition_guidance(self, market_condition: MarketCondition) -> Dict[str, Any]:
        """Get market condition considerations for cultural guidance."""
        if not market_condition:
            return {}
        
        market_guidance = {
            MarketCondition.HIGH_DEMAND: {
                "negotiation_tone": "confident_but_respectful",
                "relationship_emphasis": "moderate",
                "patience_level": "low_to_moderate",
                "cultural_considerations": ["Acknowledge seller's position", "Show appreciation for quality"]
            },
            MarketCondition.LOW_DEMAND: {
                "negotiation_tone": "collaborative",
                "relationship_emphasis": "high",
                "patience_level": "high",
                "cultural_considerations": ["Build long-term relationship", "Show understanding of challenges"]
            },
            MarketCondition.OVERSUPPLY: {
                "negotiation_tone": "respectful_but_firm",
                "relationship_emphasis": "moderate",
                "patience_level": "moderate",
                "cultural_considerations": ["Avoid appearing opportunistic", "Emphasize mutual benefit"]
            },
            MarketCondition.SHORTAGE: {
                "negotiation_tone": "respectful_and_appreciative",
                "relationship_emphasis": "very_high",
                "patience_level": "high",
                "cultural_considerations": ["Show gratitude for availability", "Build strong relationship"]
            },
            MarketCondition.STABLE: {
                "negotiation_tone": "balanced",
                "relationship_emphasis": "moderate",
                "patience_level": "moderate",
                "cultural_considerations": ["Focus on fair dealing", "Maintain professional respect"]
            },
            MarketCondition.VOLATILE: {
                "negotiation_tone": "cautious_and_understanding",
                "relationship_emphasis": "high",
                "patience_level": "high",
                "cultural_considerations": ["Acknowledge uncertainty", "Emphasize partnership"]
            }
        }
        
        return market_guidance.get(market_condition, {})
    
    async def _get_historical_insights(
        self,
        buyer_region: str,
        seller_region: str,
        commodity: str
    ) -> Dict[str, Any]:
        """Get historical insights from previous negotiations."""
        try:
            # Query historical negotiations between these regions
            pipeline = [
                {
                    "$match": {
                        "cultural_guidance.buyer_region": buyer_region,
                        "cultural_guidance.seller_region": seller_region,
                        "status": {"$in": ["accepted", "completed"]}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "total_negotiations": {"$sum": 1},
                        "avg_steps": {"$avg": {"$size": "$steps"}},
                        "success_rate": {"$avg": {"$cond": [{"$eq": ["$status", "accepted"]}, 1, 0]}},
                        "common_strategies": {"$push": "$ai_recommendations.negotiation_strategy"}
                    }
                }
            ]
            
            result = await self.negotiation_outcomes_collection.aggregate(pipeline).to_list(1)
            
            if result:
                data = result[0]
                return {
                    "historical_success_rate": data.get("success_rate", 0.7),
                    "typical_negotiation_length": data.get("avg_steps", 3),
                    "total_interactions": data.get("total_negotiations", 0),
                    "effective_strategies": self._analyze_effective_strategies(
                        data.get("common_strategies", [])
                    ),
                    "regional_patterns": f"Based on {data.get('total_negotiations', 0)} previous negotiations"
                }
            else:
                return {
                    "historical_success_rate": 0.7,
                    "note": "Limited historical data available"
                }
                
        except Exception as e:
            logger.error(f"Error getting historical insights: {e}")
            return {"note": "Historical analysis unavailable"}
    
    async def _log_cultural_interaction(
        self,
        buyer_region: str,
        seller_region: str,
        cultural_context: CulturalContext,
        commodity: str
    ):
        """Log cultural interaction for future analysis."""
        try:
            interaction_log = {
                "buyer_region": buyer_region,
                "seller_region": seller_region,
                "cultural_context": cultural_context.value,
                "commodity": commodity,
                "timestamp": datetime.utcnow(),
                "guidance_requested": True
            }
            
            await self.cultural_interactions_collection.insert_one(interaction_log)
            
        except Exception as e:
            logger.error(f"Error logging cultural interaction: {e}")
    
    def _calculate_cultural_distance(self, buyer_data: Dict, seller_data: Dict) -> float:
        """Calculate cultural distance between two regions."""
        if not buyer_data or not seller_data:
            return 0.5
        
        distance_factors = []
        
        # Compare negotiation styles
        buyer_style = buyer_data.get("negotiation_style")
        seller_style = seller_data.get("negotiation_style")
        if buyer_style and seller_style:
            style_distance = 0.0 if buyer_style == seller_style else 0.3
            distance_factors.append(style_distance)
        
        # Compare communication styles
        buyer_comm = buyer_data.get("communication_style")
        seller_comm = seller_data.get("communication_style")
        if buyer_comm and seller_comm:
            comm_distance = 0.0 if buyer_comm == seller_comm else 0.2
            distance_factors.append(comm_distance)
        
        # Compare time orientations
        buyer_time = buyer_data.get("time_orientation")
        seller_time = seller_data.get("time_orientation")
        if buyer_time and seller_time:
            time_distance = 0.0 if buyer_time == seller_time else 0.1
            distance_factors.append(time_distance)
        
        # Compare hierarchy respect levels
        buyer_hierarchy = buyer_data.get("hierarchy_respect")
        seller_hierarchy = seller_data.get("hierarchy_respect")
        if buyer_hierarchy and seller_hierarchy:
            hierarchy_distance = 0.0 if buyer_hierarchy == seller_hierarchy else 0.15
            distance_factors.append(hierarchy_distance)
        
        # Compare regions
        buyer_region = buyer_data.get("region")
        seller_region = seller_data.get("region")
        if buyer_region and seller_region:
            region_distance = 0.0 if buyer_region == seller_region else 0.25
            distance_factors.append(region_distance)
        
        return sum(distance_factors) / len(distance_factors) if distance_factors else 0.5
    
    def _get_fallback_guidance(self, buyer_region: str, seller_region: str) -> CulturalGuidance:
        """Get fallback cultural guidance when data is unavailable."""
        return CulturalGuidance(
            buyer_region=buyer_region,
            seller_region=seller_region,
            cultural_context=CulturalContext.MODERN,
            greeting_style="Respectful and professional",
            negotiation_approach="Collaborative and fair",
            cultural_sensitivities=["Be respectful", "Show patience", "Listen actively"],
            recommended_phrases={"en": "Let's find a mutually beneficial solution"},
            taboo_topics=["Personal finances", "Family matters", "Political issues"],
            time_orientation="flexible",
            relationship_importance="high"
        )
    
    # Additional helper methods for merging and determining guidance attributes
    
    def _merge_greeting_styles(self, buyer_data: Dict, seller_data: Dict) -> str:
        """Merge greeting styles from both regions."""
        buyer_greeting = buyer_data.get("greeting_customs", {}).get("business", "Namaste")
        seller_greeting = seller_data.get("greeting_customs", {}).get("business", "Namaste")
        
        if buyer_greeting == seller_greeting:
            return f"Use traditional greeting: {buyer_greeting}"
        else:
            return f"Adapt greeting style - Buyer prefers: {buyer_greeting}, Seller prefers: {seller_greeting}"
    
    def _merge_negotiation_approaches(self, buyer_data: Dict, seller_data: Dict) -> str:
        """Merge negotiation approaches from both regions."""
        buyer_approach = buyer_data.get("negotiation_approach", {}).get("style", "collaborative")
        seller_approach = seller_data.get("negotiation_approach", {}).get("style", "collaborative")
        
        if "relationship" in buyer_approach.lower() or "relationship" in seller_approach.lower():
            return "Relationship-focused approach with patience and respect"
        elif "direct" in buyer_approach.lower() and "direct" in seller_approach.lower():
            return "Direct but respectful business approach"
        else:
            return "Balanced approach combining relationship-building with business efficiency"
    
    def _merge_cultural_sensitivities(self, buyer_data: Dict, seller_data: Dict) -> List[str]:
        """Merge cultural sensitivities from both regions."""
        buyer_sensitivities = buyer_data.get("cultural_sensitivities", [])
        seller_sensitivities = seller_data.get("cultural_sensitivities", [])
        
        # Combine and deduplicate
        combined = list(set(buyer_sensitivities + seller_sensitivities))
        
        # Add cross-cultural sensitivities
        combined.extend([
            "Respect regional differences",
            "Show appreciation for local customs",
            "Be patient with communication styles"
        ])
        
        return combined[:10]  # Limit to top 10
    
    def _merge_recommended_phrases(self, buyer_data: Dict, seller_data: Dict) -> Dict[str, str]:
        """Merge recommended phrases from both regions."""
        buyer_phrases = buyer_data.get("recommended_phrases", {})
        seller_phrases = seller_data.get("recommended_phrases", {})
        
        # Combine phrases, preferring seller's language if different
        merged_phrases = buyer_phrases.copy()
        merged_phrases.update(seller_phrases)
        
        # Add universal phrases
        merged_phrases["en"] = "Let's work together to find a solution that benefits both of us"
        merged_phrases["hi"] = "आइए मिलकर एक ऐसा समाधान खोजते हैं जो हम दोनों के लिए फायदेमंद हो"
        
        return merged_phrases
    
    def _merge_taboo_topics(self, buyer_data: Dict, seller_data: Dict) -> List[str]:
        """Merge taboo topics from both regions."""
        buyer_taboos = buyer_data.get("taboo_topics", [])
        seller_taboos = seller_data.get("taboo_topics", [])
        
        # Combine and deduplicate
        combined = list(set(buyer_taboos + seller_taboos))
        
        # Add universal taboos
        combined.extend([
            "Personal financial problems",
            "Family disputes",
            "Religious conflicts",
            "Political controversies"
        ])
        
        return list(set(combined))  # Remove duplicates
    
    def _determine_time_orientation(self, buyer_data: Dict, seller_data: Dict) -> str:
        """Determine appropriate time orientation."""
        buyer_time = buyer_data.get("time_orientation", "flexible")
        seller_time = seller_data.get("time_orientation", "flexible")
        
        if buyer_time == "punctual" and seller_time == "punctual":
            return "punctual"
        elif buyer_time == "flexible" or seller_time == "flexible":
            return "flexible"
        else:
            return "moderately_flexible"
    
    def _determine_relationship_importance(self, buyer_data: Dict, seller_data: Dict) -> str:
        """Determine relationship importance level."""
        buyer_rel = buyer_data.get("relationship_building", {}).get("importance", "moderate")
        seller_rel = seller_data.get("relationship_building", {}).get("importance", "moderate")
        
        importance_levels = {"low": 1, "moderate": 2, "high": 3, "very_high": 4}
        
        buyer_level = importance_levels.get(buyer_rel, 2)
        seller_level = importance_levels.get(seller_rel, 2)
        
        avg_level = (buyer_level + seller_level) / 2
        
        if avg_level >= 3.5:
            return "very_high"
        elif avg_level >= 2.5:
            return "high"
        elif avg_level >= 1.5:
            return "moderate"
        else:
            return "low"
    
    def _get_default_guidance_data(self) -> Dict[str, Any]:
        """Get default guidance data when regional data is unavailable."""
        return {
            "greeting_style": "Respectful and professional",
            "negotiation_approach": "Collaborative and fair",
            "cultural_sensitivities": ["Be respectful", "Show patience"],
            "recommended_phrases": {"en": "Let's find a mutually beneficial solution"},
            "taboo_topics": ["Personal finances", "Family matters"],
            "time_orientation": "flexible",
            "relationship_importance": "high",
            "communication_style": "respectful",
            "bargaining_tactics": ["Be fair", "Show respect"],
            "hierarchy_sensitivity": "moderate",
            "decision_making_pattern": "consultative"
        }
    
    # Additional helper methods for cultural guidance analysis
    
    def _identify_friction_points(self, buyer_data: Dict, seller_data: Dict) -> List[str]:
        """Identify potential friction points between regions."""
        friction_points = []
        
        if not buyer_data or not seller_data:
            return ["Limited cultural data available"]
        
        # Compare negotiation styles
        buyer_style = buyer_data.get("negotiation_style")
        seller_style = seller_data.get("negotiation_style")
        if buyer_style != seller_style:
            friction_points.append(f"Different negotiation styles: {buyer_style} vs {seller_style}")
        
        # Compare time orientations
        buyer_time = buyer_data.get("time_orientation")
        seller_time = seller_data.get("time_orientation")
        if buyer_time != seller_time:
            friction_points.append(f"Different time orientations: {buyer_time} vs {seller_time}")
        
        # Compare hierarchy expectations
        buyer_hierarchy = buyer_data.get("hierarchy_respect")
        seller_hierarchy = seller_data.get("hierarchy_respect")
        if buyer_hierarchy != seller_hierarchy:
            friction_points.append(f"Different hierarchy expectations: {buyer_hierarchy} vs {seller_hierarchy}")
        
        return friction_points if friction_points else ["Minimal cultural differences expected"]
    
    def _generate_sensitivity_recommendations(
        self, 
        buyer_data: Dict, 
        seller_data: Dict, 
        friction_points: List[str]
    ) -> List[str]:
        """Generate sensitivity recommendations based on cultural analysis."""
        recommendations = []
        
        if "negotiation styles" in " ".join(friction_points).lower():
            recommendations.append("Be flexible in negotiation approach and adapt to partner's style")
        
        if "time orientations" in " ".join(friction_points).lower():
            recommendations.append("Discuss and agree on meeting schedules and deadlines early")
        
        if "hierarchy" in " ".join(friction_points).lower():
            recommendations.append("Show appropriate respect for seniority and decision-making processes")
        
        # Add general recommendations
        recommendations.extend([
            "Take time to understand regional customs and preferences",
            "Use respectful language and avoid assumptions",
            "Be patient with different communication styles"
        ])
        
        return recommendations[:5]  # Limit to top 5
    
    def _calculate_cultural_success_probability(
        self, 
        buyer_data: Dict, 
        seller_data: Dict, 
        cultural_distance: float
    ) -> float:
        """Calculate success probability based on cultural factors."""
        base_probability = 0.7
        
        # Adjust based on cultural distance
        if cultural_distance < 0.2:
            base_probability += 0.2
        elif cultural_distance > 0.6:
            base_probability -= 0.2
        
        # Adjust based on relationship importance alignment
        buyer_rel = buyer_data.get("relationship_building", {}).get("importance", "moderate")
        seller_rel = seller_data.get("relationship_building", {}).get("importance", "moderate")
        
        if buyer_rel == seller_rel:
            base_probability += 0.1
        
        return max(0.0, min(1.0, base_probability))
    
    def _get_sensitivity_level(self, cultural_distance: float) -> str:
        """Get sensitivity level based on cultural distance."""
        if cultural_distance < 0.3:
            return "low"
        elif cultural_distance < 0.6:
            return "moderate"
        else:
            return "high"
    
    def _get_adaptation_strategies(self, buyer_data: Dict, seller_data: Dict) -> List[str]:
        """Get adaptation strategies for both parties."""
        strategies = []
        
        if buyer_data and seller_data:
            buyer_style = buyer_data.get("negotiation_style")
            seller_style = seller_data.get("negotiation_style")
            
            if buyer_style == NegotiationStyle.DIRECT_BUSINESS and seller_style == NegotiationStyle.RELATIONSHIP_FIRST:
                strategies.append("Buyer should invest time in relationship building before business discussion")
                strategies.append("Seller should appreciate buyer's efficiency-focused approach")
            elif buyer_style == NegotiationStyle.RELATIONSHIP_FIRST and seller_style == NegotiationStyle.DIRECT_BUSINESS:
                strategies.append("Buyer should be prepared for more direct business discussions")
                strategies.append("Seller should allow some time for relationship building")
        
        strategies.extend([
            "Use common language or translation services",
            "Share cultural context and preferences openly",
            "Find common ground in business objectives"
        ])
        
        return strategies[:5]
    
    def _get_communication_preferences(self, region_data: Dict) -> Dict[str, str]:
        """Get communication preferences for a region."""
        if not region_data:
            return {"style": "respectful", "pace": "moderate"}
        
        return {
            "style": region_data.get("communication_style", "respectful"),
            "pace": region_data.get("negotiation_approach", {}).get("pace", "moderate"),
            "formality": region_data.get("hierarchy_respect", "moderate")
        }
    
    def _get_generic_tips(self, user_role: str) -> Dict[str, Any]:
        """Get generic tips when regional data is unavailable."""
        return {
            "region": "Generic",
            "role_specific_tips": [f"General {user_role} negotiation tips"],
            "communication_tips": ["Be respectful and patient", "Listen actively"],
            "success_factors": ["Build good relationship", "Be fair in pricing", "Show cultural sensitivity"]
        }
    
    def _get_role_specific_tips(self, region_data: Dict, user_role: str) -> List[str]:
        """Get role-specific tips for a region."""
        if not region_data:
            return [f"General {user_role} tips"]
        
        base_tips = []
        
        if user_role == "buyer":
            base_tips.extend([
                f"Respect {region_data.get('greeting_customs', {}).get('business', 'local')} greeting customs",
                "Show appreciation for product quality and seller expertise",
                "Be patient with the local negotiation pace"
            ])
        else:  # seller
            base_tips.extend([
                "Highlight product quality and local sourcing",
                "Be transparent about pricing factors",
                "Show willingness to build long-term relationship"
            ])
        
        # Add region-specific considerations
        if region_data.get("relationship_building", {}).get("importance") == "very_high":
            base_tips.append("Invest significant time in relationship building")
        
        return base_tips
    
    def _get_commodity_specific_tips(self, region_data: Dict, commodity: str) -> List[str]:
        """Get commodity-specific tips."""
        if not commodity:
            return []
        
        tips = []
        
        if "grain" in commodity.lower() or "wheat" in commodity.lower():
            tips.append("Discuss quality grades and moisture content")
            tips.append("Consider seasonal price variations")
        elif "vegetable" in commodity.lower():
            tips.append("Emphasize freshness and quality")
            tips.append("Discuss delivery timing for perishables")
        
        return tips
    
    def _get_timing_recommendations(self, region_data: Dict) -> Dict[str, str]:
        """Get timing recommendations for a region."""
        if not region_data:
            return {"best_time": "morning", "duration": "30-60 minutes"}
        
        return {
            "best_time": "morning or early afternoon",
            "duration": region_data.get("relationship_building", {}).get("time_investment", "30-45 minutes"),
            "flexibility": region_data.get("time_orientation", "flexible")
        }
    
    def _get_communication_tips(self, region_data: Dict) -> List[str]:
        """Get communication tips for a region."""
        if not region_data:
            return ["Be respectful and patient"]
        
        tips = []
        
        comm_style = region_data.get("communication_style")
        if comm_style == CommunicationStyle.HIGH_CONTEXT:
            tips.append("Pay attention to non-verbal cues and implied meanings")
        elif comm_style == CommunicationStyle.DIRECT:
            tips.append("Be clear and straightforward in communication")
        
        if region_data.get("primary_languages"):
            languages = region_data["primary_languages"]
            tips.append(f"Consider using local languages: {', '.join(languages)}")
        
        return tips
    
    def _get_dos(self, region_data: Dict, user_role: str) -> List[str]:
        """Get do's for a region and role."""
        dos = [
            "Show respect for local customs",
            "Be patient and courteous",
            "Listen actively to understand needs"
        ]
        
        if region_data:
            sensitivities = region_data.get("cultural_sensitivities", [])
            if sensitivities:
                dos.append(f"Be mindful of: {sensitivities[0]}")
        
        return dos
    
    def _get_donts(self, region_data: Dict, user_role: str) -> List[str]:
        """Get don'ts for a region and role."""
        donts = [
            "Don't rush the negotiation process",
            "Don't ignore cultural differences",
            "Don't make assumptions about preferences"
        ]
        
        if region_data:
            taboos = region_data.get("taboo_topics", [])
            if taboos:
                donts.append(f"Avoid discussing: {taboos[0]}")
        
        return donts
    
    def _get_success_factors(self, region_data: Dict) -> List[str]:
        """Get success factors for a region."""
        if not region_data:
            return ["Build trust", "Be fair", "Show respect"]
        
        factors = []
        
        if region_data.get("relationship_building", {}).get("importance") == "very_high":
            factors.append("Strong relationship building")
        
        bargaining_tactics = region_data.get("bargaining_tactics", [])
        if bargaining_tactics:
            factors.extend(bargaining_tactics[:2])
        
        factors.extend([
            "Cultural sensitivity",
            "Fair pricing",
            "Reliable communication"
        ])
        
        return factors[:5]
    
    def _get_common_mistakes(self, region_data: Dict, user_role: str) -> List[str]:
        """Get common mistakes for a region and role."""
        mistakes = [
            "Rushing the negotiation process",
            "Ignoring cultural customs",
            "Making price the only focus"
        ]
        
        if region_data:
            if region_data.get("time_orientation") == "flexible":
                mistakes.append("Being too rigid about timing")
            
            if region_data.get("hierarchy_respect") == "high":
                mistakes.append("Not showing proper respect to senior members")
        
        return mistakes
    
    # Analysis methods for compatibility
    
    def _calculate_overall_compatibility(self, buyer_data: Dict, seller_data: Dict) -> float:
        """Calculate overall compatibility score."""
        if not buyer_data or not seller_data:
            return 0.7
        
        compatibility_factors = []
        
        # Negotiation style compatibility
        buyer_style = buyer_data.get("negotiation_style")
        seller_style = seller_data.get("negotiation_style")
        if buyer_style == seller_style:
            compatibility_factors.append(1.0)
        else:
            compatibility_factors.append(0.6)
        
        # Time orientation compatibility
        buyer_time = buyer_data.get("time_orientation")
        seller_time = seller_data.get("time_orientation")
        if buyer_time == seller_time:
            compatibility_factors.append(1.0)
        else:
            compatibility_factors.append(0.7)
        
        # Regional compatibility
        buyer_region = buyer_data.get("region")
        seller_region = seller_data.get("region")
        if buyer_region == seller_region:
            compatibility_factors.append(1.0)
        else:
            compatibility_factors.append(0.5)
        
        return sum(compatibility_factors) / len(compatibility_factors) if compatibility_factors else 0.7
    
    def _analyze_communication_compatibility(self, buyer_data: Dict, seller_data: Dict) -> float:
        """Analyze communication style compatibility."""
        if not buyer_data or not seller_data:
            return 0.7
        
        buyer_comm = buyer_data.get("communication_style")
        seller_comm = seller_data.get("communication_style")
        
        if buyer_comm == seller_comm:
            return 1.0
        elif (buyer_comm == CommunicationStyle.DIRECT and seller_comm == CommunicationStyle.INDIRECT) or \
             (buyer_comm == CommunicationStyle.INDIRECT and seller_comm == CommunicationStyle.DIRECT):
            return 0.5
        else:
            return 0.7
    
    def _analyze_negotiation_compatibility(self, buyer_data: Dict, seller_data: Dict) -> float:
        """Analyze negotiation style compatibility."""
        if not buyer_data or not seller_data:
            return 0.7
        
        buyer_style = buyer_data.get("negotiation_style")
        seller_style = seller_data.get("negotiation_style")
        
        if buyer_style == seller_style:
            return 1.0
        elif (buyer_style == NegotiationStyle.DIRECT_BUSINESS and 
              seller_style == NegotiationStyle.RELATIONSHIP_FIRST):
            return 0.4
        else:
            return 0.6
    
    def _analyze_time_compatibility(self, buyer_data: Dict, seller_data: Dict) -> float:
        """Analyze time orientation compatibility."""
        if not buyer_data or not seller_data:
            return 0.7
        
        buyer_time = buyer_data.get("time_orientation")
        seller_time = seller_data.get("time_orientation")
        
        if buyer_time == seller_time:
            return 1.0
        elif (buyer_time == "punctual" and seller_time == "flexible") or \
             (buyer_time == "flexible" and seller_time == "punctual"):
            return 0.6
        else:
            return 0.8
    
    def _analyze_relationship_compatibility(self, buyer_data: Dict, seller_data: Dict) -> float:
        """Analyze relationship importance compatibility."""
        if not buyer_data or not seller_data:
            return 0.7
        
        buyer_rel = buyer_data.get("relationship_building", {}).get("importance", "moderate")
        seller_rel = seller_data.get("relationship_building", {}).get("importance", "moderate")
        
        importance_levels = {"low": 1, "moderate": 2, "high": 3, "very_high": 4}
        
        buyer_level = importance_levels.get(buyer_rel, 2)
        seller_level = importance_levels.get(seller_rel, 2)
        
        difference = abs(buyer_level - seller_level)
        
        if difference == 0:
            return 1.0
        elif difference == 1:
            return 0.8
        elif difference == 2:
            return 0.6
        else:
            return 0.4
    
    def _analyze_hierarchy_compatibility(self, buyer_data: Dict, seller_data: Dict) -> float:
        """Analyze hierarchy respect compatibility."""
        if not buyer_data or not seller_data:
            return 0.7
        
        buyer_hierarchy = buyer_data.get("hierarchy_respect", "moderate")
        seller_hierarchy = seller_data.get("hierarchy_respect", "moderate")
        
        if buyer_hierarchy == seller_hierarchy:
            return 1.0
        else:
            return 0.6
    
    def _identify_potential_challenges(self, buyer_data: Dict, seller_data: Dict) -> List[str]:
        """Identify potential challenges in the negotiation."""
        challenges = []
        
        if not buyer_data or not seller_data:
            return ["Limited cultural data for analysis"]
        
        # Check for style mismatches
        buyer_style = buyer_data.get("negotiation_style")
        seller_style = seller_data.get("negotiation_style")
        
        if buyer_style == NegotiationStyle.DIRECT_BUSINESS and seller_style == NegotiationStyle.RELATIONSHIP_FIRST:
            challenges.append("Buyer's business focus may conflict with seller's relationship emphasis")
        
        # Check for time orientation differences
        buyer_time = buyer_data.get("time_orientation")
        seller_time = seller_data.get("time_orientation")
        
        if buyer_time == "punctual" and seller_time == "flexible":
            challenges.append("Different expectations about timing and schedules")
        
        # Check for communication style differences
        buyer_comm = buyer_data.get("communication_style")
        seller_comm = seller_data.get("communication_style")
        
        if buyer_comm == CommunicationStyle.DIRECT and seller_comm == CommunicationStyle.INDIRECT:
            challenges.append("Different communication styles may lead to misunderstandings")
        
        return challenges if challenges else ["Minimal challenges expected"]
    
    def _get_bridging_strategies(self, buyer_data: Dict, seller_data: Dict) -> List[str]:
        """Get strategies to bridge cultural differences."""
        strategies = []
        
        if not buyer_data or not seller_data:
            return ["Focus on common business objectives", "Use respectful communication"]
        
        # Address negotiation style differences
        buyer_style = buyer_data.get("negotiation_style")
        seller_style = seller_data.get("negotiation_style")
        
        if buyer_style != seller_style:
            strategies.append("Find middle ground between different negotiation approaches")
        
        # Address communication differences
        buyer_comm = buyer_data.get("communication_style")
        seller_comm = seller_data.get("communication_style")
        
        if buyer_comm != seller_comm:
            strategies.append("Clarify communication preferences and adapt accordingly")
        
        strategies.extend([
            "Establish common ground through shared business goals",
            "Use cultural mediators or translators if needed",
            "Take time to understand each other's perspectives"
        ])
        
        return strategies[:5]
    
    def _get_success_predictors(self, buyer_data: Dict, seller_data: Dict) -> List[str]:
        """Get success predictors for the negotiation."""
        predictors = []
        
        if not buyer_data or not seller_data:
            return ["Mutual respect", "Clear communication", "Fair pricing"]
        
        # Check for positive compatibility factors
        if buyer_data.get("region") == seller_data.get("region"):
            predictors.append("Same regional background facilitates understanding")
        
        if buyer_data.get("negotiation_style") == seller_data.get("negotiation_style"):
            predictors.append("Compatible negotiation styles")
        
        if buyer_data.get("time_orientation") == seller_data.get("time_orientation"):
            predictors.append("Aligned time expectations")
        
        predictors.extend([
            "Mutual business interest",
            "Cultural awareness and sensitivity",
            "Effective communication"
        ])
        
        return predictors[:5]
    
    def _get_seasonal_activities(self, seasonal_factor: SeasonalFactor) -> List[str]:
        """Get seasonal activities relevant to negotiations."""
        activities_map = {
            SeasonalFactor.HARVEST_SEASON: ["Harvest celebrations", "Quality assessments", "Bulk trading"],
            SeasonalFactor.FESTIVAL_SEASON: ["Festival preparations", "Gift exchanges", "Community gatherings"],
            SeasonalFactor.MONSOON: ["Weather discussions", "Transport planning", "Storage considerations"],
            SeasonalFactor.OFF_SEASON: ["Planning activities", "Relationship building", "Market analysis"]
        }
        
        return activities_map.get(seasonal_factor, [])
    
    def _get_seasonal_topics(self, seasonal_factor: SeasonalFactor) -> List[str]:
        """Get seasonal conversation topics."""
        topics_map = {
            SeasonalFactor.HARVEST_SEASON: ["Crop yields", "Quality grades", "Market prices"],
            SeasonalFactor.FESTIVAL_SEASON: ["Festival celebrations", "Family traditions", "Community events"],
            SeasonalFactor.MONSOON: ["Weather conditions", "Transportation", "Storage facilities"],
            SeasonalFactor.OFF_SEASON: ["Future planning", "Market trends", "Business development"]
        }
        
        return topics_map.get(seasonal_factor, [])
    
    def _analyze_effective_strategies(self, strategies: List[str]) -> List[str]:
        """Analyze effective strategies from historical data."""
        if not strategies:
            return ["Collaborative approach", "Fair pricing", "Respectful communication"]
        
        # Count strategy occurrences and return most common
        strategy_counts = {}
        for strategy in strategies:
            if strategy:
                strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
        
        # Sort by frequency and return top strategies
        sorted_strategies = sorted(strategy_counts.items(), key=lambda x: x[1], reverse=True)
        return [strategy for strategy, count in sorted_strategies[:5]]
    def _determine_communication_style(self, buyer_data: Dict, seller_data: Dict) -> str:
        """Determine appropriate communication style."""
        if not buyer_data or not seller_data:
            return "respectful"
        
        buyer_comm = buyer_data.get("communication_style")
        seller_comm = seller_data.get("communication_style")
        
        if buyer_comm == seller_comm:
            return buyer_comm.value if buyer_comm else "respectful"
        elif buyer_comm == CommunicationStyle.DIRECT or seller_comm == CommunicationStyle.DIRECT:
            return "clear_and_respectful"
        else:
            return "adaptive_and_patient"
    
    def _merge_gift_giving_customs(self, buyer_data: Dict, seller_data: Dict) -> Optional[str]:
        """Merge gift giving customs from both regions."""
        if not buyer_data or not seller_data:
            return None
        
        buyer_gifts = buyer_data.get("gift_giving", {})
        seller_gifts = seller_data.get("gift_giving", {})
        
        if not buyer_gifts and not seller_gifts:
            return None
        
        customs = []
        
        # Add appropriate gifts from both regions
        buyer_appropriate = buyer_gifts.get("appropriate", [])
        seller_appropriate = seller_gifts.get("appropriate", [])
        
        if buyer_appropriate or seller_appropriate:
            all_appropriate = list(set(buyer_appropriate + seller_appropriate))
            customs.append(f"Appropriate gifts: {', '.join(all_appropriate[:3])}")
        
        # Add items to avoid
        buyer_avoid = buyer_gifts.get("avoid", [])
        seller_avoid = seller_gifts.get("avoid", [])
        
        if buyer_avoid or seller_avoid:
            all_avoid = list(set(buyer_avoid + seller_avoid))
            customs.append(f"Avoid: {', '.join(all_avoid[:3])}")
        
        return "; ".join(customs) if customs else None
    
    def _merge_bargaining_tactics(self, buyer_data: Dict, seller_data: Dict) -> List[str]:
        """Merge bargaining tactics from both regions."""
        if not buyer_data or not seller_data:
            return ["Be fair", "Show respect", "Build relationship"]
        
        buyer_tactics = buyer_data.get("bargaining_tactics", [])
        seller_tactics = seller_data.get("bargaining_tactics", [])
        
        # Combine tactics from both regions
        combined_tactics = []
        
        # Add buyer's tactics
        if buyer_tactics:
            combined_tactics.extend(buyer_tactics[:2])  # Take top 2
        
        # Add seller's tactics
        if seller_tactics:
            combined_tactics.extend(seller_tactics[:2])  # Take top 2
        
        # Add universal tactics
        universal_tactics = [
            "Show mutual respect",
            "Focus on win-win outcomes",
            "Be patient and understanding",
            "Build trust through transparency"
        ]
        
        combined_tactics.extend(universal_tactics)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_tactics = []
        for tactic in combined_tactics:
            if tactic not in seen:
                seen.add(tactic)
                unique_tactics.append(tactic)
        
        return unique_tactics[:6]  # Return top 6 tactics
    
    def _determine_hierarchy_sensitivity(self, buyer_data: Dict, seller_data: Dict) -> str:
        """Determine hierarchy sensitivity level."""
        if not buyer_data or not seller_data:
            return "moderate"
        
        buyer_hierarchy = buyer_data.get("hierarchy_respect", "moderate")
        seller_hierarchy = seller_data.get("hierarchy_respect", "moderate")
        
        hierarchy_levels = {"low": 1, "moderate": 2, "high": 3}
        
        buyer_level = hierarchy_levels.get(buyer_hierarchy, 2)
        seller_level = hierarchy_levels.get(seller_hierarchy, 2)
        
        avg_level = (buyer_level + seller_level) / 2
        
        if avg_level >= 2.5:
            return "high"
        elif avg_level >= 1.5:
            return "moderate"
        else:
            return "low"
    
    def _determine_decision_making_pattern(self, buyer_data: Dict, seller_data: Dict) -> str:
        """Determine decision making pattern."""
        if not buyer_data or not seller_data:
            return "consultative"
        
        buyer_pattern = buyer_data.get("negotiation_approach", {}).get("decision_making", "consultative")
        seller_pattern = seller_data.get("negotiation_approach", {}).get("decision_making", "consultative")
        
        if "quick" in buyer_pattern or "quick" in seller_pattern:
            return "efficient"
        elif "consultative" in buyer_pattern or "consultative" in seller_pattern:
            return "consultative"
        else:
            return "collaborative"