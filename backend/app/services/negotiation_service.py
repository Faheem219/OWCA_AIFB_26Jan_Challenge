"""
Negotiation Assistant Service with AI guidance.
"""
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.models.negotiation import (
    NegotiationSession, NegotiationCreate, NegotiationUpdate,
    Offer, NegotiationStep, MarketContext, CulturalGuidance,
    PriceRecommendation, CounterOfferSuggestion, NegotiationAnalytics,
    NegotiationInsights, NegotiationStatus, OfferType, NegotiationStrategy,
    CulturalContext, SeasonalFactor, MarketCondition
)
from app.models.product import Product
from app.models.user import User
from app.db.mongodb import Collections
from app.services.price_discovery_service import PriceDiscoveryService
from app.services.cultural_guidance_service import CulturalGuidanceService

logger = logging.getLogger(__name__)


class NegotiationAssistantService:
    """AI-powered negotiation assistant service."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.negotiations_collection = db[Collections.NEGOTIATIONS]
        self.products_collection = db[Collections.PRODUCTS]
        self.users_collection = db[Collections.USERS]
        self.price_service = PriceDiscoveryService(db)
        self.cultural_service = CulturalGuidanceService(db)
    
    async def initiate_negotiation(
        self, 
        buyer_id: str, 
        negotiation_data: NegotiationCreate
    ) -> NegotiationSession:
        """Initiate a new negotiation session."""
        try:
            # Verify product exists
            product = await self.products_collection.find_one(
                {"_id": ObjectId(negotiation_data.product_id)}
            )
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product not found"
                )
            
            # Verify seller exists
            seller = await self.users_collection.find_one(
                {"_id": ObjectId(negotiation_data.seller_id)}
            )
            if not seller:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Seller not found"
                )
            
            # Get market context
            market_context = await self._get_market_context(
                product["category"], 
                product.get("location", {})
            )
            
            # Get cultural guidance
            buyer = await self.users_collection.find_one({"_id": ObjectId(buyer_id)})
            cultural_guidance = await self._get_cultural_guidance(buyer, seller)
            
            # Create initial negotiation step
            initial_step = NegotiationStep(
                step_number=1,
                participant_id=buyer_id,
                participant_role="buyer",
                action="offer",
                offer=negotiation_data.initial_offer,
                message=negotiation_data.message
            )
            
            # Create negotiation session
            negotiation = NegotiationSession(
                product_id=negotiation_data.product_id,
                buyer_id=buyer_id,
                seller_id=negotiation_data.seller_id,
                initial_offer=negotiation_data.initial_offer,
                current_offer=negotiation_data.initial_offer,
                steps=[initial_step],
                market_context=market_context,
                cultural_guidance=cultural_guidance,
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            
            # Save to database
            result = await self.negotiations_collection.insert_one(
                negotiation.dict(by_alias=True)
            )
            negotiation.id = result.inserted_id
            
            logger.info(f"Initiated negotiation {negotiation.id} for product {negotiation_data.product_id}")
            return negotiation
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error initiating negotiation: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to initiate negotiation"
            )
    
    async def get_price_recommendation(
        self, 
        commodity: str, 
        quantity: float, 
        quality_grade: str,
        market_context: MarketContext,
        user_role: str = "buyer"
    ) -> PriceRecommendation:
        """Get AI-powered price recommendation."""
        try:
            # Get current market prices
            current_prices = await self.price_service.get_current_prices(
                commodity, 
                market_context.location
            )
            
            # Calculate base recommendation
            if current_prices:
                market_price = sum(p.price_modal for p in current_prices) / len(current_prices)
            else:
                market_price = market_context.current_market_price
            
            # Apply quality adjustment
            quality_multiplier = self._get_quality_multiplier(quality_grade)
            base_price = market_price * quality_multiplier
            
            # Apply quantity discount
            quantity_discount = self._calculate_quantity_discount(quantity, commodity)
            
            # Apply seasonal factors
            seasonal_adjustment = self._get_seasonal_adjustment(
                market_context.seasonal_factor, 
                commodity
            )
            
            # Apply market condition adjustment
            market_adjustment = self._get_market_condition_adjustment(
                market_context.market_condition
            )
            
            # Calculate final recommendation
            if user_role == "buyer":
                # Buyer wants lower price
                recommended_price = base_price * (1 - quantity_discount) * seasonal_adjustment * market_adjustment * 0.95
                price_range_min = recommended_price * 0.9
                price_range_max = recommended_price * 1.05
            else:
                # Seller wants higher price
                recommended_price = base_price * (1 - quantity_discount) * seasonal_adjustment * market_adjustment * 1.05
                price_range_min = recommended_price * 0.95
                price_range_max = recommended_price * 1.1
            
            # Build factors considered
            factors_considered = [
                f"Current market price: ₹{market_price:.2f}",
                f"Quality grade: {quality_grade}",
                f"Quantity discount: {quantity_discount*100:.1f}%",
                f"Seasonal factor: {market_context.seasonal_factor}",
                f"Market condition: {market_context.market_condition}"
            ]
            
            # Build reasoning
            reasoning = self._build_price_reasoning(
                market_context, quality_grade, quantity, user_role
            )
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(
                market_context, len(current_prices)
            )
            
            return PriceRecommendation(
                recommended_price=recommended_price,
                price_range_min=price_range_min,
                price_range_max=price_range_max,
                confidence_score=confidence_score,
                reasoning=reasoning,
                factors_considered=factors_considered,
                market_comparison={
                    "current_market": market_price,
                    "recommended": recommended_price,
                    "msp": market_context.msp_price or 0.0
                },
                risk_assessment="medium",
                success_probability=0.75
            )
            
        except Exception as e:
            logger.error(f"Error getting price recommendation: {e}")
            # Return fallback recommendation
            return PriceRecommendation(
                recommended_price=market_context.current_market_price,
                price_range_min=market_context.current_market_price * 0.9,
                price_range_max=market_context.current_market_price * 1.1,
                confidence_score=0.5,
                reasoning="Fallback recommendation based on provided market price",
                factors_considered=["Market context price"],
                market_comparison={"current_market": market_context.current_market_price},
                risk_assessment="medium",
                success_probability=0.6
            )
    
    async def generate_counter_offer(
        self, 
        current_offer: Offer, 
        market_data: MarketContext,
        negotiation_history: List[NegotiationStep],
        user_role: str = "seller"
    ) -> CounterOfferSuggestion:
        """Generate AI-powered counter-offer suggestion."""
        try:
            # Analyze negotiation history
            negotiation_pattern = self._analyze_negotiation_pattern(negotiation_history)
            
            # Get price recommendation
            price_rec = await self.get_price_recommendation(
                market_data.commodity,
                current_offer.quantity,
                "standard",  # Default quality
                market_data,
                user_role
            )
            
            # Determine negotiation strategy
            strategy = self._determine_negotiation_strategy(
                current_offer, price_rec, negotiation_pattern, user_role
            )
            
            # Calculate suggested price
            if user_role == "seller":
                # Seller counter-offers higher
                if current_offer.unit_price < price_rec.recommended_price:
                    suggested_price = min(
                        price_rec.recommended_price,
                        current_offer.unit_price * 1.15  # Max 15% increase
                    )
                else:
                    suggested_price = current_offer.unit_price * 1.05  # Small increase
            else:
                # Buyer counter-offers lower
                if current_offer.unit_price > price_rec.recommended_price:
                    suggested_price = max(
                        price_rec.recommended_price,
                        current_offer.unit_price * 0.85  # Max 15% decrease
                    )
                else:
                    suggested_price = current_offer.unit_price * 0.95  # Small decrease
            
            # Build justification
            justification = self._build_counter_offer_justification(
                current_offer, suggested_price, market_data, strategy
            )
            
            # Check for bulk discount applicability
            bulk_discount_applicable = current_offer.quantity >= 100  # Example threshold
            bulk_discount_percentage = 0.05 if bulk_discount_applicable else None
            
            # Get seasonal and market factors
            seasonal_factors = self._get_seasonal_factors(market_data.seasonal_factor)
            market_factors = self._get_market_factors(market_data.market_condition)
            
            # Calculate success probability
            success_probability = self._calculate_counter_offer_success_probability(
                current_offer, suggested_price, price_rec, negotiation_pattern
            )
            
            return CounterOfferSuggestion(
                suggested_price=suggested_price,
                negotiation_strategy=strategy,
                justification=justification,
                bulk_discount_applicable=bulk_discount_applicable,
                bulk_discount_percentage=bulk_discount_percentage,
                seasonal_factors=seasonal_factors,
                market_factors=market_factors,
                psychological_factors=["anchoring", "reciprocity"],
                success_probability=success_probability,
                alternative_offers=[
                    {
                        "price": suggested_price * 0.98,
                        "terms": "Quick payment discount"
                    },
                    {
                        "price": suggested_price * 1.02,
                        "terms": "Extended payment terms"
                    }
                ]
            )
            
        except Exception as e:
            logger.error(f"Error generating counter offer: {e}")
            # Return fallback suggestion
            fallback_price = current_offer.unit_price * (1.05 if user_role == "seller" else 0.95)
            return CounterOfferSuggestion(
                suggested_price=fallback_price,
                negotiation_strategy=NegotiationStrategy.COMPROMISING,
                justification="Fallback counter-offer based on current market conditions",
                success_probability=0.6
            )
    
    async def get_cultural_guidance(
        self, 
        buyer_region: str, 
        seller_region: str,
        commodity: str = None,
        seasonal_factor: SeasonalFactor = None,
        market_condition: MarketCondition = None
    ) -> CulturalGuidance:
        """Get comprehensive cultural negotiation guidance."""
        try:
            return await self.cultural_service.get_comprehensive_cultural_guidance(
                buyer_region=buyer_region,
                seller_region=seller_region,
                commodity=commodity,
                seasonal_factor=seasonal_factor,
                market_condition=market_condition
            )
        except Exception as e:
            logger.error(f"Error getting cultural guidance: {e}")
            # Return enhanced fallback guidance
            return CulturalGuidance(
                buyer_region=buyer_region,
                seller_region=seller_region,
                cultural_context=CulturalContext.MODERN,
                greeting_style="Respectful and professional greeting with appropriate regional customs",
                negotiation_approach="Collaborative approach with cultural sensitivity and patience",
                cultural_sensitivities=[
                    "Respect regional customs and traditions",
                    "Show patience with different communication styles",
                    "Acknowledge cultural differences positively",
                    "Build relationship before focusing on business",
                    "Use appropriate language and tone"
                ],
                recommended_phrases={
                    "en": "Let's find a solution that honors both our traditions and business needs",
                    "hi": "आइए एक ऐसा समाधान खोजते हैं जो हमारी परंपराओं और व्यावसायिक आवश्यकताओं दोनों का सम्मान करे"
                },
                taboo_topics=[
                    "Regional political tensions",
                    "Religious differences", 
                    "Personal financial struggles",
                    "Family disputes",
                    "Caste-related issues"
                ],
                time_orientation="flexible",
                relationship_importance="high"
            )
    
    async def update_negotiation(
        self, 
        negotiation_id: str, 
        user_id: str, 
        update_data: NegotiationUpdate
    ) -> NegotiationSession:
        """Update negotiation with new step."""
        try:
            # Get existing negotiation
            negotiation_data = await self.negotiations_collection.find_one(
                {"_id": ObjectId(negotiation_id)}
            )
            if not negotiation_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Negotiation not found"
                )
            
            negotiation = NegotiationSession(**negotiation_data)
            
            # Verify user is participant
            if user_id not in [negotiation.buyer_id, negotiation.seller_id]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to update this negotiation"
                )
            
            # Determine user role
            user_role = "buyer" if user_id == negotiation.buyer_id else "seller"
            
            # Create new step
            new_step = NegotiationStep(
                step_number=len(negotiation.steps) + 1,
                participant_id=user_id,
                participant_role=user_role,
                action=update_data.action,
                offer=update_data.offer,
                message=update_data.message,
                ai_recommendation_used=update_data.use_ai_recommendation
            )
            
            # Update negotiation status and current offer
            if update_data.action == "accept":
                negotiation.status = NegotiationStatus.ACCEPTED
                negotiation.completed_at = datetime.utcnow()
                if negotiation.current_offer:
                    negotiation.final_agreed_price = negotiation.current_offer.unit_price
                    negotiation.final_agreed_quantity = negotiation.current_offer.quantity
            elif update_data.action == "reject":
                negotiation.status = NegotiationStatus.REJECTED
                negotiation.completed_at = datetime.utcnow()
            elif update_data.action == "counter_offer" and update_data.offer:
                negotiation.status = NegotiationStatus.COUNTER_OFFERED
                negotiation.current_offer = update_data.offer
            
            # Add step to negotiation
            negotiation.steps.append(new_step)
            negotiation.updated_at = datetime.utcnow()
            
            # Update in database
            await self.negotiations_collection.update_one(
                {"_id": ObjectId(negotiation_id)},
                {"$set": negotiation.dict(by_alias=True, exclude={"id"})}
            )
            
            logger.info(f"Updated negotiation {negotiation_id} with action {update_data.action}")
            return negotiation
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating negotiation: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update negotiation"
            )
    
    async def get_cultural_sensitivity_indicators(
        self,
        buyer_region: str,
        seller_region: str,
        negotiation_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Get cultural sensitivity indicators for negotiation.
        
        Args:
            buyer_region: Buyer's region/state
            seller_region: Seller's region/state  
            negotiation_context: Additional context about the negotiation
            
        Returns:
            Cultural sensitivity indicators and recommendations
        """
        try:
            return await self.cultural_service.get_cultural_sensitivity_indicators(
                buyer_region=buyer_region,
                seller_region=seller_region,
                negotiation_context=negotiation_context
            )
        except Exception as e:
            logger.error(f"Error getting cultural sensitivity indicators: {e}")
            return {
                "cultural_distance": 0.5,
                "compatibility_score": 0.5,
                "sensitivity_level": "moderate",
                "recommendations": ["Be respectful and patient"],
                "success_probability": 0.7
            }
    
    async def get_region_specific_negotiation_tips(
        self,
        target_region: str,
        user_role: str,
        commodity: str = None
    ) -> Dict[str, Any]:
        """
        Get region-specific negotiation tips.
        
        Args:
            target_region: The region to get tips for
            user_role: Whether user is "buyer" or "seller"
            commodity: Type of commodity being negotiated
            
        Returns:
            Region-specific tips and strategies
        """
        try:
            return await self.cultural_service.get_region_specific_tips(
                target_region=target_region,
                user_role=user_role,
                commodity=commodity
            )
        except Exception as e:
            logger.error(f"Error getting region-specific tips: {e}")
            return {
                "region": target_region,
                "role_specific_tips": [f"General {user_role} tips for {target_region}"],
                "communication_tips": ["Be respectful and patient"],
                "success_factors": ["Build good relationship", "Be fair in pricing"]
            }
    
    async def analyze_cultural_compatibility(
        self,
        buyer_region: str,
        seller_region: str
    ) -> Dict[str, Any]:
        """
        Analyze cultural compatibility between buyer and seller regions.
        
        Args:
            buyer_region: Buyer's region/state
            seller_region: Seller's region/state
            
        Returns:
            Detailed compatibility analysis
        """
        try:
            return await self.cultural_service.analyze_cultural_compatibility(
                buyer_region=buyer_region,
                seller_region=seller_region
            )
        except Exception as e:
            logger.error(f"Error analyzing cultural compatibility: {e}")
            return {
                "overall_compatibility": 0.7,
                "potential_challenges": ["Communication differences"],
                "bridging_strategies": ["Be patient and respectful"]
            }
    
    # Helper methods
    
    async def _get_market_context(
        self, 
        commodity: str, 
        location: Dict[str, Any]
    ) -> MarketContext:
        """Get market context for negotiation."""
        try:
            # Get current prices
            current_prices = await self.price_service.get_current_prices(
                commodity, 
                location.get("city", "Mumbai")
            )
            
            if current_prices:
                current_market_price = sum(p.price_modal for p in current_prices) / len(current_prices)
                price_trend = "stable"  # Simplified
            else:
                current_market_price = 100.0  # Fallback
                price_trend = "stable"
            
            return MarketContext(
                commodity=commodity,
                location=location.get("city", "Mumbai"),
                current_market_price=current_market_price,
                price_trend=price_trend,
                seasonal_factor=SeasonalFactor.HARVEST_SEASON,  # Mock
                market_condition=MarketCondition.STABLE,
                supply_demand_ratio=1.0,
                weather_impact="normal",
                festival_impact=None,
                msp_price=current_market_price * 0.9
            )
            
        except Exception as e:
            logger.error(f"Error getting market context: {e}")
            return MarketContext(
                commodity=commodity,
                location="Mumbai",
                current_market_price=100.0,
                price_trend="stable",
                market_condition=MarketCondition.STABLE,
                supply_demand_ratio=1.0
            )
    
    async def _get_cultural_guidance(
        self, 
        buyer: Dict[str, Any], 
        seller: Dict[str, Any]
    ) -> CulturalGuidance:
        """Get cultural guidance for negotiation."""
        buyer_region = buyer.get("buyer_profile", {}).get("location", {}).get("state", "Maharashtra")
        seller_region = seller.get("vendor_profile", {}).get("location", {}).get("state", "Maharashtra")
        
        # Get comprehensive cultural guidance
        return await self.cultural_service.get_comprehensive_cultural_guidance(
            buyer_region=buyer_region,
            seller_region=seller_region
        )
    
    def _get_quality_multiplier(self, quality_grade: str) -> float:
        """Get price multiplier based on quality grade."""
        multipliers = {
            "premium": 1.2,
            "standard": 1.0,
            "below_standard": 0.8
        }
        return multipliers.get(quality_grade.lower(), 1.0)
    
    def _calculate_quantity_discount(self, quantity: float, commodity: str) -> float:
        """Calculate quantity-based discount."""
        if quantity >= 1000:  # Bulk order
            return 0.1  # 10% discount
        elif quantity >= 500:
            return 0.05  # 5% discount
        elif quantity >= 100:
            return 0.02  # 2% discount
        return 0.0
    
    def _get_seasonal_adjustment(
        self, 
        seasonal_factor: Optional[SeasonalFactor], 
        commodity: str
    ) -> float:
        """Get seasonal price adjustment."""
        if not seasonal_factor:
            return 1.0
        
        adjustments = {
            SeasonalFactor.HARVEST_SEASON: 0.9,  # Lower prices during harvest
            SeasonalFactor.OFF_SEASON: 1.1,     # Higher prices off-season
            SeasonalFactor.FESTIVAL_SEASON: 1.15, # Higher prices during festivals
            SeasonalFactor.MONSOON: 1.05,       # Slightly higher due to transport
        }
        
        return adjustments.get(seasonal_factor, 1.0)
    
    def _get_market_condition_adjustment(self, market_condition: MarketCondition) -> float:
        """Get market condition adjustment."""
        adjustments = {
            MarketCondition.HIGH_DEMAND: 1.1,
            MarketCondition.LOW_DEMAND: 0.9,
            MarketCondition.OVERSUPPLY: 0.85,
            MarketCondition.SHORTAGE: 1.2,
            MarketCondition.STABLE: 1.0,
            MarketCondition.VOLATILE: 1.05
        }
        return adjustments.get(market_condition, 1.0)
    
    def _build_price_reasoning(
        self, 
        market_context: MarketContext, 
        quality_grade: str, 
        quantity: float, 
        user_role: str
    ) -> str:
        """Build reasoning for price recommendation."""
        reasoning_parts = [
            f"Based on current market price of ₹{market_context.current_market_price:.2f}",
            f"Quality grade '{quality_grade}' adjustment applied",
            f"Quantity of {quantity} units considered for bulk pricing"
        ]
        
        if market_context.seasonal_factor:
            reasoning_parts.append(f"Seasonal factor '{market_context.seasonal_factor}' impacts pricing")
        
        if market_context.market_condition != MarketCondition.STABLE:
            reasoning_parts.append(f"Market condition '{market_context.market_condition}' affects supply-demand")
        
        role_context = "buyer-favorable" if user_role == "buyer" else "seller-favorable"
        reasoning_parts.append(f"Recommendation optimized for {role_context} outcome")
        
        return ". ".join(reasoning_parts) + "."
    
    def _calculate_confidence_score(
        self, 
        market_context: MarketContext, 
        price_data_points: int
    ) -> float:
        """Calculate confidence score for recommendation."""
        base_confidence = 0.7
        
        # Adjust based on data availability
        if price_data_points >= 5:
            base_confidence += 0.2
        elif price_data_points >= 3:
            base_confidence += 0.1
        elif price_data_points == 0:
            base_confidence -= 0.3
        
        # Adjust based on market volatility
        if market_context.market_condition == MarketCondition.VOLATILE:
            base_confidence -= 0.1
        elif market_context.market_condition == MarketCondition.STABLE:
            base_confidence += 0.1
        
        return max(0.0, min(1.0, base_confidence))
    
    def _analyze_negotiation_pattern(
        self, 
        negotiation_history: List[NegotiationStep]
    ) -> Dict[str, Any]:
        """Analyze negotiation pattern from history."""
        if not negotiation_history:
            return {"pattern": "initial", "trend": "neutral"}
        
        offers = [step.offer for step in negotiation_history if step.offer]
        if len(offers) < 2:
            return {"pattern": "initial", "trend": "neutral"}
        
        # Analyze price trend
        prices = [offer.unit_price for offer in offers]
        if prices[-1] > prices[0]:
            trend = "increasing"
        elif prices[-1] < prices[0]:
            trend = "decreasing"
        else:
            trend = "stable"
        
        return {
            "pattern": "progressive",
            "trend": trend,
            "steps_count": len(negotiation_history),
            "price_range": max(prices) - min(prices) if prices else 0
        }
    
    def _determine_negotiation_strategy(
        self, 
        current_offer: Offer, 
        price_rec: PriceRecommendation, 
        pattern: Dict[str, Any], 
        user_role: str
    ) -> NegotiationStrategy:
        """Determine appropriate negotiation strategy."""
        # Simple strategy determination logic
        price_diff = abs(current_offer.unit_price - price_rec.recommended_price)
        relative_diff = price_diff / price_rec.recommended_price
        
        if relative_diff < 0.05:  # Very close to recommended price
            return NegotiationStrategy.ACCOMMODATING
        elif relative_diff < 0.15:  # Moderately close
            return NegotiationStrategy.COMPROMISING
        elif pattern.get("steps_count", 0) > 3:  # Long negotiation
            return NegotiationStrategy.COLLABORATIVE
        else:
            return NegotiationStrategy.COMPETITIVE
    
    def _build_counter_offer_justification(
        self, 
        current_offer: Offer, 
        suggested_price: float, 
        market_data: MarketContext, 
        strategy: NegotiationStrategy
    ) -> str:
        """Build justification for counter-offer."""
        price_change = ((suggested_price - current_offer.unit_price) / current_offer.unit_price) * 100
        
        justification_parts = [
            f"Counter-offer of ₹{suggested_price:.2f} represents a {abs(price_change):.1f}% {'increase' if price_change > 0 else 'decrease'}",
            f"Current market rate for {market_data.commodity} is ₹{market_data.current_market_price:.2f}",
            f"Market conditions show {market_data.market_condition.value} supply-demand balance"
        ]
        
        if strategy == NegotiationStrategy.COLLABORATIVE:
            justification_parts.append("This offer aims for mutual benefit and long-term relationship")
        elif strategy == NegotiationStrategy.COMPETITIVE:
            justification_parts.append("This competitive offer reflects current market dynamics")
        
        return ". ".join(justification_parts) + "."
    
    def _get_seasonal_factors(self, seasonal_factor: Optional[SeasonalFactor]) -> List[str]:
        """Get seasonal factors affecting negotiation."""
        if not seasonal_factor:
            return []
        
        factors_map = {
            SeasonalFactor.HARVEST_SEASON: ["Abundant supply", "Lower transportation costs"],
            SeasonalFactor.OFF_SEASON: ["Limited supply", "Higher storage costs"],
            SeasonalFactor.FESTIVAL_SEASON: ["Increased demand", "Premium pricing"],
            SeasonalFactor.MONSOON: ["Transportation challenges", "Quality concerns"]
        }
        
        return factors_map.get(seasonal_factor, [])
    
    def _get_market_factors(self, market_condition: MarketCondition) -> List[str]:
        """Get market factors affecting negotiation."""
        factors_map = {
            MarketCondition.HIGH_DEMAND: ["Strong buyer interest", "Limited inventory"],
            MarketCondition.LOW_DEMAND: ["Buyer's market", "Flexible pricing"],
            MarketCondition.OVERSUPPLY: ["Abundant options", "Competitive pricing"],
            MarketCondition.SHORTAGE: ["Limited availability", "Premium pricing"],
            MarketCondition.STABLE: ["Balanced market", "Fair pricing"],
            MarketCondition.VOLATILE: ["Price uncertainty", "Quick decisions needed"]
        }
        
        return factors_map.get(market_condition, [])
    
    def _calculate_counter_offer_success_probability(
        self, 
        current_offer: Offer, 
        suggested_price: float, 
        price_rec: PriceRecommendation, 
        pattern: Dict[str, Any]
    ) -> float:
        """Calculate success probability for counter-offer."""
        base_probability = 0.6
        
        # Adjust based on price reasonableness
        if price_rec.price_range_min <= suggested_price <= price_rec.price_range_max:
            base_probability += 0.2
        
        # Adjust based on negotiation history
        if pattern.get("steps_count", 0) > 5:  # Long negotiation
            base_probability -= 0.1
        
        # Adjust based on price change magnitude
        price_change = abs(suggested_price - current_offer.unit_price) / current_offer.unit_price
        if price_change > 0.2:  # Large change
            base_probability -= 0.15
        elif price_change < 0.05:  # Small change
            base_probability += 0.1
        
        return max(0.0, min(1.0, base_probability))
    
    def _determine_cultural_context(self, buyer_region: str, seller_region: str) -> CulturalContext:
        """Determine cultural context based on regions."""
        # Simplified mapping
        if buyer_region == seller_region:
            return CulturalContext.TRADITIONAL
        else:
            return CulturalContext.MODERN
    
    def _get_regional_guidance(self, buyer_region: str, seller_region: str) -> Dict[str, Any]:
        """Get region-specific negotiation guidance."""
        # Simplified guidance data
        return {
            "greeting_style": "Respectful and warm",
            "negotiation_approach": "Relationship-focused with patience",
            "cultural_sensitivities": [
                "Show respect for experience and age",
                "Allow time for decision-making",
                "Avoid aggressive tactics"
            ],
            "recommended_phrases": {
                "en": "Let's find a solution that works for both of us",
                "hi": "आइए एक ऐसा समाधान खोजते हैं जो हम दोनों के लिए काम करे"
            },
            "taboo_topics": ["Personal finances", "Family problems"],
            "time_orientation": "flexible",
            "relationship_importance": "high"
        }