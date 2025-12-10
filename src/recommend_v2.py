"""
Enhanced Recommendation Engine (Part 3 Core Logic)
Implements Retrieve-Think-Generate chain for outfit recommendations.

Architecture:
1. RETRIEVE: Search catalog using hybrid search
2. THINK: Reason about candidates based on user context, weather, personal color
3. GENERATE: Create recommendation with VTON prompt for Part 4

Output format optimized for Part 4 (Virtual Try-On Presenter)
"""

import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

from src.data_loader_v2 import CatalogLoaderV2
from src.mock_context_v2 import select_context, validate_context


@dataclass
class RecommendationOutput:
    """Output schema for Part 4 (Virtual Try-On Presenter)."""
    task_id: str
    selected_outfit: Dict[str, Any]  # filename, category, description
    reasoning_log: str  # Why this outfit was chosen (Traditional Chinese)
    vton_generation_prompt: str  # For Stable Diffusion / image generation
    alternative_candidates: List[Dict[str, Any]] = None  # Top 3 alternatives
    confidence_score: float = 0.0
    generated_at: str = ""
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class OutfitRecommenderV2:
    """
    Enhanced outfit recommender with Retrieve-Think-Generate chain.
    
    Integrates Part 1 (Catalog) → Part 3 (Logic) → Part 4 (VTON)
    """
    
    def __init__(
        self,
        descriptions_path: str = "src/outfit_descriptions.json",
        embeddings_path: str = "src/outfit_embeddings.npy",
        model_name: str = "all-MiniLM-L6-v2",
        auto_detect_model: bool = True
    ):
        """
        Initialize the recommender.
        
        Args:
            descriptions_path: Path to outfit_descriptions.json (Part 1)
            embeddings_path: Path to outfit_embeddings.npy (Part 1)
            model_name: Embedding model name
            auto_detect_model: Allow auto-detection of compatible model
        """
        self.catalog_loader = CatalogLoaderV2(
            descriptions_path=descriptions_path,
            embeddings_path=embeddings_path,
            model_name=model_name,
            auto_detect_model=auto_detect_model
        )
    
    def recommend(
        self,
        context: Optional[Dict[str, Any]] = None,
        scenario: str = "beach_wedding",
        top_k: int = 5
    ) -> RecommendationOutput:
        """
        Generate outfit recommendation using Retrieve-Think-Generate chain.
        
        Args:
            context: User context from Part 2 (or None to use mock)
            scenario: Scenario name if context is None
            top_k: Number of candidates to retrieve
        
        Returns:
            RecommendationOutput for Part 4
        """
        # 1. RETRIEVE: Load context
        if context is None:
            context = select_context(scenario)
        
        if not validate_context(context):
            raise ValueError("Invalid context: missing required fields")
        
        # 2. RETRIEVE: Get candidate outfits via hybrid search
        candidates = self._retrieve_candidates(context, top_k)

        # Hard metadata filtering before thinking/LLM
        try:
            candidates = self.catalog_loader.filter_metadata(context, candidates)
        except Exception:
            # If filtering fails for any reason, continue with original candidates
            pass
        
        if not candidates:
            return self._create_empty_output(context)
        
        # 3. THINK: Score and select best outfit
        selected_item, score = self._think_and_select(context, candidates)

        # 3.5 COMPOSITION: if the selected item is a Top/Upper, try to find a Bottom to form a full outfit
        composed_pair = None
        selected_category = (selected_item.get("category", "") or "").lower()
        if selected_category in ["upper", "top", "topwear"]:
            bottom = self._find_matching_bottom(selected_item, context)
            if bottom:
                composed_pair = {
                    "top": selected_item,
                    "bottom": bottom
                }
        
        # 4. GENERATE: Create reasoning and VTON prompt
        # If composed_pair exists, generate combined reasoning and prompt
        if composed_pair:
            reasoning = self._generate_reasoning(context, composed_pair["top"]) + (
                "\n搭配建議：" + composed_pair["bottom"].get("complete_description", "")
            )
            vton_prompt = self._generate_vton_prompt_for_pair(context, composed_pair["top"], composed_pair["bottom"])
        else:
            reasoning = self._generate_reasoning(context, selected_item)
            vton_prompt = self._generate_vton_prompt(context, selected_item)
        
        # 5. Package output for Part 4
        # Build selected_outfit dict - support both single items and composed pairs
        if composed_pair:
            selected_outfit_dict = {
                "filename": f"{self._extract_filename(composed_pair['top'])} + {self._extract_filename(composed_pair['bottom'])}",
                "category": f"{selected_item.get('category', '')} + {composed_pair['bottom'].get('category', '')}",
                "color": f"{selected_item.get('color_primary', '')} / {composed_pair['bottom'].get('color_primary', '')}",
                "material": f"{selected_item.get('material', '')} + {composed_pair['bottom'].get('material', '')}",
                "description": selected_item.get("complete_description", ""),
                "components": {
                    "top": {
                        "filename": self._extract_filename(selected_item),
                        "category": selected_item.get("category", ""),
                        "color": selected_item.get("color_primary", ""),
                        "material": selected_item.get("material", ""),
                        "description": selected_item.get("complete_description", "")
                    },
                    "bottom": {
                        "filename": self._extract_filename(composed_pair["bottom"]),
                        "category": composed_pair["bottom"].get("category", ""),
                        "color": composed_pair["bottom"].get("color_primary", ""),
                        "material": composed_pair["bottom"].get("material", ""),
                        "description": composed_pair["bottom"].get("complete_description", "")
                    }
                }
            }
        else:
            selected_outfit_dict = {
                "filename": self._extract_filename(selected_item),
                "category": selected_item.get("category", ""),
                "color": selected_item.get("color_primary", ""),
                "material": selected_item.get("material", ""),
                "description": selected_item.get("complete_description", "")
            }
        
        output = RecommendationOutput(
            task_id=f"recommendation_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            selected_outfit=selected_outfit_dict,
            reasoning_log=reasoning,
            vton_generation_prompt=vton_prompt,
            alternative_candidates=[
                {
                    "filename": self._extract_filename(c),
                    "category": c.get("category", ""),
                    "description": c.get("complete_description", "")[:100]
                }
                for c in [item for item, _ in candidates[1:4]]
            ],
            confidence_score=float(score),
            generated_at=datetime.now().isoformat()
        )
        
        return output
    
    def _retrieve_candidates(
        self,
        context: Dict[str, Any],
        top_k: int = 5
    ) -> List[tuple]:
        """
        RETRIEVE Phase: Search catalog for candidate outfits.
        
        Args:
            context: User context
            top_k: Number of candidates
        
        Returns:
            List of (item_metadata, similarity_score) tuples
        """
        # Build comprehensive search query from context
        query_parts = []
        
        # User's natural query
        if "user_query" in context:
            query_parts.append(context["user_query"])
        
        # Weather-based keywords
        weather = context.get("weather", {})
        temp = weather.get("temperature_c", 20)
        condition = weather.get("condition", "")
        
        if temp > 28:
            query_parts.append("lightweight breathable cool")
        elif temp < 15:
            query_parts.append("warm cozy insulated")
        
        if "sunny" in condition.lower():
            query_parts.append("light color sun-protective")
        elif "rain" in condition.lower():
            query_parts.append("waterproof durable")
        
        # Style preferences
        user_profile = context.get("user_profile", {})
        if "style_preferences" in user_profile:
            query_parts.extend(user_profile["style_preferences"])
        
        # Color preferences
        if "color_preferences" in user_profile:
            query_parts.extend(user_profile["color_preferences"])
        
        # Personal color
        if "personal_color" in user_profile:
            query_parts.append(user_profile["personal_color"])
        
        # Occasion
        occasion = context.get("occasion", {})
        if "type" in occasion:
            query_parts.append(occasion["type"])
        
        search_query = " ".join(query_parts)
        
        # Search using hybrid search
        candidates = self.catalog_loader.search_by_text(
            query=search_query,
            top_k=top_k,
            threshold=0.0  # Lower threshold to get more candidates for thinking
        )
        
        return candidates
    
    def _think_and_select(
        self,
        context: Dict[str, Any],
        candidates: List[tuple]
    ) -> tuple:
        """
        THINK Phase: Evaluate candidates and select the best one.
        
        Scoring: retrieval_score + color_match + style_match + material_fit
        
        Args:
            context: User context
            candidates: Retrieved candidates
        
        Returns:
            (best_item, best_score)
        """
        best_item = None
        best_score = -1
        
        user_profile = context.get("user_profile", {})
        weather = context.get("weather", {})
        
        for item, retrieval_score in candidates:
            score = retrieval_score
            
            # Boost for color match
            color_prefs = user_profile.get("color_preferences", [])
            item_color = item.get("color_primary", "")
            if item_color.lower() in [c.lower() for c in color_prefs]:
                score += 0.25
            
            # Boost for style match
            style_prefs = user_profile.get("style_preferences", [])
            item_style = item.get("style_aesthetic", "")
            if item_style.lower() in [s.lower() for s in style_prefs]:
                score += 0.25
            
            # Boost for material fit (breathability in hot weather)
            temp = weather.get("temperature_c", 20)
            material = item.get("material", "").lower()
            if temp > 28 and any(m in material for m in ["cotton", "linen", "silk", "chiffon"]):
                score += 0.2
            
            if score > best_score:
                best_score = score
                best_item = item
        
        return best_item, min(best_score, 1.0)
    
    def _generate_reasoning(
        self,
        context: Dict[str, Any],
        selected_item: Dict[str, Any]
    ) -> str:
        """
        GENERATE Phase: Create reasoning explanation.
        
        Args:
            context: User context
            selected_item: Selected outfit item
        
        Returns:
            Reasoning string in Traditional Chinese
        """
        reasons = []
        
        user_profile = context.get("user_profile", {})
        weather = context.get("weather", {})
        occasion = context.get("occasion", {})
        
        # Color reasoning
        personal_color = user_profile.get("personal_color", "")
        item_color = selected_item.get("color_primary", "")
        if item_color:
            reasons.append(f"色調'{item_color}'完美詮釋您的{personal_color}色彩季型")
        
        # Material & weather reasoning
        material = selected_item.get("material", "")
        temp = weather.get("temperature_c", 20)
        if material:
            if temp > 28:
                reasons.append(f"{material}材質透氣輕盈，適合{temp}°C高溫環境")
            else:
                reasons.append(f"{material}材質舒適耐穿，適合{weather.get('condition', '當前')}天氣")
        
        # Style reasoning
        style_pref = user_profile.get("style_preferences", [])
        item_style = selected_item.get("style_aesthetic", "")
        if item_style and style_pref:
            reasons.append(f"風格'{item_style}'展現您喜愛的{style_pref[0]}特質")
        
        # Occasion reasoning
        occasion_type = occasion.get("type", "")
        if occasion_type:
            reasons.append(f"整體造型適合{occasion_type}的場合，展現得體優雅")
        
        return "。".join(reasons) + "。" if reasons else "這件衣服非常適合您的當前場合。"
    
    def _generate_vton_prompt(
        self,
        context: Dict[str, Any],
        selected_item: Dict[str, Any]
    ) -> str:
        """
        GENERATE Phase: Create Stable Diffusion prompt for virtual try-on.
        
        Format: Model wearing [outfit details], [environment lighting], [quality]
        
        Args:
            context: User context
            selected_item: Selected outfit item
        
        Returns:
            VTON prompt for Part 4
        """
        weather = context.get("weather", {})
        occasion = context.get("occasion", {})
        
        # Outfit description
        color = selected_item.get("color_primary", "neutral")
        material = selected_item.get("material", "fabric")
        style = selected_item.get("style_aesthetic", "elegant")
        category = selected_item.get("category", "outfit")
        description = selected_item.get("complete_description", f"{style} {color} {category}")
        
        # Environment based on weather
        condition = weather.get("condition", "natural").lower()
        location = occasion.get("location", "indoor")
        
        # Lighting keywords based on weather
        if "sunny" in condition:
            lighting = "golden hour lighting, sunny day, warm natural light"
        elif "cloudy" in condition:
            lighting = "soft diffused lighting, overcast day, gentle daylight"
        elif "rain" in condition:
            lighting = "cool ambient lighting, rainy atmosphere, moody lighting"
        else:
            lighting = "professional studio lighting, warm natural light"
        
        # Construct prompt for Stable Diffusion
        prompt = (
            f"A photorealistic image of an elegant woman wearing a {color} {material} {description}. "
            f"She is standing gracefully in a {location}, "
            f"{style.lower()} style, {lighting}, "
            f"professional photography, cinematic composition, "
            f"ultra high quality, 8k resolution, detailed fabric texture, natural skin texture, "
            f"intricate details, perfect lighting, masterpiece"
        )
        
        return prompt
    
    def _extract_filename(self, item: Dict[str, Any]) -> str:
        """Extract or derive filename from item."""
        # Try common filename fields
        for key in ["filename", "image_url", "image_path"]:
            if key in item:
                return item[key]
        
        # Fallback: use item_id or create from index
        if "item_id" in item:
            return f"{item['item_id']}.jpg"
        
        return "outfit.jpg"

    def _find_matching_bottom(self, top_item: Dict[str, Any], context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find a matching bottom (Lower) for the given top_item using catalog attributes.

        Heuristics:
        - Try to find Bottom with same color or complementary neutral
        - Prefer same style_aesthetic
        - Use search_by_attributes to filter by category='Lower' and color
        """
        top_color = (top_item.get("color_primary", "") or "").lower()
        top_style = (top_item.get("style_aesthetic", "") or "").lower()

        # First try exact color match
        candidates = self.catalog_loader.search_by_attributes(color=top_color, category="Lower", top_k=5)
        if candidates:
            # Prefer same style
            for c in candidates:
                if (c.get("style_aesthetic", "") or "").lower() == top_style:
                    return c
            return candidates[0]

        # If no exact color match, try any Lower and pick one by style or neutral color
        all_lowers = self.catalog_loader.search_by_attributes(category="Lower", top_k=10)
        if not all_lowers:
            return None

        # Prefer same style
        for c in all_lowers:
            if (c.get("style_aesthetic", "") or "").lower() == top_style:
                return c

        # Fallback: pick first neutral colored bottom (black/navy/white/gray)
        neutrals = ["black", "navy", "white", "gray", "grey", "beige"]
        for c in all_lowers:
            color = (c.get("color_primary", "") or "").lower()
            if any(n in color for n in neutrals):
                return c

        # Last resort: return first lower
        return all_lowers[0]


    def _generate_vton_prompt_for_pair(self, context: Dict[str, Any], top: Dict[str, Any], bottom: Dict[str, Any]) -> str:
        """Generate a Stable Diffusion prompt for a composed outfit (top + bottom)."""
        weather = context.get("weather", {})
        occasion = context.get("occasion", {})

        # Outfit description
        top_desc = top.get("complete_description", "top")
        bottom_desc = bottom.get("complete_description", "bottom")
        color_top = top.get("color_primary", "neutral")
        color_bottom = bottom.get("color_primary", "neutral")
        material_top = top.get("material", "fabric")
        material_bottom = bottom.get("material", "fabric")
        style = top.get("style_aesthetic", bottom.get("style_aesthetic", "elegant"))

        # Environment and lighting
        condition = weather.get("condition", "natural").lower()
        location = occasion.get("location", "indoor")
        if "sunny" in condition:
            lighting = "golden hour lighting, sunny day, warm natural light"
        elif "cloudy" in condition:
            lighting = "soft diffused lighting, overcast day, gentle daylight"
        elif "rain" in condition:
            lighting = "cool ambient lighting, rainy atmosphere, moody lighting"
        else:
            lighting = "professional studio lighting, warm natural light"

        prompt = (
            f"A photorealistic image of an elegant woman wearing a {color_top} {material_top} {top_desc} "
            f"paired with a {color_bottom} {material_bottom} {bottom_desc}. "
            f"She is posed naturally in a {location}, {style} style, {lighting}, "
            f"professional photography, cinematic composition, ultra high quality, 8k resolution, detailed fabric texture, natural skin texture, masterpiece"
        )

        return prompt
    
    def _create_empty_output(self, context: Dict[str, Any]) -> RecommendationOutput:
        """Create a fallback output when no candidates found."""
        return RecommendationOutput(
            task_id=f"recommendation_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            selected_outfit={
                "filename": "default.jpg",
                "category": "Dress",
                "description": "A versatile outfit suitable for various occasions"
            },
            reasoning_log="No suitable matches found in the current catalog. Recommending a versatile option.",
            vton_generation_prompt="A photorealistic image of an elegant woman wearing a sophisticated outfit.",
            confidence_score=0.0,
            generated_at=datetime.now().isoformat()
        )


if __name__ == "__main__":
    # Quick test: Retrieve-Think-Generate chain
    print("=" * 80)
    print("OUTFIT RECOMMENDER V2 - RETRIEVE-THINK-GENERATE CHAIN TEST")
    print("=" * 80)
    
    try:
        # Initialize recommender
        recommender = OutfitRecommenderV2(
            descriptions_path="src/outfit_descriptions.json",
            embeddings_path="src/outfit_embeddings.npy"
        )
        
        # Test with beach wedding scenario
        print("\n[SCENARIO] Beach Wedding")
        output = recommender.recommend(scenario="beach_wedding")
        
        print(f"\n[TASK ID] {output.task_id}")
        print(f"\n[SELECTED OUTFIT] {output.selected_outfit['filename']}")
        print(f"  Category: {output.selected_outfit['category']}")
        print(f"  Color: {output.selected_outfit['color']}")
        print(f"  Material: {output.selected_outfit['material']}")
        
        print(f"\n[REASONING]\n  {output.reasoning_log}")
        
        print(f"\n[VTON PROMPT]\n  {output.vton_generation_prompt}")
        
        print(f"\n[CONFIDENCE] {output.confidence_score:.2%}")
        
        print(f"\n[ALTERNATIVES]")
        for i, alt in enumerate(output.alternative_candidates or [], 1):
            print(f"  {i}. {alt['filename']} ({alt['category']})")
        
        print(f"\n[OUTPUT JSON]\n{output.to_json()}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
