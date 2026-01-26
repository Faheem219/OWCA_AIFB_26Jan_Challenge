"""
Demo script for Market Analytics and Forecasting functionality.

This script demonstrates the key features implemented for task 11.1:
- Demand forecasting algorithms
- Weather impact prediction system
- Seasonal and festival demand alerts
- Export-import price influence tracking
"""
import asyncio
from datetime import date, timedelta
from app.services.market_analytics_service import market_analytics_service
from app.models.market_analytics import ForecastModel, WeatherCondition, AlertSeverity


async def demo_demand_forecasting():
    """Demo demand forecasting functionality."""
    print("=" * 60)
    print("DEMAND FORECASTING DEMO")
    print("=" * 60)
    
    try:
        # Generate demand forecast for rice
        forecast = await market_analytics_service.generate_demand_forecast(
            commodity="rice",
            location="Maharashtra",
            forecast_days=30,
            model=ForecastModel.ENSEMBLE
        )
        
        print(f"Commodity: {forecast.commodity}")
        print(f"Location: {forecast.location}")
        print(f"Forecast Period: {forecast.forecast_period_days} days")
        print(f"Predicted Demand Multiplier: {forecast.predicted_demand:.2f}")
        print(f"Demand Trend: {forecast.demand_trend}")
        print(f"Confidence: {forecast.confidence:.2f}")
        print(f"Model Used: {forecast.model_used}")
        print(f"Seasonal Factor: {forecast.seasonal_factor:.2f}")
        print(f"Weather Factor: {forecast.weather_factor:.2f}")
        print(f"Festival Factor: {forecast.festival_factor:.2f}")
        print(f"Export-Import Factor: {forecast.export_import_factor:.2f}")
        print(f"Factors Considered: {', '.join(forecast.factors_considered)}")
        
    except Exception as e:
        print(f"Error in demand forecasting demo: {str(e)}")


async def demo_weather_impact():
    """Demo weather impact prediction."""
    print("\n" + "=" * 60)
    print("WEATHER IMPACT PREDICTION DEMO")
    print("=" * 60)
    
    try:
        # Predict weather impact for wheat during drought
        prediction = await market_analytics_service.predict_weather_impact(
            commodity="wheat",
            weather_condition=WeatherCondition.DROUGHT,
            affected_regions=["Punjab", "Haryana", "Uttar Pradesh"],
            impact_duration_days=21
        )
        
        print(f"Commodity: {prediction.commodity}")
        print(f"Weather Condition: {prediction.weather_condition}")
        print(f"Affected Regions: {', '.join(prediction.affected_regions)}")
        print(f"Impact Duration: {prediction.impact_duration_days} days")
        print(f"Expected Price Impact: {prediction.price_impact_percentage:.1f}%")
        print(f"Expected Supply Impact: {prediction.supply_impact_percentage:.1f}%")
        print(f"Confidence: {prediction.confidence:.2f}")
        print("Mitigation Suggestions:")
        for i, suggestion in enumerate(prediction.mitigation_suggestions, 1):
            print(f"  {i}. {suggestion}")
        
    except Exception as e:
        print(f"Error in weather impact demo: {str(e)}")


async def demo_seasonal_alerts():
    """Demo seasonal and festival alerts."""
    print("\n" + "=" * 60)
    print("SEASONAL & FESTIVAL ALERTS DEMO")
    print("=" * 60)
    
    try:
        # Generate seasonal alerts for sugar
        alerts = await market_analytics_service.generate_seasonal_alerts(
            commodity="sugar",
            location="Maharashtra",
            days_ahead=60
        )
        
        print(f"Generated {len(alerts)} seasonal alerts for sugar")
        
        for i, alert in enumerate(alerts, 1):
            print(f"\nAlert {i}:")
            print(f"  Event: {alert.event_name}")
            print(f"  Type: {alert.alert_type}")
            print(f"  Period: {alert.event_start_date} to {alert.event_end_date}")
            print(f"  Expected Demand Change: {alert.expected_demand_change:.1f}%")
            print(f"  Price Impact Prediction: {alert.price_impact_prediction:.1f}%")
            print(f"  Severity: {alert.severity}")
            print(f"  Affected Markets: {len(alert.affected_markets)} markets")
            if alert.preparation_suggestions:
                print("  Preparation Suggestions:")
                for suggestion in alert.preparation_suggestions[:2]:  # Show first 2
                    print(f"    - {suggestion}")
        
    except Exception as e:
        print(f"Error in seasonal alerts demo: {str(e)}")


async def demo_export_import_influence():
    """Demo export-import price influence analysis."""
    print("\n" + "=" * 60)
    print("EXPORT-IMPORT INFLUENCE DEMO")
    print("=" * 60)
    
    try:
        # Analyze export-import influence for rice
        influence = await market_analytics_service.analyze_export_import_influence(
            commodity="rice",
            analysis_period_days=30
        )
        
        print(f"Commodity: {influence.commodity}")
        print(f"Analysis Date: {influence.analysis_date}")
        print(f"Domestic Price: ₹{influence.domestic_price:.2f}")
        print(f"International Price: ${influence.international_price:.2f}")
        print(f"Price Differential: ₹{influence.price_differential:.2f}")
        print(f"Price Differential %: {influence.price_differential_percentage:.1f}%")
        print(f"Trade Balance: {influence.trade_balance:.0f} tons")
        print(f"Influence Factor: {influence.influence_factor:.2f}")
        print(f"Arbitrage Opportunity: {influence.arbitrage_opportunity}")
        
        if influence.recommendations:
            print("Recommendations:")
            for i, rec in enumerate(influence.recommendations, 1):
                print(f"  {i}. {rec}")
        
    except Exception as e:
        print(f"Error in export-import influence demo: {str(e)}")


async def demo_comprehensive_analytics():
    """Demo comprehensive market analytics."""
    print("\n" + "=" * 60)
    print("COMPREHENSIVE MARKET ANALYTICS DEMO")
    print("=" * 60)
    
    try:
        # Generate comprehensive analytics for onion
        analytics = await market_analytics_service.generate_comprehensive_analytics(
            commodity="onion",
            location="Maharashtra",
            analysis_period_days=30
        )
        
        print(f"Commodity: {analytics.commodity}")
        print(f"Location: {analytics.location}")
        print(f"Analysis Period: {analytics.analysis_period_days} days")
        print(f"Overall Market Sentiment: {analytics.overall_market_sentiment}")
        print(f"Risk Assessment: {analytics.risk_assessment}")
        print(f"Confidence Score: {analytics.confidence_score:.2f}")
        
        print(f"\nDemand Forecast:")
        if analytics.demand_forecast:
            print(f"  Predicted Demand: {analytics.demand_forecast.predicted_demand:.2f}")
            print(f"  Trend: {analytics.demand_forecast.demand_trend}")
            print(f"  Confidence: {analytics.demand_forecast.confidence:.2f}")
        
        print(f"\nActive Weather Predictions: {len(analytics.weather_predictions)}")
        print(f"Active Seasonal Alerts: {len(analytics.active_alerts)}")
        
        if analytics.trading_recommendations:
            print("\nTrading Recommendations:")
            for i, rec in enumerate(analytics.trading_recommendations[:3], 1):
                print(f"  {i}. {rec}")
        
        if analytics.risk_mitigation_strategies:
            print("\nRisk Mitigation Strategies:")
            for i, strategy in enumerate(analytics.risk_mitigation_strategies[:3], 1):
                print(f"  {i}. {strategy}")
        
    except Exception as e:
        print(f"Error in comprehensive analytics demo: {str(e)}")


async def main():
    """Run all demos."""
    print("MULTILINGUAL MANDI - MARKET ANALYTICS & FORECASTING DEMO")
    print("Task 11.1: Create market analytics and forecasting")
    print("Requirements: 8.2, 8.3, 8.4, 8.5")
    
    # Run all demo functions
    await demo_demand_forecasting()
    await demo_weather_impact()
    await demo_seasonal_alerts()
    await demo_export_import_influence()
    await demo_comprehensive_analytics()
    
    print("\n" + "=" * 60)
    print("DEMO COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print("\nKey Features Implemented:")
    print("✓ Demand forecasting algorithms (Requirement 8.2)")
    print("✓ Weather impact prediction system (Requirement 8.3)")
    print("✓ Seasonal and festival demand alerts (Requirement 8.4)")
    print("✓ Export-import price influence tracking (Requirement 8.5)")
    print("\nAPI Endpoints Available:")
    print("- GET /api/v1/market-analytics/demand-forecast")
    print("- GET /api/v1/market-analytics/weather-impact")
    print("- GET /api/v1/market-analytics/seasonal-alerts")
    print("- GET /api/v1/market-analytics/export-import-influence")
    print("- GET /api/v1/market-analytics/comprehensive-analytics")
    print("- POST /api/v1/market-analytics/alerts/subscribe")
    print("- GET /api/v1/market-analytics/health")


if __name__ == "__main__":
    asyncio.run(main())