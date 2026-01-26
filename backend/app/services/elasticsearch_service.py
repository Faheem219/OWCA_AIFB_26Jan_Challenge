"""
MongoDB text search service for multilingual product search and indexing.

This service provides search functionality using MongoDB's text indexing
as an alternative to Elasticsearch for simplified deployment.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from decimal import Decimal
import re

from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection

from app.core.config import settings
from app.core.database import get_database
from app.models.product import (
    Product,
    ProductSearchQuery,
    ProductResponse,
    SupportedLanguage,
    ProductCategory,
    QualityGrade,
    ProductStatus
)

logger = logging.getLogger(__name__)


class ElasticsearchService:
    """MongoDB-based search service for product search and indexing."""
    
    def __init__(self):
        self.db = None
        self.products_collection: Optional[AsyncIOMotorCollection] = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize MongoDB connection and create text indices if needed."""
        try:
            self.db = await get_database()
            self.products_collection = self.db.products
            
            # Create text index for multilingual search
            await self._create_text_indexes()
            
            self._initialized = True
            logger.info("MongoDB text search initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize MongoDB text search: {e}")
            self._initialized = False
    
    async def close(self) -> None:
        """Close MongoDB connection (handled by database module)."""
        self._initialized = False
        logger.info("MongoDB text search service closed")
    
    async def _ensure_initialized(self) -> bool:
        """Ensure service is initialized."""
        if not self._initialized:
            await self.initialize()
        return self._initialized
    
    async def _create_text_indexes(self) -> None:
        """Create text indices for product search."""
        try:
            # Drop existing text index if any
            try:
                await self.products_collection.drop_index("product_text_search")
            except:
                pass  # Index might not exist
            
            # Create compound text index on multiple fields
            await self.products_collection.create_index(
                [
                    ("name.original_text", "text"),
                    ("name.translations.en", "text"),
                    ("name.translations.hi", "text"),
                    ("name.translations.ta", "text"),
                    ("name.translations.te", "text"),
                    ("name.translations.kn", "text"),
                    ("name.translations.ml", "text"),
                    ("name.translations.gu", "text"),
                    ("name.translations.pa", "text"),
                    ("name.translations.bn", "text"),
                    ("name.translations.mr", "text"),
                    ("description.original_text", "text"),
                    ("tags", "text"),
                    ("variety", "text"),
                    ("origin", "text")
                ],
                name="product_text_search",
                default_language="english"
            )
            
            # Create additional indexes for filtering
            await self.products_collection.create_index([("status", 1)])
            await self.products_collection.create_index([("category", 1)])
            await self.products_collection.create_index([("price", 1)])
            await self.products_collection.create_index([("location.state", 1)])
            await self.products_collection.create_index([("location.city", 1)])
            await self.products_collection.create_index([("location.coordinates", "2dsphere")])
            await self.products_collection.create_index([("vendor_id", 1)])
            await self.products_collection.create_index([("created_at", -1)])
            
            logger.info("MongoDB text indexes created successfully")
            
        except Exception as e:
            logger.error(f"Error creating text indexes: {e}")
                            "search_keywords": {"type": "keyword"},
                            "certifications": {"type": "keyword"},
                            "origin": {"type": "text"},
                            "variety": {"type": "text"},
                            
                            # Dates and timestamps
                            "harvest_date": {"type": "date"},
                            "expiry_date": {"type": "date"},
                            "created_at": {"type": "date"},
                            "updated_at": {"type": "date"},
                            
                            # Stats
                            "views_count": {"type": "integer"},
                            "favorites_count": {"type": "integer"},
                            
                            # Vendor information
                            "vendor_name": {"type": "text"},
                            "vendor_rating": {"type": "float"},
                            "vendor_location": {"type": "text"}
                        }
                    },
                    "settings": {
                        "number_of_shards": 1,
                        "number_of_replicas": 0,
                        "analysis": {
                            "analyzer": {
                                "multilingual_analyzer": {
                                    "type": "standard",
                                    "stopwords": "_none_"
                                }
                            }
                        }
                    }
                }
                
                await self.client.indices.create(index=self.index_name, body=mapping)
                logger.info(f"Created Elasticsearch index: {self.index_name}")
            
            logger.error(f"Error creating text indexes: {e}")
    
    async def index_product(self, product: Product, vendor_info: Optional[Dict[str, Any]] = None) -> bool:
        """
        Index a product in MongoDB (no-op, products are already in MongoDB).
        
        Args:
            product: Product to index
            vendor_info: Optional vendor information
            
        Returns:
            True (MongoDB collection already contains the product)
        """
        # With MongoDB, products are already in the collection
        # No separate indexing needed as we use MongoDB's text indexes
        logger.debug(f"Product {product.product_id} is already indexed in MongoDB")
        return True
    
    async def delete_product(self, product_id: str) -> bool:
        """
        Delete a product from search index (no-op for MongoDB).
        
        Args:
            product_id: Product ID to delete
            
        Returns:
            True (product deletion is handled by product service)
        """
        # Product deletion is handled by the product service directly
        logger.debug(f"Product {product_id} deletion handled by product service")
        return True
    
    async def search_products(
        self,
        query: ProductSearchQuery
    ) -> Tuple[List[Dict[str, Any]], int, Dict[str, Any]]:
        """
        Search products using MongoDB text search with multilingual support.
        
        Args:
            query: Search query parameters
            
        Returns:
            Tuple of (search results, total count, search metadata)
        """
        try:
            if not await self._ensure_initialized():
                return [], 0, {}
            
            start_time = datetime.utcnow()
            
            # Build MongoDB query
            mongo_filter = self._build_mongo_filter(query)
            
            # Build sort criteria
            sort_criteria = self._build_mongo_sort(query)
            
            # Execute search with text search if query provided
            if query.query:
                # Use text search
                mongo_filter["$text"] = {"$search": query.query}
                
                # Add text score for sorting
                projection = {"score": {"$meta": "textScore"}}
                
                # Execute query with projection
                cursor = self.products_collection.find(
                    mongo_filter,
                    projection
                ).sort([("score", {"$meta": "textScore"})] + sort_criteria)
            else:
                # Regular query without text search
                cursor = self.products_collection.find(mongo_filter).sort(sort_criteria)
            
            # Apply pagination
            cursor = cursor.skip(query.skip).limit(query.limit)
            
            # Fetch results
            products = await cursor.to_list(length=query.limit)
            
            # Get total count
            total_count = await self.products_collection.count_documents(mongo_filter)
            
            end_time = datetime.utcnow()
            search_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Convert ObjectId to string and clean up
            for product in products:
                if "_id" in product:
                    product["_id"] = str(product["_id"])
                if "score" in product:
                    product["_score"] = product.pop("score")
            
            # Build search metadata
            search_metadata = {
                "query": query.query,
                "language": query.language.value if query.language else "en",
                "search_time_ms": search_time_ms,
                "total_hits": total_count,
                "backend": "mongodb_text_search"
            }
            
            return products, total_count, search_metadata
            
        except Exception as e:
            logger.error(f"MongoDB search failed: {e}")
            return [], 0, {"error": str(e)}
    
    def _build_mongo_filter(self, query: ProductSearchQuery) -> Dict[str, Any]:
        """Build MongoDB filter from search parameters."""
        mongo_filter = {}
        
        # Status filter (only active products)
        mongo_filter["status"] = ProductStatus.ACTIVE.value
        
        # Category filter
        if query.category:
            mongo_filter["category"] = query.category.value
        
        # Subcategory filter
        if query.subcategory:
            mongo_filter["subcategory"] = {"$regex": query.subcategory, "$options": "i"}
        
        # Price range filter
        if query.min_price is not None or query.max_price is not None:
            price_filter = {}
            if query.min_price is not None:
                price_filter["$gte"] = float(query.min_price)
            if query.max_price is not None:
                price_filter["$lte"] = float(query.max_price)
            mongo_filter["price_info.base_price"] = price_filter
        
        # Location filters
        if query.city:
            mongo_filter["location.city"] = {"$regex": query.city, "$options": "i"}
        
        if query.state:
            mongo_filter["location.state"] = {"$regex": query.state, "$options": "i"}
        
        # Geospatial search
        if query.coordinates and query.radius_km:
            mongo_filter["location.coordinates"] = {
                "$nearSphere": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [query.coordinates[0], query.coordinates[1]]
                    },
                    "$maxDistance": query.radius_km * 1000  # Convert km to meters
                }
            }
        
        # Quality grades filter
        if query.quality_grades:
            mongo_filter["quality_grade"] = {
                "$in": [grade.value for grade in query.quality_grades]
            }
        
        # Availability filter
        if query.available_only:
            mongo_filter["availability.quantity_available"] = {"$gt": 0}
        
        # Organic filter
        if query.organic_only:
            mongo_filter["$or"] = [
                {"quality_grade": QualityGrade.ORGANIC.value},
                {"metadata.certifications": {"$in": ["organic", "bio", "natural"]}}
            ]
        
        return mongo_filter
    
    def _build_mongo_sort(self, query: ProductSearchQuery) -> List[Tuple[str, int]]:
        """Build MongoDB sort criteria."""
        sort_criteria = []
        
        # Text score sorting is handled separately in search_products
        
        if query.sort_by == "price":
            sort_criteria.append(("price_info.base_price", 1 if query.sort_order == "asc" else -1))
        elif query.sort_by == "date":
            sort_criteria.append(("created_at", -1 if query.sort_order == "desc" else 1))
        elif query.sort_by == "popularity":
            sort_criteria.append(("views_count", -1))
        elif query.sort_by == "relevance":
            # Relevance is handled by text score
            pass
        else:
            # Default: newest first
            sort_criteria.append(("created_at", -1))
        
        return sort_criteria
            
            # Execute search
            start_time = datetime.utcnow()
            
            response = await self.client.search(
                index=self.index_name,
                body=es_query,
                from_=query.skip,
                size=query.limit
            )
            
            end_time = datetime.utcnow()
            search_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Extract results
            hits = response["hits"]["hits"]
            total_count = response["hits"]["total"]["value"]
            
            # Convert hits to product data
            products = []
            for hit in hits:
                source = hit["_source"]
                source["_score"] = hit["_score"]
                products.append(source)
            
            # Build search metadata
            search_metadata = {
                "query": query.query,
                "language": query.language.value,
                "search_time_ms": search_time_ms,
                "total_hits": total_count,
                "max_score": response["hits"]["max_score"],
                "suggestions": await self._get_search_suggestions(query, response)
            }
            
            return products, total_count, search_metadata
            
        except Exception as e:
            logger.error(f"Elasticsearch search failed: {e}")
            return [], 0, {"error": str(e)}
    
    async def _build_elasticsearch_query(self, query: ProductSearchQuery) -> Dict[str, Any]:
        """Build Elasticsearch query from search parameters."""
        es_query = {
            "query": {
                "bool": {
                    "must": [],
                    "filter": [],
                    "should": [],
                    "must_not": []
                }
            },
            "sort": [],
            "highlight": {
                "fields": {
                    "name.original_text": {},
                    "description.original_text": {},
                    f"name.translations.{query.language.value}": {},
                    f"description.translations.{query.language.value}": {}
                }
            }
        }
        
        # Text search with multilingual support
        if query.query:
            text_query = {
                "multi_match": {
                    "query": query.query,
                    "fields": [
                        "name.original_text^3",
                        "description.original_text^2",
                        f"name.translations.{query.language.value}^3",
                        f"description.translations.{query.language.value}^2",
                        "tags^2",
                        "search_keywords^2",
                        "variety",
                        "origin"
                    ],
                    "type": "best_fields",
                    "fuzziness": "AUTO",
                    "operator": "or"
                }
            }
            es_query["query"]["bool"]["must"].append(text_query)
        else:
            # If no text query, match all
            es_query["query"]["bool"]["must"].append({"match_all": {}})
        
        # Status filter (only active products)
        es_query["query"]["bool"]["filter"].append({
            "term": {"status": ProductStatus.ACTIVE.value}
        })
        
        # Category filter
        if query.category:
            es_query["query"]["bool"]["filter"].append({
                "term": {"category": query.category.value}
            })
        
        # Subcategory filter
        if query.subcategory:
            es_query["query"]["bool"]["filter"].append({
                "match": {"subcategory": query.subcategory}
            })
        
        # Price range filter
        if query.min_price is not None or query.max_price is not None:
            price_range = {}
            if query.min_price is not None:
                price_range["gte"] = float(query.min_price)
            if query.max_price is not None:
                price_range["lte"] = float(query.max_price)
            
            es_query["query"]["bool"]["filter"].append({
                "range": {"price": price_range}
            })
        
        # Location filters
        if query.city:
            es_query["query"]["bool"]["filter"].append({
                "term": {"location.city": query.city.lower()}
            })
        
        if query.state:
            es_query["query"]["bool"]["filter"].append({
                "term": {"location.state": query.state.lower()}
            })
        
        # Geospatial search
        if query.coordinates and query.radius_km:
            es_query["query"]["bool"]["filter"].append({
                "geo_distance": {
                    "distance": f"{query.radius_km}km",
                    "location.coordinates": {
                        "lat": query.coordinates[1],
                        "lon": query.coordinates[0]
                    }
                }
            })
        
        # Quality grades filter
        if query.quality_grades:
            es_query["query"]["bool"]["filter"].append({
                "terms": {"quality_grade": [grade.value for grade in query.quality_grades]}
            })
        
        # Availability filter
        if query.available_only:
            es_query["query"]["bool"]["filter"].append({
                "range": {"quantity_available": {"gt": 0}}
            })
        
        # Organic filter
        if query.organic_only:
            es_query["query"]["bool"]["should"].extend([
                {"term": {"quality_grade": QualityGrade.ORGANIC.value}},
                {"terms": {"certifications": ["organic", "bio", "natural"]}}
            ])
            es_query["query"]["bool"]["minimum_should_match"] = 1
        
        
        return sort_criteria
    
    async def bulk_index_products(self, products: List[Tuple[Product, Optional[Dict[str, Any]]]]) -> Dict[str, int]:
        """
        Bulk index multiple products (no-op for MongoDB as products are already indexed).
        
        Args:
            products: List of (product, vendor_info) tuples
            
        Returns:
            Dictionary with success/failure counts
        """
        # With MongoDB, products are already in the collection
        # No separate bulk indexing needed
        logger.info(f"Bulk indexing {len(products)} products (using MongoDB collection)")
        return {"success": len(products), "failed": 0}
    
    async def get_search_analytics(self) -> Dict[str, Any]:
        """Get search analytics and statistics."""
        try:
            if not await self._ensure_initialized():
                return {}
            
            # Get collection statistics
            total_products = await self.products_collection.count_documents({})
            active_products = await self.products_collection.count_documents(
                {"status": ProductStatus.ACTIVE.value}
            )
            
            # Get category distribution
            category_pipeline = [
                {"$group": {"_id": "$category", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            category_dist = await self.products_collection.aggregate(category_pipeline).to_list(None)
            
            return {
                "total_products": total_products,
                "active_products": active_products,
                "inactive_products": total_products - active_products,
                "category_distribution": {
                    cat["_id"]: cat["count"] for cat in category_dist if cat["_id"]
                },
                "search_backend": "mongodb_text_search"
            }
            
        except Exception as e:
            logger.error(f"Failed to get search analytics: {e}")
            return {}


# Global elasticsearch service instance (now MongoDB-based)
elasticsearch_service = ElasticsearchService()
            
            # Get aggregations for analytics
            aggs_query = {
                "size": 0,
                "aggs": {
                    "categories": {
                        "terms": {"field": "category", "size": 10}
                    },
                    "cities": {
                        "terms": {"field": "location.city", "size": 10}
                    },
                    "quality_grades": {
                        "terms": {"field": "quality_grade", "size": 10}
                    },
                    "price_stats": {
                        "stats": {"field": "price"}
                    }
                }
            }
            
            aggs_response = await self.client.search(
                index=self.index_name,
                body=aggs_query
            )
            
            return {
                "total_products": stats["indices"][self.index_name]["total"]["docs"]["count"],
                "index_size": stats["indices"][self.index_name]["total"]["store"]["size_in_bytes"],
                "categories": aggs_response["aggregations"]["categories"]["buckets"],
                "cities": aggs_response["aggregations"]["cities"]["buckets"],
                "quality_grades": aggs_response["aggregations"]["quality_grades"]["buckets"],
                "price_stats": aggs_response["aggregations"]["price_stats"]
            }
            
        except Exception as e:
            logger.error(f"Failed to get search analytics: {e}")
            return {}


# Global Elasticsearch service instance
elasticsearch_service = ElasticsearchService()