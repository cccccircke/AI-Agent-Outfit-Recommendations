"""
Data loader for integrating with Step 1 (Catalog Builder) output.
Handles clothing metadata and embeddings from various sources.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Optional
import numpy as np


class ClothingDataLoader:
    """Load clothing data from Step 1 Catalog Builder output."""
    
    @staticmethod
    def load_from_embedding_output(
        embedding_dir: str,
        metadata_file: str = "metadata.json",
        embedding_file: str = "embeddings.npy"
    ) -> tuple[List[Dict], np.ndarray]:
        """
        Load clothing data from Step 1 output.
        
        Expected structure:
            embedding_dir/
            ├── metadata.json (list of items with: id, title, color, style, material, season, image_url, etc.)
            └── embeddings.npy (shape: [num_items, embedding_dim])
        
        Args:
            embedding_dir: Directory containing Step 1 outputs
            metadata_file: Name of metadata JSON file
            embedding_file: Name of embeddings numpy file
        
        Returns:
            (items_list, embeddings_array)
        """
        metadata_path = os.path.join(embedding_dir, metadata_file)
        embedding_path = os.path.join(embedding_dir, embedding_file)
        
        if not os.path.exists(metadata_path):
            raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
        if not os.path.exists(embedding_path):
            raise FileNotFoundError(f"Embedding file not found: {embedding_path}")
        
        # Load metadata
        with open(metadata_path, 'r', encoding='utf-8') as f:
            items = json.load(f)
        
        # Load embeddings
        embeddings = np.load(embedding_path)
        
        print(f"✓ Loaded {len(items)} items with shape {embeddings.shape}")
        return items, embeddings
    
    @staticmethod
    def load_from_image_folder(
        image_folder: str,
        auto_extract_metadata: bool = True
    ) -> List[Dict]:
        """
        Load clothing items from image folder (JPG).
        Auto-generates metadata from filename or manual entry.
        
        Expected folder structure:
            image_folder/
            ├── item_0_white_cotton_shirt.jpg
            ├── item_1_blue_jeans.jpg
            └── metadata.jsonl (optional: manual metadata)
        
        Args:
            image_folder: Path to folder containing JPG images
            auto_extract_metadata: Extract color/style from filename
        
        Returns:
            List of items with image_url, title, etc.
        """
        items = []
        image_files = list(Path(image_folder).glob("*.jpg")) + \
                     list(Path(image_folder).glob("*.jpeg"))
        
        for idx, img_path in enumerate(sorted(image_files)):
            filename = img_path.stem
            
            item = {
                "item_id": f"item_{idx}",
                "title": filename.replace("_", " ").title(),
                "image_url": str(img_path),
                "role": "unknown",  # Will be filled manually or by ML
                "color": "unknown",
                "style": "unknown",
                "material": "unknown",
                "season": "spring",  # Default
                "available": True,
            }
            items.append(item)
        
        print(f"✓ Loaded {len(items)} items from {image_folder}")
        return items
    
    @staticmethod
    def load_from_bda_project(
        repo_path: str = "../../BDA_Final_Project_114-1"
    ) -> tuple[List[Dict], Optional[np.ndarray]]:
        """
        Load clothing data directly from BDA Final Project repo.
        
        Args:
            repo_path: Path to BDA_Final_Project_114-1 folder
        
        Returns:
            (items_list, embeddings_array or None)
        """
        bda_path = Path(repo_path)
        
        # Try to find output folder
        possible_paths = [
            bda_path / "output" / "metadata.json",
            bda_path / "results" / "metadata.json",
            bda_path / "data" / "processed" / "metadata.json",
        ]
        
        metadata_path = None
        for p in possible_paths:
            if p.exists():
                metadata_path = p
                break
        
        if not metadata_path:
            print("⚠️  Could not find BDA project metadata. Using manual loader.")
            return [], None
        
        with open(metadata_path, 'r', encoding='utf-8') as f:
            items = json.load(f)
        
        # Try to load embeddings
        embedding_path = metadata_path.parent / "embeddings.npy"
        embeddings = None
        if embedding_path.exists():
            embeddings = np.load(embedding_path)
        
        print(f"✓ Loaded {len(items)} items from BDA project")
        return items, embeddings


class Step15InputBuilder:
    """Build realistic Step 1.5 input (color analysis, context, preferences)."""
    
    @staticmethod
    def generate_color_analysis(
        dominant_colors: List[str],
        seasonal_palette: str = "spring"
    ) -> Dict:
        """
        Generate color analysis from Step 1.5 (Personal Style module).
        
        Args:
            dominant_colors: User's color preferences (e.g., ['white', 'navy', 'beige'])
            seasonal_palette: Seasonal color type (spring, summer, autumn, winter)
        
        Returns:
            Color analysis dict
        """
        return {
            "dominant_colors": dominant_colors,
            "seasonal_palette": seasonal_palette,
            "undertone": "warm" if seasonal_palette in ["autumn", "spring"] else "cool",
            "contrast_level": "medium",
        }
    
    @staticmethod
    def generate_context_input(
        user_id: str,
        date_time: str,
        location: str,
        temp_c: int,
        humidity: int,
        condition: str,
        occasion: List[str],
        activities: Optional[List[Dict]] = None,
        color_preferences: Optional[List[str]] = None,
        style_preferences: Optional[List[str]] = None,
    ) -> Dict:
        """
        Generate complete Step 1.5 context input.
        
        Args:
            user_id: User identifier
            date_time: ISO format datetime
            location: User location
            temp_c: Temperature in Celsius
            humidity: Humidity percentage
            condition: Weather condition (sunny, rainy, cloudy, snowy)
            occasion: List of occasions (work, date, casual, gym, party)
            activities: Optional list of activities with times
            color_preferences: Color preferences from analysis
            style_preferences: Style preferences (casual, formal, sporty, boho, etc.)
        
        Returns:
            Complete context dict for Step 3 (Outfit Planner)
        """
        if activities is None:
            activities = [
                {"time": "09:00", "activity": occasion[0] if occasion else "casual", "location": location}
            ]
        
        if color_preferences is None:
            color_preferences = ["white", "navy", "beige"]
        
        if style_preferences is None:
            style_preferences = ["casual", "smart-casual"]
        
        return {
            "user_id": user_id,
            "date_time": date_time,
            "location": location,
            "weather": {
                "temp_c": temp_c,
                "humidity": humidity,
                "condition": condition,
            },
            "preferences": {
                "styles": style_preferences,
                "colors": color_preferences,
                "avoid": [],
                "fit_pref": "regular",
            },
            "occasion": occasion,
            "itinerary": activities,
            "palette_analysis": {
                "dominant_colors": color_preferences,
                "seasonal_palette": Step15InputBuilder._infer_season(temp_c),
            },
            "demographics": {
                "age": 28,
                "gender": "female",
            },
            "last_worn_history": [],
        }
    
    @staticmethod
    def _infer_season(temp_c: int) -> str:
        """Infer season from temperature."""
        if temp_c <= 0:
            return "winter"
        elif temp_c <= 10:
            return "fall"
        elif temp_c <= 20:
            return "spring"
        else:
            return "summer"


def example_integration():
    """Example: Integrate real clothing data with recommendation pipeline."""
    print("\n" + "="*70)
    print("INTEGRATION EXAMPLE: Step 1 → Step 3 (Outfit Planner)")
    print("="*70)
    
    # Option 1: Load from image folder (JPG)
    print("\n1. Loading clothing images...")
    # loader = ClothingDataLoader()
    # items = loader.load_from_image_folder("path/to/your/clothes/folder")
    
    # Option 2: Load from BDA project
    print("\n2. Loading from BDA Final Project (Step 1)...")
    # items, embeddings = loader.load_from_bda_project()
    
    # For demo, create sample items
    items = [
        {
            "item_id": "item_0",
            "title": "白色棉質短袖襯衫",
            "role": "top",
            "color": "white",
            "style": "casual",
            "material": "cotton",
            "season": "spring",
            "image_url": "/path/to/white_shirt.jpg"
        },
        {
            "item_id": "item_1",
            "title": "深藍色牛仔褲",
            "role": "bottom",
            "color": "navy",
            "style": "casual",
            "material": "denim",
            "season": "spring",
            "image_url": "/path/to/navy_jeans.jpg"
        },
    ]
    
    print(f"\n✓ Loaded {len(items)} items")
    print(f"  Sample: {items[0]['title']}")
    
    # Step 1.5: Generate context input
    print("\n3. Generating Step 1.5 Context Input...")
    builder = Step15InputBuilder()
    
    context = builder.generate_context_input(
        user_id="user_123",
        date_time="2025-12-10T09:00:00Z",
        location="台北",
        temp_c=22,
        humidity=60,
        condition="sunny",
        occasion=["work", "coffee_meet"],
        activities=[
            {"time": "09:00", "activity": "office", "location": "公司"},
            {"time": "13:00", "activity": "coffee", "location": "咖啡廳"},
        ],
        color_preferences=["white", "navy", "beige"],
        style_preferences=["casual", "smart-casual"],
    )
    
    print("\n✓ Generated context input:")
    print(json.dumps({
        "user_id": context["user_id"],
        "weather": context["weather"],
        "occasion": context["occasion"],
        "preferences": context["preferences"],
    }, indent=2, ensure_ascii=False))
    
    print("\n" + "="*70)
    print("FLOW: Items (Step 1) → Context (Step 1.5) → Recommendations (Step 3)")
    print("="*70)


if __name__ == "__main__":
    example_integration()
