"""
JSON Schema definitions for outfit recommendation system.
Includes request/response schemas for validation and documentation.
"""

ITEM_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "ClothingItem",
    "description": "A single clothing item in the catalog",
    "type": "object",
    "required": ["item_id", "title", "role", "color", "style"],
    "properties": {
        "item_id": {
            "type": "string",
            "description": "Unique identifier for the item"
        },
        "title": {
            "type": "string",
            "description": "Human-readable name (e.g., '白色棉質襯衫')"
        },
        "description": {
            "type": "string",
            "description": "Detailed description for embedding"
        },
        "role": {
            "type": "string",
            "enum": ["top", "bottom", "outer", "shoes", "accessory"],
            "description": "Position/role in outfit"
        },
        "color": {
            "type": "string",
            "description": "Primary color (e.g., 'white', 'navy')"
        },
        "colors_secondary": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Secondary colors"
        },
        "style": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": ["casual", "formal", "sporty", "boho", "street", "smart-casual", "elegant", "vintage"]
            },
            "description": "Style categories"
        },
        "material": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Material composition (e.g., ['cotton', 'polyester'])"
        },
        "pattern": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Pattern types (e.g., ['plain', 'stripe', 'floral'])"
        },
        "season": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": ["spring", "summer", "fall", "winter"]
            },
            "description": "Suitable seasons"
        },
        "fit": {
            "type": "string",
            "enum": ["slim", "regular", "relaxed", "oversized"],
            "description": "Fit type"
        },
        "length": {
            "type": "string",
            "enum": ["short", "knee", "midi", "long"],
            "description": "Length category"
        },
        "gender": {
            "type": "string",
            "enum": ["male", "female", "unisex"],
            "description": "Target gender"
        },
        "age_range": {
            "type": "array",
            "items": {"type": "integer"},
            "minItems": 2,
            "maxItems": 2,
            "description": "[min_age, max_age]"
        },
        "brand": {
            "type": "string",
            "description": "Brand name (optional)"
        },
        "price_usd": {
            "type": "number",
            "description": "Price in USD"
        },
        "popularity": {
            "type": "number",
            "minimum": 0,
            "maximum": 1,
            "description": "Popularity score (0-1)"
        },
        "available": {
            "type": "boolean",
            "default": true,
            "description": "In-stock status"
        },
        "image_url": {
            "type": "string",
            "format": "uri",
            "description": "Product image URL"
        },
        "embedding": {
            "type": "array",
            "items": {"type": "number"},
            "description": "Text/visual embedding vector"
        },
        "tags": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Searchable tags"
        },
        "metadata": {
            "type": "object",
            "description": "Additional metadata"
        }
    }
}


WEATHER_CONTEXT_SCHEMA = {
    "title": "WeatherContext",
    "type": "object",
    "required": ["temp_c", "condition"],
    "properties": {
        "temp_c": {
            "type": "integer",
            "description": "Temperature in Celsius"
        },
        "humidity": {
            "type": "integer",
            "minimum": 0,
            "maximum": 100,
            "description": "Humidity percentage"
        },
        "condition": {
            "type": "string",
            "enum": ["sunny", "cloudy", "rainy", "snowy", "windy", "hot", "cold"],
            "description": "Weather condition"
        },
        "uv_index": {
            "type": "number",
            "description": "UV index (0-12+)"
        },
        "wind_speed_kmh": {
            "type": "number",
            "description": "Wind speed in km/h"
        }
    }
}


USER_CONTEXT_SCHEMA = {
    "title": "UserContext",
    "description": "User preferences and session context",
    "type": "object",
    "required": ["user_id", "weather", "occasion"],
    "properties": {
        "user_id": {
            "type": "string",
            "description": "Unique user identifier"
        },
        "date_time": {
            "type": "string",
            "format": "date-time",
            "description": "Request timestamp"
        },
        "location": {
            "type": "string",
            "description": "City or location name"
        },
        "weather": {
            "$ref": "#/definitions/WeatherContext"
        },
        "preferences": {
            "type": "object",
            "properties": {
                "styles": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "colors": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "avoid": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Colors/styles to avoid"
                },
                "fit_pref": {
                    "type": "string"
                }
            }
        },
        "occasion": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": ["work", "date", "casual_walk", "gym", "party", "outdoor", "home", "travel"]
            },
            "description": "Activity/occasion types"
        },
        "itinerary": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "time": {"type": "string"},
                    "activity": {"type": "string"},
                    "location": {"type": "string"}
                }
            },
            "description": "Daily schedule"
        },
        "palette_analysis": {
            "type": "object",
            "properties": {
                "dominant_colors": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "seasonal_palette": {
                    "type": "string"
                }
            },
            "description": "Results from color analysis (from step 1.5)"
        },
        "demographics": {
            "type": "object",
            "properties": {
                "age": {"type": "integer"},
                "gender": {"type": "string"}
            }
        },
        "last_worn_history": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Item IDs recently worn"
        }
    },
    "definitions": {
        "WeatherContext": WEATHER_CONTEXT_SCHEMA
    }
}


OUTFIT_RECOMMENDATION_SCHEMA = {
    "title": "OutfitRecommendation",
    "description": "A single outfit recommendation",
    "type": "object",
    "required": ["rank", "outfit_id", "items", "overall_score"],
    "properties": {
        "rank": {
            "type": "integer",
            "minimum": 1,
            "description": "Ranking position (1 = best)"
        },
        "outfit_id": {
            "type": "string",
            "description": "Unique outfit identifier"
        },
        "overall_score": {
            "type": "number",
            "minimum": 0,
            "maximum": 1,
            "description": "Overall recommendation score"
        },
        "confidence": {
            "type": "number",
            "minimum": 0,
            "maximum": 1,
            "description": "Model confidence in recommendation"
        },
        "items": {
            "type": "array",
            "minItems": 3,
            "description": "Outfit items",
            "items": {
                "type": "object",
                "required": ["role", "item_id", "title"],
                "properties": {
                    "role": {
                        "type": "string",
                        "enum": ["top", "bottom", "outer", "shoes", "accessory"]
                    },
                    "item_id": {"type": "string"},
                    "title": {"type": "string"},
                    "color": {"type": "string"},
                    "style": {"type": "string"},
                    "material": {"type": "string"},
                    "match_score": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1,
                        "description": "How well this item matches context"
                    },
                    "image_url": {
                        "type": "string",
                        "format": "uri"
                    }
                }
            }
        },
        "suitability": {
            "type": "object",
            "properties": {
                "temp_ok": {"type": "boolean"},
                "weather_ok": {"type": "boolean"},
                "occasion_ok": {"type": "boolean"},
                "weather_explanation": {"type": "string"}
            }
        },
        "reasons": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Bullet-point explanations (from LLM or heuristic)"
        },
        "accessory_suggestions": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Recommended accessories"
        },
        "color_harmony": {
            "type": "object",
            "properties": {
                "harmony_score": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1
                },
                "notes": {"type": "string"}
            }
        },
        "visual_preview_url": {
            "type": "string",
            "format": "uri",
            "description": "Link to outfit visualization"
        },
        "explainability_trace": {
            "type": "object",
            "description": "Feature scores for transparency",
            "properties": {
                "color_harmony_score": {"type": "number"},
                "style_match_score": {"type": "number"},
                "weather_suitability_score": {"type": "number"},
                "user_pref_alignment": {"type": "number"},
                "novelty_score": {"type": "number"}
            }
        }
    }
}


RECOMMENDATION_REQUEST_SCHEMA = {
    "title": "RecommendationRequest",
    "type": "object",
    "required": ["user_id", "weather", "occasion"],
    "properties": {
        "user_id": {"type": "string"},
        "weather": {"$ref": "#/definitions/WeatherContext"},
        "occasion": {
            "type": "array",
            "items": {"type": "string"}
        },
        "preferences": {
            "type": "object",
            "properties": {
                "styles": {"type": "array", "items": {"type": "string"}},
                "colors": {"type": "array", "items": {"type": "string"}}
            }
        },
        "palette_analysis": {
            "type": "object"
        },
        "demographics": {
            "type": "object"
        },
        "last_worn_history": {
            "type": "array",
            "items": {"type": "string"}
        },
        "top_n": {
            "type": "integer",
            "minimum": 1,
            "maximum": 10,
            "default": 3
        },
        "use_llm": {
            "type": "boolean",
            "default": false,
            "description": "Enable LLM-powered explanations"
        }
    },
    "definitions": {
        "WeatherContext": WEATHER_CONTEXT_SCHEMA
    }
}


RECOMMENDATION_RESPONSE_SCHEMA = {
    "title": "RecommendationResponse",
    "type": "object",
    "required": ["request_id", "user_id", "timestamp", "recommendations"],
    "properties": {
        "request_id": {
            "type": "string",
            "description": "Unique request identifier for tracking"
        },
        "user_id": {"type": "string"},
        "timestamp": {
            "type": "string",
            "format": "date-time"
        },
        "context_summary": {
            "type": "object",
            "description": "Echo of request context for validation"
        },
        "recommendations": {
            "type": "array",
            "minItems": 1,
            "items": {"$ref": "#/definitions/OutfitRecommendation"}
        },
        "metadata": {
            "type": "object",
            "properties": {
                "retrieval_time_ms": {"type": "number"},
                "ranking_time_ms": {"type": "number"},
                "llm_time_ms": {"type": "number"},
                "total_time_ms": {"type": "number"},
                "candidates_retrieved": {"type": "integer"},
                "candidates_assembled": {"type": "integer"},
                "llm_model": {"type": "string"},
                "ranking_model": {"type": "string"},
                "embedding_model": {"type": "string"}
            }
        },
        "exposure_control": {
            "type": "object",
            "description": "Diversity and exploration parameters",
            "properties": {
                "max_recs": {"type": "integer"},
                "diversity_penalty": {"type": "number"},
                "freshness_weight": {"type": "number"}
            }
        }
    },
    "definitions": {
        "OutfitRecommendation": OUTFIT_RECOMMENDATION_SCHEMA,
        "WeatherContext": WEATHER_CONTEXT_SCHEMA
    }
}


# Export all schemas
SCHEMAS = {
    "item": ITEM_SCHEMA,
    "weather_context": WEATHER_CONTEXT_SCHEMA,
    "user_context": USER_CONTEXT_SCHEMA,
    "outfit_recommendation": OUTFIT_RECOMMENDATION_SCHEMA,
    "recommendation_request": RECOMMENDATION_REQUEST_SCHEMA,
    "recommendation_response": RECOMMENDATION_RESPONSE_SCHEMA,
}


def validate_schema(data, schema_name: str) -> tuple[bool, str]:
    """
    Validate data against a schema.
    
    Args:
        data: Data to validate
        schema_name: One of the SCHEMAS keys
    
    Returns:
        (is_valid, error_message)
    """
    try:
        import jsonschema
    except ImportError:
        return False, "jsonschema package required: pip install jsonschema"
    
    schema = SCHEMAS.get(schema_name)
    if not schema:
        return False, f"Unknown schema: {schema_name}"
    
    try:
        jsonschema.validate(instance=data, schema=schema)
        return True, ""
    except jsonschema.ValidationError as e:
        return False, str(e)


if __name__ == "__main__":
    import json
    # Print all schemas in readable format
    for name, schema in SCHEMAS.items():
        print(f"\n{'='*60}")
        print(f"Schema: {name.upper()}")
        print('='*60)
        print(json.dumps(schema, indent=2, ensure_ascii=False))
