"""
Outfit Recommendation Interface - Complete Pipeline

This module implements the complete recommendation pipeline:
1. Input: User context from Person 2 (mock or real)
2. Process: Retrieve → Reason → Decide
3. Output: JSON for Person 4 (Virtual Try-On Presenter)

Architecture:
- Retrieval: Semantic search over outfit catalog
- Reasoning: LLM evaluates candidates against user context
- Decision: Select best outfit and generate VTON prompt
- Output: Standardized JSON with filename, reasoning, and VTON prompt
"""

import json
import os
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

try:
    from src.data_loader import CatalogLoader
    from src.mock_context import select_context
    from src.llm_chain import OutfitExplainer
    from src.prompts import get_complete_recommendation_prompt
    HAS_MODULES = True
except ImportError:
    HAS_MODULES = False


@dataclass
class RecommendationOutput:
    """
    Standard output format for Person 4 (Virtual Try-On Presenter)
    
    Attributes:
        selected_outfit_filename: Image filename of selected outfit (e.g., "12.jpg")
        selected_outfit_id: Unique ID from catalog
        reasoning: Natural language explanation in Traditional Chinese
        vton_prompt: Stable Diffusion prompt for image generation
        negative_prompt: What to avoid in image generation
        confidence_score: Recommendation confidence (0-1)
        fashion_notes: Additional styling insights
        generated_at: Timestamp of recommendation
    """
    selected_outfit_filename: str
    selected_outfit_id: str
    reasoning: str
    vton_prompt: str
    negative_prompt: str = ""
    confidence_score: float = 0.0
    fashion_notes: str = ""
    generated_at: str = ""
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class OutfitRecommender:
    """
    Complete outfit recommendation pipeline.
    
    Combines catalog search, LLM reasoning, and VTON prompt generation.
    """
    
    def __init__(
        self,
        catalog_path: str = "items.json",
        embeddings_path: Optional[str] = None,
        use_llm: bool = False
    ):
        """
        Initialize recommender.
        
        Args:
            catalog_path: Path to outfit catalog JSON
            embeddings_path: Path to embeddings NPY (optional)
            use_llm: Whether to use LLM for enhanced reasoning
        """
        self.catalog_loader = CatalogLoader(
            catalog_path=catalog_path,
            embeddings_path=embeddings_path
        )
        self.use_llm = use_llm
        self.explainer = None
        
        if use_llm:
            try:
                self.explainer = OutfitExplainer()
            except ValueError as e:
                print(f"Warning: Could not initialize LLM: {e}")
                self.use_llm = False
    
    def recommend(
        self,
        context: Optional[Dict[str, Any]] = None,
        scenario: str = "beach_wedding",
        top_k: int = 5
    ) -> RecommendationOutput:
        """
        Generate outfit recommendation for given context.
        
        Args:
            context: User context dict (if None, uses mock)
            scenario: Scenario name if context is None
            top_k: Number of candidates to retrieve
        
        Returns:
            RecommendationOutput with outfit selection and VTON prompt
        """
        # Step 1: Get context (from argument or mock)
        if context is None:
            context = select_context(scenario)
        
        # Step 2: Retrieve candidates via semantic search
        candidates = self._retrieve_candidates(context, top_k)
        
        if not candidates:
            return self._create_fallback_output(context)
        
        # Step 3: Evaluate and select best outfit
        selected_item, score = self._select_best_outfit(context, candidates)
        
        # Step 4: Generate reasoning
        reasoning = self._generate_reasoning(context, selected_item)
        
        # Step 5: Generate VTON prompt
        vton_prompt, negative_prompt = self._generate_vton_prompt(context, selected_item)
        
        # Step 6: Package output
        output = RecommendationOutput(
            selected_outfit_filename=self._extract_filename(selected_item),
            selected_outfit_id=selected_item.get("item_id", "unknown"),
            reasoning=reasoning,
            vton_prompt=vton_prompt,
            negative_prompt=negative_prompt,
            confidence_score=float(score),
            fashion_notes=self._generate_fashion_notes(context, selected_item),
            generated_at=datetime.now().isoformat()
        )
        
        return output
    
    def _retrieve_candidates(
        self,
        context: Dict[str, Any],
        top_k: int = 5
    ) -> List[Tuple[Dict, float]]:
        """
        Retrieve candidate outfits via semantic search.
        
        Args:
            context: User context
            top_k: Number of candidates to retrieve
        
        Returns:
            List of (item, score) tuples
        """
        # Build search query from context
        query_parts = []
        
        # Add user query
        if "user_query" in context:
            query_parts.append(context["user_query"])
        
        # Add weather keywords
        if "weather" in context:
            weather = context["weather"]
            temp = weather.get("temperature_c", 20)
            condition = weather.get("condition", "")
            if temp > 25:
                query_parts.append("breathable lightweight")
            elif temp < 15:
                query_parts.append("warm cozy")
            if "sunny" in condition.lower():
                query_parts.append("light color sun protection")
        
        # Add style preferences
        if "user_profile" in context:
            profile = context["user_profile"]
            if "style_preferences" in profile:
                query_parts.extend(profile["style_preferences"])
            if "color_preferences" in profile:
                query_parts.extend(profile["color_preferences"])
        
        # Combine into search query
        search_query = " ".join(query_parts)
        
        # Search catalog
        candidates = self.catalog_loader.search_by_text(
            query=search_query,
            top_k=top_k,
            threshold=0.2
        )
        
        return candidates
    
    def _select_best_outfit(
        self,
        context: Dict[str, Any],
        candidates: List[Tuple[Dict, float]]
    ) -> Tuple[Dict, float]:
        """
        Select the best outfit from candidates.
        
        Currently uses retrieval score + heuristic matching.
        With LLM enabled, uses LLM evaluation.
        
        Args:
            context: User context
            candidates: List of (item, score) tuples from retrieval
        
        Returns:
            (selected_item, final_score)
        """
        if not candidates:
            return {}, 0.0
        
        if self.use_llm and self.explainer:
            # TODO: LLM-based selection
            # For now, use retrieval score
            pass
        
        # Use retrieval score as selection criterion
        best_item, best_score = candidates[0]
        
        # Apply heuristic boosts based on exact matches
        for item, score in candidates:
            boosted_score = score
            
            # Boost for color preference match
            if "user_profile" in context:
                user_colors = context["user_profile"].get("color_preferences", [])
                if item.get("color") in user_colors:
                    boosted_score += 0.2
            
            # Boost for style match
            if "user_profile" in context:
                user_styles = context["user_profile"].get("style_preferences", [])
                if item.get("style") in user_styles:
                    boosted_score += 0.2
            
            if boosted_score > best_score:
                best_score = boosted_score
                best_item = item
        
        return best_item, min(best_score, 1.0)
    
    def _generate_reasoning(
        self,
        context: Dict[str, Any],
        selected_item: Dict
    ) -> str:
        """
        Generate natural language reasoning for the selection.
        
        Args:
            context: User context
            selected_item: Selected outfit item
        
        Returns:
            Reasoning string in Traditional Chinese
        """
        if self.use_llm and self.explainer:
            try:
                # Use LLM for reasoning
                prompt = get_complete_recommendation_prompt()
                formatted_prompt = prompt.format(
                    selected_outfit=json.dumps(selected_item, ensure_ascii=False),
                    occasion=context.get("occasion", {}).get("type", ""),
                    weather=context.get("weather", {}).get("condition", ""),
                    user_style=", ".join(context.get("user_profile", {}).get("style_preferences", [])),
                    personal_color=context.get("user_profile", {}).get("personal_color", "")
                )
                # This would call LLM, for now return heuristic
                return self._generate_heuristic_reasoning(context, selected_item)
            except Exception as e:
                print(f"LLM reasoning failed: {e}")
                return self._generate_heuristic_reasoning(context, selected_item)
        
        return self._generate_heuristic_reasoning(context, selected_item)
    
    def _generate_heuristic_reasoning(
        self,
        context: Dict[str, Any],
        selected_item: Dict
    ) -> str:
        """
        Generate reasoning using heuristic rules (no LLM).
        
        Args:
            context: User context
            selected_item: Selected outfit item
        
        Returns:
            Reasoning string
        """
        reasons = []
        
        # Color matching
        user_colors = context.get("user_profile", {}).get("color_preferences", [])
        if selected_item.get("color") in user_colors:
            reasons.append(f"色色符合您的偏好色系（{selected_item.get('color')}）")
        
        # Style matching
        user_styles = context.get("user_profile", {}).get("style_preferences", [])
        if selected_item.get("style") in user_styles:
            reasons.append(f"風格完美詮釋您偏愛的{selected_item.get('style')}風格")
        
        # Weather appropriateness
        weather = context.get("weather", {})
        temp = weather.get("temperature_c", 20)
        material = selected_item.get("material", "")
        if temp > 25 and material:
            reasons.append(f"採用{material}材質，透氣舒適，適合高溫天氣")
        
        # Occasion appropriateness
        occasion = context.get("occasion", {}).get("type", "")
        if occasion:
            reasons.append(f"服裝等級與場合相符（{occasion}）")
        
        if not reasons:
            reasons.append(f"這件{selected_item.get('title', '服裝')}優雅得體，適合您的風格")
        
        return "。".join(reasons) + "。"
    
    def _generate_vton_prompt(
        self,
        context: Dict[str, Any],
        selected_item: Dict
    ) -> Tuple[str, str]:
        """
        Generate Stable Diffusion prompt for virtual try-on.
        
        Args:
            context: User context
            selected_item: Selected outfit item
        
        Returns:
            (vton_prompt, negative_prompt)
        """
        # Build VTON prompt components
        color = selected_item.get("color", "neutral")
        material = selected_item.get("material", "fabric")
        style = selected_item.get("style", "elegant")
        fit = selected_item.get("fit", "fitted")
        title = selected_item.get("title", "outfit")
        
        # Occasion details
        occasion = context.get("occasion", {})
        location = occasion.get("location", "indoor")
        formality = occasion.get("formality", "casual")
        
        # Weather
        weather = context.get("weather", {})
        condition = weather.get("condition", "natural").lower()
        
        # Build prompt
        vton_prompt = (
            f"A photorealistic image of an elegant woman wearing a {color} {material} {title} "
            f"({fit} silhouette, {style} style), "
            f"standing gracefully on a {location}, "
            f"{condition} lighting, professional photography, cinematic, "
            f"ultra high quality, detailed facial features, natural skin, soft lighting"
        )
        
        negative_prompt = (
            "ugly, distorted, blurry, low quality, amateur, unfinished, "
            "oversaturated, poorly lit, wrong proportions, deformed"
        )
        
        return vton_prompt, negative_prompt
    
    def _generate_fashion_notes(
        self,
        context: Dict[str, Any],
        selected_item: Dict
    ) -> str:
        """
        Generate additional fashion insights.
        
        Args:
            context: User context
            selected_item: Selected outfit item
        
        Returns:
            Fashion notes string
        """
        notes = []
        
        # Personal color analysis
        personal_color = context.get("user_profile", {}).get("personal_color", "")
        if personal_color:
            notes.append(f"完美詮釋您的{personal_color}色彩季型")
        
        # Body type consideration
        body_type = context.get("user_profile", {}).get("body_type", "")
        fit = selected_item.get("fit", "")
        if body_type and fit:
            notes.append(f"{fit}剪裁修飾{body_type}身材")
        
        # Occasion appropriateness
        occasion = context.get("occasion", {}).get("type", "")
        formality = context.get("occasion", {}).get("formality", "")
        if occasion and formality:
            notes.append(f"得體展現{formality}場合的優雅氣質")
        
        if not notes:
            notes.append("展現個人品味與自信")
        
        return "。".join(notes) + "。"
    
    def _extract_filename(self, item: Dict) -> str:
        """Extract image filename from item (format: "12.jpg")."""
        item_id = item.get("item_id", "unknown")
        # Assume IDs are like "outfit_12" → "12.jpg"
        if "_" in item_id:
            num = item_id.split("_")[-1]
            return f"{num}.jpg"
        return f"{item_id}.jpg"
    
    def _create_fallback_output(self, context: Dict) -> RecommendationOutput:
        """Create fallback output when no candidates found."""
        return RecommendationOutput(
            selected_outfit_filename="fallback.jpg",
            selected_outfit_id="fallback",
            reasoning="無法根據您的偏好找到合適的服裝。請稍後重試或聯絡客服。",
            vton_prompt="A professional fashion model in neutral elegance, office lighting",
            negative_prompt="ugly, distorted",
            confidence_score=0.0,
            fashion_notes="推薦服務暫時不可用",
            generated_at=datetime.now().isoformat()
        )


def main_recommend(scenario: str = "beach_wedding", use_llm: bool = False) -> Dict:
    """
    Main entry point for outfit recommendation.
    
    Args:
        scenario: Scenario name (beach_wedding, office_meeting, default)
        use_llm: Whether to use LLM for enhanced reasoning
    
    Returns:
        Recommendation output as dictionary
    """
    try:
        recommender = OutfitRecommender(use_llm=use_llm)
        output = recommender.recommend(scenario=scenario)
        result = output.to_dict()
        return result
    except Exception as e:
        print(f"Recommendation failed: {e}")
        return {
            "error": str(e),
            "selected_outfit_filename": "error.jpg",
            "reasoning": "系統錯誤，無法生成推薦"
        }


if __name__ == "__main__":
    import sys
    scenario = sys.argv[1] if len(sys.argv) > 1 else "beach_wedding"
    use_llm = "--with-llm" in sys.argv
    
    print("=" * 60)
    print("Outfit Recommendation System")
    print("=" * 60)
    print(f"Scenario: {scenario}")
    print(f"Using LLM: {use_llm}")
    print("=" * 60)
    
    result = main_recommend(scenario, use_llm)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # Save to file
    output_path = "recommendation_output.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n✓ Output saved to {output_path}")
