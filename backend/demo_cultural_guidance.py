#!/usr/bin/env python3
"""
Demo script for Cultural Negotiation Guidance System.

This script demonstrates the comprehensive cultural guidance system
that provides region-specific negotiation tips, cultural sensitivity
indicators, and compatibility analysis for the multilingual mandi platform.
"""

import asyncio
import json
from motor.motor_asyncio import AsyncIOMotorClient
from app.services.cultural_guidance_service import CulturalGuidanceService
from app.data.cultural_negotiation_database import get_all_supported_states


async def demo_cultural_guidance():
    """Demonstrate the cultural guidance system."""
    print("🌍 Cultural Negotiation Guidance System Demo")
    print("=" * 60)
    
    # Create a mock database connection (in real usage, this would be the actual DB)
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["demo_cultural_guidance"]
    
    # Initialize the cultural guidance service
    cultural_service = CulturalGuidanceService(db)
    
    print(f"\n📍 Supported States: {len(get_all_supported_states())} states")
    print(f"States: {', '.join(get_all_supported_states())}")
    
    # Demo 1: Comprehensive Cultural Guidance
    print("\n" + "="*60)
    print("🤝 Demo 1: Comprehensive Cultural Guidance")
    print("="*60)
    
    buyer_region = "Punjab"
    seller_region = "Tamil Nadu"
    
    print(f"\nScenario: Buyer from {buyer_region} negotiating with Seller from {seller_region}")
    
    guidance = await cultural_service.get_comprehensive_cultural_guidance(
        buyer_region=buyer_region,
        seller_region=seller_region,
        commodity="rice"
    )
    
    print(f"\n🎯 Cultural Context: {guidance.cultural_context.value}")
    print(f"👋 Greeting Style: {guidance.greeting_style}")
    print(f"🤝 Negotiation Approach: {guidance.negotiation_approach}")
    print(f"⏰ Time Orientation: {guidance.time_orientation}")
    print(f"❤️ Relationship Importance: {guidance.relationship_importance}")
    
    print(f"\n🚨 Cultural Sensitivities:")
    for i, sensitivity in enumerate(guidance.cultural_sensitivities[:3], 1):
        print(f"  {i}. {sensitivity}")
    
    print(f"\n💬 Recommended Phrases:")
    for lang, phrase in guidance.recommended_phrases.items():
        print(f"  {lang.upper()}: {phrase}")
    
    print(f"\n🚫 Topics to Avoid:")
    for i, topic in enumerate(guidance.taboo_topics[:3], 1):
        print(f"  {i}. {topic}")
    
    # Demo 2: Cultural Sensitivity Indicators
    print("\n" + "="*60)
    print("📊 Demo 2: Cultural Sensitivity Indicators")
    print("="*60)
    
    indicators = await cultural_service.get_cultural_sensitivity_indicators(
        buyer_region=buyer_region,
        seller_region=seller_region
    )
    
    print(f"\n📏 Cultural Distance: {indicators['cultural_distance']:.2f}")
    print(f"🤝 Compatibility Score: {indicators['compatibility_score']:.2f}")
    print(f"⚠️ Sensitivity Level: {indicators['sensitivity_level']}")
    print(f"🎯 Success Probability: {indicators['success_probability']:.2f}")
    
    print(f"\n💡 Recommendations:")
    for i, rec in enumerate(indicators['recommendations'][:3], 1):
        print(f"  {i}. {rec}")
    
    # Demo 3: Region-Specific Tips
    print("\n" + "="*60)
    print("💡 Demo 3: Region-Specific Tips")
    print("="*60)
    
    target_region = "Gujarat"
    user_role = "buyer"
    
    print(f"\nTips for {user_role} negotiating in {target_region}:")
    
    tips = await cultural_service.get_region_specific_tips(
        target_region=target_region,
        user_role=user_role,
        commodity="cotton"
    )
    
    print(f"\n🎯 Role-Specific Tips:")
    for i, tip in enumerate(tips['role_specific_tips'][:3], 1):
        print(f"  {i}. {tip}")
    
    print(f"\n💬 Communication Tips:")
    for i, tip in enumerate(tips['communication_tips'][:3], 1):
        print(f"  {i}. {tip}")
    
    print(f"\n✅ Success Factors:")
    for i, factor in enumerate(tips['success_factors'][:3], 1):
        print(f"  {i}. {factor}")
    
    # Demo 4: Cultural Compatibility Analysis
    print("\n" + "="*60)
    print("🔍 Demo 4: Cultural Compatibility Analysis")
    print("="*60)
    
    buyer_region_2 = "Maharashtra"
    seller_region_2 = "West Bengal"
    
    print(f"\nAnalyzing compatibility: {buyer_region_2} ↔ {seller_region_2}")
    
    analysis = await cultural_service.analyze_cultural_compatibility(
        buyer_region=buyer_region_2,
        seller_region=seller_region_2
    )
    
    print(f"\n📊 Overall Compatibility: {analysis['overall_compatibility']:.2f}")
    
    print(f"\n⚠️ Potential Challenges:")
    for i, challenge in enumerate(analysis['potential_challenges'][:3], 1):
        print(f"  {i}. {challenge}")
    
    print(f"\n🌉 Bridging Strategies:")
    for i, strategy in enumerate(analysis['bridging_strategies'][:3], 1):
        print(f"  {i}. {strategy}")
    
    # Demo 5: Same Region vs Cross-Regional Comparison
    print("\n" + "="*60)
    print("⚖️ Demo 5: Same Region vs Cross-Regional Comparison")
    print("="*60)
    
    # Same region comparison
    same_region_indicators = await cultural_service.get_cultural_sensitivity_indicators(
        buyer_region="Punjab",
        seller_region="Haryana"  # Both North Indian
    )
    
    # Cross-regional comparison
    cross_region_indicators = await cultural_service.get_cultural_sensitivity_indicators(
        buyer_region="Punjab",  # North
        seller_region="Tamil Nadu"  # South
    )
    
    print(f"\n🏠 Same Region (Punjab ↔ Haryana):")
    print(f"  Cultural Distance: {same_region_indicators['cultural_distance']:.2f}")
    print(f"  Compatibility: {same_region_indicators['compatibility_score']:.2f}")
    print(f"  Success Probability: {same_region_indicators['success_probability']:.2f}")
    
    print(f"\n🌏 Cross-Regional (Punjab ↔ Tamil Nadu):")
    print(f"  Cultural Distance: {cross_region_indicators['cultural_distance']:.2f}")
    print(f"  Compatibility: {cross_region_indicators['compatibility_score']:.2f}")
    print(f"  Success Probability: {cross_region_indicators['success_probability']:.2f}")
    
    print(f"\n📈 Analysis:")
    if same_region_indicators['compatibility_score'] > cross_region_indicators['compatibility_score']:
        print("  ✅ Same region negotiations show higher compatibility as expected")
    else:
        print("  ⚠️ Cross-regional compatibility is surprisingly high")
    
    # Demo 6: API Endpoints Available
    print("\n" + "="*60)
    print("🔗 Demo 6: Available API Endpoints")
    print("="*60)
    
    endpoints = [
        "GET /api/v1/negotiation/cultural-guidance",
        "GET /api/v1/negotiation/cultural-sensitivity-indicators", 
        "GET /api/v1/negotiation/region-specific-tips",
        "GET /api/v1/negotiation/cultural-compatibility",
        "GET /api/v1/negotiation/supported-regions",
        "GET /api/v1/negotiation/cultural-database-stats"
    ]
    
    print("\n🌐 Cultural Guidance API Endpoints:")
    for endpoint in endpoints:
        print(f"  • {endpoint}")
    
    print(f"\n🎉 Cultural Negotiation Guidance System Demo Complete!")
    print(f"📝 Features Implemented:")
    print(f"  ✅ Regional negotiation etiquette database ({len(get_all_supported_states())} states)")
    print(f"  ✅ Cultural guidance recommendation engine")
    print(f"  ✅ Region-specific negotiation tips")
    print(f"  ✅ Cultural sensitivity indicators")
    print(f"  ✅ Compatibility analysis and bridging strategies")
    print(f"  ✅ Comprehensive API endpoints")
    print(f"  ✅ Property-based testing validation")
    
    # Cleanup
    client.close()


if __name__ == "__main__":
    asyncio.run(demo_cultural_guidance())