"""
Mock AI service for chat suggestions, content moderation, and analytics.

This service provides rule-based AI functionality as a fallback for AWS Bedrock/Lex.
"""

import logging
import random
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class AIService:
    """Mock AI service with rule-based responses."""
    
    def __init__(self):
        """Initialize AI service."""
        # Negotiation suggestion templates
        self.negotiation_templates = {
            "counteroffer_high": [
                "The current offer is {current_price}₹. Based on market data, you could counter with {suggested_price}₹.",
                "Market analysis suggests {suggested_price}₹ would be a fair counter-offer to {current_price}₹.",
                "Consider offering {suggested_price}₹, which is closer to the average market price."
            ],
            "counteroffer_low": [
                "The offer of {current_price}₹ is below market value. Counter with {suggested_price}₹.",
                "Market data shows this should be priced around {suggested_price}₹. Counter accordingly.",
                "This seems underpriced. Suggest {suggested_price}₹ based on market trends."
            ],
            "accept": [
                "This is a fair offer at {current_price}₹, close to market average.",
                "The price {current_price}₹ matches current market rates. Consider accepting.",
                "Good deal! {current_price}₹ is competitive for this product."
            ],
            "reject": [
                "This offer of {current_price}₹ is significantly below market value.",
                "Consider rejecting {current_price}₹ and looking for better offers.",
                "This price is not competitive. Market rates are higher."
            ]
        }
        
        # Content moderation keywords
        self.inappropriate_keywords = [
            "spam", "scam", "fraud", "fake", "cheat",
            "violence", "hate", "abuse", "offensive"
        ]
        
        # Community guidelines
        self.community_rules = {
            "profanity": ["bad", "inappropriate language detected"],
            "personal_info": ["email", "phone", "contact info shared publicly"],
            "spam": ["repeated messages", "promotional content"],
            "harassment": ["threatening", "bullying", "harassment"]
        }
    
    async def generate_negotiation_suggestion(
        self,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate negotiation suggestion based on context.
        
        Args:
            context: Dict containing:
                - current_price: float
                - market_average: float
                - buyer_budget: Optional[float]
                - seller_minimum: Optional[float]
                - commodity: str
                
        Returns:
            Negotiation suggestion with reasoning
        """
        try:
            current_price = context.get("current_price", 0)
            market_avg = context.get("market_average", current_price)
            commodity = context.get("commodity", "product")
            
            # Determine suggestion type
            price_diff = (current_price - market_avg) / market_avg if market_avg > 0 else 0
            
            if abs(price_diff) < 0.05:  # Within 5% of market average
                suggestion_type = "accept"
                suggested_price = current_price
                confidence = 0.9
            elif price_diff > 0.15:  # More than 15% above market
                suggestion_type = "reject"
                suggested_price = market_avg * 1.05
                confidence = 0.8
            elif price_diff < -0.15:  # More than 15% below market
                suggestion_type = "counteroffer_low"
                suggested_price = market_avg * 0.95
                confidence = 0.85
            else:
                suggestion_type = "counteroffer_high"
                suggested_price = market_avg
                confidence = 0.75
            
            # Generate message
            template = random.choice(self.negotiation_templates[suggestion_type])
            message = template.format(
                current_price=f"{current_price:.2f}",
                suggested_price=f"{suggested_price:.2f}"
            )
            
            return {
                "suggestion_type": suggestion_type,
                "suggested_action": suggestion_type.replace("_", " ").title(),
                "suggested_price": round(suggested_price, 2),
                "current_price": current_price,
                "market_average": market_avg,
                "confidence": confidence,
                "message": message,
                "reasoning": self._generate_negotiation_reasoning(
                    current_price, market_avg, suggested_price, suggestion_type
                ),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating negotiation suggestion: {e}")
            return {
                "suggestion_type": "error",
                "message": "Unable to generate suggestion at this time",
                "confidence": 0.0
            }
    
    def _generate_negotiation_reasoning(
        self,
        current_price: float,
        market_avg: float,
        suggested_price: float,
        suggestion_type: str
    ) -> List[str]:
        """Generate reasoning for negotiation suggestion."""
        reasoning = []
        
        price_diff_pct = ((current_price - market_avg) / market_avg * 100) if market_avg > 0 else 0
        
        reasoning.append(
            f"Current offer: ₹{current_price:.2f}, Market average: ₹{market_avg:.2f}"
        )
        
        if price_diff_pct > 5:
            reasoning.append(
                f"The offer is {price_diff_pct:.1f}% above market average."
            )
        elif price_diff_pct < -5:
            reasoning.append(
                f"The offer is {abs(price_diff_pct):.1f}% below market average."
            )
        else:
            reasoning.append("The offer is close to market average.")
        
        if suggestion_type == "accept":
            reasoning.append("This is a fair deal for both parties.")
        elif "counteroffer" in suggestion_type:
            reasoning.append(
                f"A counter-offer of ₹{suggested_price:.2f} would be more aligned with market rates."
            )
        else:
            reasoning.append("Consider waiting for a better offer.")
        
        return reasoning
    
    async def moderate_content(
        self,
        content: str,
        content_type: str = "message"
    ) -> Dict[str, Any]:
        """
        Moderate content for inappropriate material.
        
        Args:
            content: Text content to moderate
            content_type: Type of content (message, review, listing)
            
        Returns:
            Moderation result
        """
        try:
            content_lower = content.lower()
            
            # Check for inappropriate keywords
            issues_found = []
            confidence_scores = []
            
            for keyword in self.inappropriate_keywords:
                if keyword in content_lower:
                    issues_found.append({
                        "type": "inappropriate_content",
                        "keyword": keyword,
                        "severity": "high"
                    })
                    confidence_scores.append(0.8)
            
            # Check for community rule violations
            for rule_type, indicators in self.community_rules.items():
                for indicator in indicators:
                    if indicator in content_lower:
                        issues_found.append({
                            "type": rule_type,
                            "indicator": indicator,
                            "severity": "medium"
                        })
                        confidence_scores.append(0.6)
            
            # Check for excessive caps (shouting)
            caps_ratio = sum(1 for c in content if c.isupper()) / len(content) if content else 0
            if caps_ratio > 0.5 and len(content) > 10:
                issues_found.append({
                    "type": "excessive_caps",
                    "indicator": "shouting",
                    "severity": "low"
                })
                confidence_scores.append(0.5)
            
            # Determine overall status
            if issues_found:
                high_severity = any(issue["severity"] == "high" for issue in issues_found)
                status = "rejected" if high_severity else "flagged"
                avg_confidence = sum(confidence_scores) / len(confidence_scores)
            else:
                status = "approved"
                avg_confidence = 0.9
            
            return {
                "status": status,
                "content_type": content_type,
                "issues_found": issues_found,
                "confidence": round(avg_confidence, 2),
                "recommendations": self._generate_moderation_recommendations(issues_found),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error moderating content: {e}")
            return {
                "status": "error",
                "message": "Unable to moderate content at this time",
                "confidence": 0.0
            }
    
    def _generate_moderation_recommendations(self, issues: List[Dict]) -> List[str]:
        """Generate recommendations based on moderation issues."""
        if not issues:
            return ["Content approved - no issues found"]
        
        recommendations = []
        
        severity_counts = {"high": 0, "medium": 0, "low": 0}
        for issue in issues:
            severity_counts[issue["severity"]] += 1
        
        if severity_counts["high"] > 0:
            recommendations.append("Content contains inappropriate material and should be rejected")
        
        if severity_counts["medium"] > 0:
            recommendations.append("Content may violate community guidelines - manual review recommended")
        
        if severity_counts["low"] > 0:
            recommendations.append("Minor issues detected - consider notifying user")
        
        return recommendations
    
    async def generate_product_insights(
        self,
        product_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate AI-powered insights for a product.
        
        Args:
            product_data: Product information
            
        Returns:
            Product insights and recommendations
        """
        try:
            commodity = product_data.get("commodity", "product")
            price = product_data.get("price", 0)
            quality = product_data.get("quality", "medium")
            description = product_data.get("description", "")
            
            insights = []
            recommendations = []
            
            # Price insights
            if price > 0:
                insights.append(f"Price analysis: ₹{price:.2f} per unit")
                
                # Simple price benchmarking
                if price < 50:
                    recommendations.append("Consider competitive pricing for better visibility")
                elif price > 5000:
                    recommendations.append("High-value product - ensure detailed description")
            
            # Quality insights
            if quality.lower() == "high":
                insights.append("Premium quality product")
                recommendations.append("Highlight quality certifications if available")
            elif quality.lower() == "low":
                insights.append("Economy tier product")
                recommendations.append("Focus on value proposition")
            
            # Description insights
            if len(description) < 50:
                recommendations.append("Add more details to product description")
            elif len(description) > 500:
                insights.append("Comprehensive product description provided")
            
            # Seasonal insights
            month = datetime.now().month
            if month in [3, 4, 5]:  # Spring
                insights.append("Spring season - good time for fresh produce")
            elif month in [6, 7, 8, 9]:  # Monsoon
                insights.append("Monsoon season - adjust pricing for seasonal variations")
            elif month in [10, 11]:  # Autumn
                insights.append("Harvest season - expect increased supply")
            else:  # Winter
                insights.append("Winter season - peak demand for certain commodities")
            
            return {
                "commodity": commodity,
                "insights": insights,
                "recommendations": recommendations,
                "sustainability_score": self._calculate_sustainability_score(product_data),
                "market_competitiveness": random.choice(["high", "medium", "low"]),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating product insights: {e}")
            return {
                "insights": [],
                "recommendations": ["Unable to generate insights at this time"],
                "error": str(e)
            }
    
    def _calculate_sustainability_score(self, product_data: Dict[str, Any]) -> float:
        """Calculate a simple sustainability score."""
        score = 0.5  # Base score
        
        # Check for sustainability keywords
        description = product_data.get("description", "").lower()
        sustainability_keywords = [
            "organic", "eco-friendly", "sustainable", "natural",
            "pesticide-free", "chemical-free", "traditional"
        ]
        
        keyword_matches = sum(1 for kw in sustainability_keywords if kw in description)
        score += min(keyword_matches * 0.1, 0.4)
        
        # Local sourcing bonus
        if "local" in description or "nearby" in description:
            score += 0.1
        
        return min(score, 1.0)
    
    async def generate_chat_response(
        self,
        user_message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate AI chatbot response (simple rule-based).
        
        Args:
            user_message: User's message
            context: Optional conversation context
            
        Returns:
            AI response
        """
        message_lower = user_message.lower()
        
        # Greeting responses
        if any(word in message_lower for word in ["hello", "hi", "hey", "namaste"]):
            responses = [
                "Hello! How can I help you today?",
                "Hi there! Looking for fresh produce?",
                "Namaste! Welcome to Mandi Marketplace!"
            ]
            return {
                "response": random.choice(responses),
                "intent": "greeting",
                "confidence": 0.9
            }
        
        # Help responses
        if any(word in message_lower for word in ["help", "assist", "support"]):
            return {
                "response": "I can help you with product listings, price inquiries, and negotiations. What do you need?",
                "intent": "help_request",
                "confidence": 0.85
            }
        
        # Price inquiries
        if any(word in message_lower for word in ["price", "cost", "rate", "kya hai"]):
            return {
                "response": "I can help you find current market prices. Which commodity are you interested in?",
                "intent": "price_inquiry",
                "confidence": 0.8
            }
        
        # Default response
        return {
            "response": "I understand you want to know more. Could you please provide more details?",
            "intent": "unknown",
            "confidence": 0.5
        }


# Global AI service instance
ai_service = AIService()
