"""
Enhanced Data Loader for Step 1 (Catalog Builder) Integration
Supports hybrid search: embedding-based (semantic) + keyword-based (fallback)

Architecture:
- Loads Part 1 data: outfit_descriptions.json + outfit_embeddings.npy
- Supports flexible embedding models with auto-detection
- Provides hybrid search with fallback mechanisms
"""

import json
import os
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path

try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False


class CatalogLoaderV2:
    """
    Enhanced catalog loader supporting Part 1 integration with hybrid search.
    
    Features:
    - Load outfit_descriptions.json (metadata)
    - Load outfit_embeddings.npy (semantic vectors)
    - Hybrid search: embedding-based + keyword fallback
    - Auto-detect compatible embedding models
    """
    
    def __init__(
        self,
        descriptions_path: str = "src/outfit_descriptions.json",
        embeddings_path: Optional[str] = None,
        model_name: str = "all-MiniLM-L6-v2",
        auto_detect_model: bool = True
    ):
        """
        Initialize the catalog loader.
        
        Args:
            descriptions_path: Path to outfit_descriptions.json from Part 1
            embeddings_path: Path to outfit_embeddings.npy from Part 1
            model_name: Sentence transformer model for encoding queries
            auto_detect_model: If True, try to auto-detect compatible model
        """
        self.descriptions_path = descriptions_path
        self.embeddings_path = embeddings_path
        self.model_name = model_name
        self.auto_detect_model = auto_detect_model
        
        # Load catalog metadata
        self.catalog = self._load_descriptions()
        self.catalog_size = len(self.catalog)
        
        # Load embeddings and model
        self.embeddings = None
        self.embedding_model = None
        self._load_embeddings_and_model()
    
    def _load_descriptions(self) -> Dict[str, Dict[str, Any]]:
        """Load outfit_descriptions.json from Part 1."""
        if not os.path.exists(self.descriptions_path):
            raise FileNotFoundError(f"Descriptions not found: {self.descriptions_path}")
        
        with open(self.descriptions_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # If data is a list, convert to dict keyed by filename/item_id
        if isinstance(data, list):
            return {f"outfit_{i}": item for i, item in enumerate(data)}
        return data
    
    def _load_embeddings_and_model(self):
        """Load embeddings and try to initialize compatible model."""
        if not self.embeddings_path or not os.path.exists(self.embeddings_path):
            print(f"Info: Embeddings file not found. Using keyword-only search.")
            return
        
        try:
            self.embeddings = np.load(self.embeddings_path)
            print(f"Info: Loaded embeddings shape {self.embeddings.shape}")
        except Exception as e:
            print(f"Warning: Failed to load embeddings: {e}")
            return
        
        if not HAS_SENTENCE_TRANSFORMERS:
            print("Warning: sentence-transformers not installed. Using keyword-only search.")
            return
        
        # Try to load the specified model and check compatibility
        self._try_load_model(self.model_name)
        
        # If failed and auto-detect enabled, try candidate models
        if self.embedding_model is None and self.auto_detect_model:
            self._auto_detect_model()
    
    def _try_load_model(self, model_name: str) -> bool:
        """Try to load a model and verify embedding dimension compatibility."""
        try:
            model = SentenceTransformer(model_name)
            sample_emb = model.encode(["test"], convert_to_numpy=True)
            model_dim = sample_emb.shape[1]
            embeddings_dim = self.embeddings.shape[1]
            
            if model_dim == embeddings_dim:
                self.embedding_model = model
                self.model_name = model_name
                print(f"Info: Loaded model '{model_name}' (dim={model_dim})")
                return True
            else:
                print(f"Warning: Model dimension mismatch: model={model_dim}, embeddings={embeddings_dim}")
                return False
        except Exception as e:
            print(f"Warning: Failed to load model '{model_name}': {e}")
            return False
    
    def _auto_detect_model(self):
        """Try to auto-detect a compatible model from common options."""
        candidates = [
            'distiluse-base-multilingual-cased-v2',  # 512-dim
            'sentence-transformers/distiluse-base-multilingual-cased-v2',
            'paraphrase-multilingual-MiniLM-L12-v2',  # 384-dim
            'paraphrase-xlm-r-multilingual-v1',  # 768-dim
            'all-mpnet-base-v2',  # 768-dim
        ]
        
        embeddings_dim = self.embeddings.shape[1]
        print(f"Info: Auto-detecting compatible model for {embeddings_dim}-dim embeddings...")
        
        for model_name in candidates:
            if self._try_load_model(model_name):
                return
        
        print(f"Info: No compatible model auto-detected. Using keyword-only search.")
    
    def search_by_text(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.3
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Search catalog using hybrid approach: embedding-based + keyword fallback.
        
        Args:
            query: Text query (e.g., "light blue breathable summer dress")
            top_k: Number of results to return
            threshold: Minimum similarity score for embedding search
        
        Returns:
            List of (item_metadata, similarity_score) tuples
        """
        if self.embedding_model is not None and self.embeddings is not None:
            return self._search_by_embedding(query, top_k, threshold)
        else:
            return self._search_by_keyword(query, top_k)
    
    def _search_by_embedding(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.3
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Semantic search using embeddings."""
        # Encode query
        query_emb = self.embedding_model.encode([query], convert_to_numpy=True)
        query_emb = query_emb / (np.linalg.norm(query_emb, axis=1, keepdims=True) + 1e-10)
        
        # Normalize embeddings for cosine similarity
        embeddings_norm = self.embeddings / (np.linalg.norm(self.embeddings, axis=1, keepdims=True) + 1e-10)
        
        # Compute similarities
        similarities = np.dot(embeddings_norm, query_emb.T).flatten()
        
        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        catalog_items = list(self.catalog.items())
        for idx in top_indices:
            score = float(similarities[idx])
            if score >= threshold:
                item_key, item_meta = catalog_items[int(idx)]
                results.append((item_meta, score))
        
        return results
    
    def _search_by_keyword(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Keyword-based fallback search."""
        keywords = query.lower().split()
        results = []
        
        for item_key, item_meta in self.catalog.items():
            score = 0
            text_to_search = (
                str(item_meta.get("complete_description", "")).lower() + " " +
                str(item_meta.get("color_primary", "")).lower() + " " +
                str(item_meta.get("material", "")).lower() + " " +
                str(item_meta.get("style_aesthetic", "")).lower()
            )
            
            for keyword in keywords:
                if keyword in text_to_search:
                    score += 1
            
            if score > 0:
                normalized_score = min(score / len(keywords), 1.0) if keywords else 0.0
                results.append((item_meta, normalized_score))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
    
    def search_by_attributes(
        self,
        color: Optional[str] = None,
        material: Optional[str] = None,
        category: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Exact attribute matching."""
        results = []
        
        for item_key, item_meta in self.catalog.items():
            match = True
            
            if color and str(item_meta.get("color_primary", "")).lower() != color.lower():
                match = False
            if material and str(item_meta.get("material", "")).lower() != material.lower():
                match = False
            if category and str(item_meta.get("category", "")).lower() != category.lower():
                match = False
            
            if match:
                results.append(item_meta)
        
        return results[:top_k]
    
    def get_by_id(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Get single item by ID."""
        return self.catalog.get(item_id)
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Get all items in catalog."""
        return list(self.catalog.values())
    
    def get_stats(self) -> Dict[str, Any]:
        """Get catalog statistics."""
        colors = set()
        materials = set()
        styles = set()
        categories = set()
        
        for item in self.catalog.values():
            if item.get("color_primary"):
                colors.add(item.get("color_primary"))
            if item.get("material"):
                materials.add(item.get("material"))
            if item.get("style_aesthetic"):
                styles.add(item.get("style_aesthetic"))
            if item.get("category"):
                categories.add(item.get("category"))
        
        return {
            "total_items": self.catalog_size,
            "unique_colors": len(colors),
            "unique_materials": len(materials),
            "unique_styles": len(styles),
            "unique_categories": len(categories),
            "has_embeddings": self.embedding_model is not None and self.embeddings is not None,
            "embedding_model": self.model_name if self.embedding_model else None,
            "embedding_dim": self.embeddings.shape[1] if self.embeddings is not None else None,
        }


# Backward compatibility alias
CatalogLoader = CatalogLoaderV2


if __name__ == "__main__":
    # Quick test
    loader = CatalogLoaderV2(
        descriptions_path="src/outfit_descriptions.json",
        embeddings_path="src/outfit_embeddings.npy"
    )
    print(f"Loaded catalog with {loader.catalog_size} items")
    print(f"Stats: {loader.get_stats()}")
    
    results = loader.search_by_text("light blue chiffon dress for beach wedding", top_k=5)
    print(f"\nSearch results for 'light blue chiffon dress':")
    for item, score in results:
        print(f"  - {item.get('complete_description', 'N/A')[:80]} (score={score:.4f})")
