"""
Data loader and converter for Step 1 (Catalog Builder) output.
Expects outfit_descriptions.json from the Catalog Builder.

Provides:
1. Catalog loading from Step 1 output (outfit_descriptions.json)
2. Embedding-based semantic search (using outfit_embeddings.npy)
3. Text-based hybrid search combining embeddings with keyword matching
"""

import json
import os
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path

try:
    from sentence_transformers import SentenceTransformer
    HAS_EMBEDDINGS = True
except ImportError:
    HAS_EMBEDDINGS = False


def load_catalog_from_step1(json_path: str) -> List[Dict[str, Any]]:
    """
    Load outfit catalog from Step 1 output (outfit_descriptions.json).
    
    Args:
        json_path: Path to outfit_descriptions.json from Step 1
    
    Returns:
        List of outfit items with standardized fields for Step 3
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        step1_data = json.load(f)
    
    items = []
    for idx, outfit in enumerate(step1_data):
        # Map Step 1 fields to our standardized schema
        item = {
            "item_id": f"outfit_{idx}",
            "category": outfit.get("category", ""),  # Upper, Lower, Dress, Set
            "subcategory": outfit.get("subcategory", ""),
            "title": outfit.get("complete_description", outfit.get("subcategory", f"Outfit {idx}")),
            "role": _map_category_to_role(outfit.get("category", "")),
            "color": outfit.get("color_primary", ""),
            "color_secondary": outfit.get("color_secondary", ""),
            "colors": [outfit.get("color_primary", "")] + 
                     ([outfit.get("color_secondary", "")] if outfit.get("color_secondary") else []),
            "pattern": outfit.get("pattern", ""),
            "material": outfit.get("material", ""),
            "style": outfit.get("style_aesthetic", ""),
            "fit": outfit.get("fit_silhouette", ""),
            "sleeve_length": outfit.get("sleeve_length", ""),
            "length": outfit.get("length", ""),
            "description": outfit.get("complete_description", ""),
            "raw_metadata": outfit,  # Keep original for reference
        }
        items.append(item)
    
    return items


def _map_category_to_role(category: str) -> str:
    """Map Step 1 category to our role field."""
    category_lower = category.lower()
    if "upper" in category_lower:
        return "top"
    elif "lower" in category_lower:
        return "bottom"
    elif "dress" in category_lower:
        return "dress"
    elif "set" in category_lower:
        return "set"
    else:
        return "other"


def convert_to_standard_format(step1_catalog: List[Dict]) -> List[Dict]:
    """
    Convert Step 1 items to standard format for recommender.
    
    Args:
        step1_catalog: Output from load_catalog_from_step1()
    
    Returns:
        Items in standardized schema format
    """
    standardized = []
    for item in step1_catalog:
        std_item = {
            "item_id": item["item_id"],
            "title": item["title"],
            "role": item["role"],
            "color": item["color"],
            "colors": item["colors"],
            "style": item["style"],
            "material": item["material"],
            "pattern": item["pattern"],
            "fit": item["fit"],
            "description": item["description"],
            "category": item["category"],
            "subcategory": item["subcategory"],
            "sleeve_length": item.get("sleeve_length", ""),
            "length": item.get("length", ""),
            "available": True,
            "popularity": 0.5,  # Default; can be updated based on usage
            "image_url": "",  # To be filled with actual image URLs
        }
        standardized.append(std_item)
    
    return standardized


def save_standardized_catalog(items: List[Dict], output_path: str):
    """Save standardized catalog to JSON."""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


class CatalogLoader:
    """
    Catalog loader with support for embedding-based semantic search.
    
    This class encapsulates both the outfit catalog (JSON) and embeddings (NPY).
    Provides hybrid search combining text similarity with keyword matching.
    """
    
    def __init__(
        self,
        catalog_path: str = "items.json",
        embeddings_path: Optional[str] = None,
        model_name: str = "all-MiniLM-L6-v2"
    ):
        """
        Initialize the catalog loader.
        
        Args:
            catalog_path: Path to JSON file with outfit descriptions
            embeddings_path: Path to NPY file with precomputed embeddings
            model_name: Sentence transformer model to use for query embeddings
        """
        self.catalog_path = catalog_path
        self.embeddings_path = embeddings_path
        self.model_name = model_name
        
        # Load catalog
        self.catalog = self._load_catalog()
        self.catalog_size = len(self.catalog)
        
        # Load embeddings if available. If model and embeddings dimensions
        # mismatch, disable the embedding_model and fallback to keyword search.
        self.embeddings = None
        self.embedding_model = None
        if embeddings_path and os.path.exists(embeddings_path) and HAS_EMBEDDINGS:
            try:
                self.embeddings = np.load(embeddings_path)
            except Exception:
                self.embeddings = None

            if self.embeddings is not None:
                try:
                    # Try to load the embedding model and verify vector dimension
                    model = SentenceTransformer(model_name)
                    sample_emb = model.encode(["__test__"], convert_to_numpy=True)
                    model_dim = int(sample_emb.shape[1])
                    emb_dim = int(self.embeddings.shape[1]) if len(self.embeddings.shape) > 1 else 0
                    if model_dim == emb_dim:
                        self.embedding_model = model
                    else:
                        print(
                            f"Warning: embedding dimension mismatch: embeddings={emb_dim}, model={model_dim}."
                            " Disabling embedding model and using keyword fallback."
                        )
                        self.embedding_model = None
                except Exception as e:
                    # If model loading or encoding fails, fall back to keyword search
                    print(f"Warning: failed to initialize embedding model '{model_name}': {e}. Using keyword fallback.")
                    self.embedding_model = None

                # If embeddings loaded but model didn't match, attempt to auto-detect a compatible model
                if self.embedding_model is None:
                    # Candidate models to try (ordered by likelihood)
                    candidate_models = [
                        'distiluse-base-multilingual-cased-v2',
                        'sentence-transformers/distiluse-base-multilingual-cased-v2',
                        'paraphrase-multilingual-MiniLM-L12-v2',
                        'paraphrase-xlm-r-multilingual-v1',
                        'all-MiniLM-L6-v2',
                        'all-mpnet-base-v2'
                    ]
                    emb_dim = int(self.embeddings.shape[1])
                    for cand in candidate_models:
                        try:
                            cand_model = SentenceTransformer(cand)
                            cand_emb = cand_model.encode(["__test__"], convert_to_numpy=True)
                            cand_dim = int(cand_emb.shape[1])
                            if cand_dim == emb_dim:
                                self.embedding_model = cand_model
                                self.model_name = cand
                                print(f"Info: auto-detected compatible embedding model: {cand} (dim={cand_dim})")
                                break
                        except Exception:
                            continue
                    if self.embedding_model is None:
                        print(f"Info: no compatible embedding model auto-detected for embedding dim={emb_dim}. Using keyword fallback.")
    
    def _load_catalog(self) -> List[Dict]:
        """Load catalog from JSON file."""
        if os.path.exists(self.catalog_path):
            with open(self.catalog_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            raise FileNotFoundError(f"Catalog not found: {self.catalog_path}")
    
    def get_by_id(self, item_id: str) -> Optional[Dict]:
        """Get a single item by ID."""
        for item in self.catalog:
            if item.get("item_id") == item_id:
                return item
        return None
    
    def search_by_text(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.3
    ) -> List[Tuple[Dict, float]]:
        """
        Search catalog by text query using semantic similarity.
        
        Args:
            query: Text query (e.g., "light blue breathable summer dress")
            top_k: Number of results to return
            threshold: Minimum similarity score (0-1)
        
        Returns:
            List of (item, similarity_score) tuples, sorted by similarity descending
        """
        if not HAS_EMBEDDINGS or self.embeddings is None or self.embedding_model is None:
            # Fallback: keyword-based search
            return self._search_by_keyword(query, top_k)
        
        # Embed the query
        query_embedding = self.embedding_model.encode([query], convert_to_numpy=True)
        query_embedding = query_embedding.astype(np.float32)
        query_embedding = query_embedding / (np.linalg.norm(query_embedding) + 1e-10)
        
        # Normalize catalog embeddings
        catalog_embeddings = self.embeddings.astype(np.float32)
        for i in range(catalog_embeddings.shape[0]):
            catalog_embeddings[i] = catalog_embeddings[i] / (np.linalg.norm(catalog_embeddings[i]) + 1e-10)
        
        # Compute cosine similarities
        similarities = np.dot(catalog_embeddings, query_embedding.T).flatten()
        
        # Get top-k results
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            score = float(similarities[idx])
            if score >= threshold:
                item = self.catalog[int(idx)]
                results.append((item, score))
        
        return results
    
    def _search_by_keyword(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Tuple[Dict, float]]:
        """
        Fallback keyword-based search (when embeddings unavailable).
        
        Args:
            query: Text query
            top_k: Number of results to return
        
        Returns:
            List of (item, keyword_match_score) tuples
        """
        keywords = query.lower().split()
        results = []
        
        for item in self.catalog:
            # Score based on keyword matches in title, description, color, material, style
            score = 0
            text_to_search = (
                item.get("title", "").lower() + " " +
                item.get("description", "").lower() + " " +
                item.get("color", "").lower() + " " +
                item.get("material", "").lower() + " " +
                item.get("style", "").lower()
            )
            
            for keyword in keywords:
                if keyword in text_to_search:
                    score += 1
            
            if score > 0:
                normalized_score = min(score / len(keywords), 1.0)
                results.append((item, normalized_score))
        
        # Sort by score descending and return top-k
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
    
    def search_by_attributes(
        self,
        color: Optional[str] = None,
        material: Optional[str] = None,
        style: Optional[str] = None,
        fit: Optional[str] = None,
        category: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict]:
        """
        Filter catalog by exact attribute matching.
        
        Args:
            color: Primary color to match
            material: Material to match
            style: Style aesthetic to match
            fit: Fit silhouette to match
            category: Category to match
            top_k: Maximum number of results
        
        Returns:
            List of matching items
        """
        results = []
        
        for item in self.catalog:
            match = True
            
            if color and item.get("color", "").lower() != color.lower():
                match = False
            if material and item.get("material", "").lower() != material.lower():
                match = False
            if style and item.get("style", "").lower() != style.lower():
                match = False
            if fit and item.get("fit", "").lower() != fit.lower():
                match = False
            if category and item.get("category", "").lower() != category.lower():
                match = False
            
            if match:
                results.append(item)
        
        return results[:top_k]
    
    def get_all(self) -> List[Dict]:
        """Get all items in catalog."""
        return self.catalog
    
    def get_stats(self) -> Dict[str, Any]:
        """Get catalog statistics."""
        colors = set()
        materials = set()
        styles = set()
        categories = set()
        
        for item in self.catalog:
            colors.add(item.get("color", ""))
            materials.add(item.get("material", ""))
            styles.add(item.get("style", ""))
            categories.add(item.get("category", ""))
        
        return {
            "total_items": self.catalog_size,
            "unique_colors": len(colors),
            "unique_materials": len(materials),
            "unique_styles": len(styles),
            "unique_categories": len(categories),
            "colors": list(colors),
            "materials": list(materials),
            "styles": list(styles),
            "categories": list(categories),
            # True only if embeddings loaded AND the model is compatible
            "has_embeddings": (self.embeddings is not None and self.embedding_model is not None),
        }


if __name__ == "__main__":
    # Example usage (when Step 1 data is available)
    try:
        catalog = load_catalog_from_step1("outfit_descriptions.json")
        standardized = convert_to_standard_format(catalog)
        save_standardized_catalog(standardized, "catalog_standardized.json")
        print(f"✓ Loaded {len(catalog)} outfits from Step 1")
        print(f"✓ Converted to {len(standardized)} standardized items")
    except FileNotFoundError:
        print("outfit_descriptions.json not found. Using synthetic data instead.")
