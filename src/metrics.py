"""
Evaluation metrics for outfit recommendation system.
Includes offline (retrieval, ranking) and online (user engagement) metrics.
"""

import json
from typing import List, Dict, Tuple
from collections import defaultdict
import numpy as np


class RecommendationMetrics:
    """Compute offline evaluation metrics."""
    
    @staticmethod
    def ndcg_at_k(relevance_scores: List[float], k: int = 3) -> float:
        """
        Normalized Discounted Cumulative Gain @ k.
        Higher is better (max 1.0).
        
        Args:
            relevance_scores: List of relevance scores for ranked items (0-1)
            k: Top-k cutoff
        
        Returns:
            NDCG@k score
        """
        if not relevance_scores or k <= 0:
            return 0.0
        
        relevance_scores = relevance_scores[:k]
        
        # DCG = sum(rel_i / log2(i+1))
        dcg = sum(rel / np.log2(i + 2) for i, rel in enumerate(relevance_scores))
        
        # IDCG = DCG of perfect ranking
        ideal = sorted(relevance_scores, reverse=True)
        idcg = sum(rel / np.log2(i + 2) for i, rel in enumerate(ideal))
        
        return dcg / idcg if idcg > 0 else 0.0
    
    @staticmethod
    def precision_at_k(relevant_items: List[int], k: int = 3) -> float:
        """
        Precision @ k: fraction of top-k items that are relevant.
        
        Args:
            relevant_items: Binary labels (1=relevant, 0=not relevant)
            k: Top-k cutoff
        
        Returns:
            Precision@k (0-1)
        """
        if not relevant_items or k <= 0:
            return 0.0
        return sum(relevant_items[:k]) / k
    
    @staticmethod
    def mean_reciprocal_rank(relevant_items: List[int]) -> float:
        """
        Mean Reciprocal Rank: position of first relevant item.
        High score if relevant item appears early.
        
        Args:
            relevant_items: Binary labels
        
        Returns:
            MRR (0-1)
        """
        for i, rel in enumerate(relevant_items, 1):
            if rel:
                return 1.0 / i
        return 0.0
    
    @staticmethod
    def map_at_k(relevant_items: List[int], k: int = 3) -> float:
        """
        Mean Average Precision @ k.
        
        Args:
            relevant_items: Binary labels
            k: Top-k cutoff
        
        Returns:
            MAP@k
        """
        if not relevant_items or k <= 0:
            return 0.0
        
        relevant_items = relevant_items[:k]
        precisions = []
        for i, rel in enumerate(relevant_items, 1):
            if rel:
                precisions.append(sum(relevant_items[:i]) / i)
        
        return sum(precisions) / len(relevant_items) if relevant_items else 0.0
    
    @staticmethod
    def diversity_score(outfit_vectors: List[List[float]]) -> float:
        """
        Intra-list diversity: average pairwise distance between outfits.
        Encourages variety in recommendations.
        
        Args:
            outfit_vectors: List of embedding vectors for outfits
        
        Returns:
            Diversity score (0-1, higher = more diverse)
        """
        if len(outfit_vectors) < 2:
            return 1.0
        
        outfit_vectors = np.array(outfit_vectors)
        # Normalize vectors
        norms = np.linalg.norm(outfit_vectors, axis=1, keepdims=True)
        outfit_vectors = outfit_vectors / (norms + 1e-8)
        
        # Compute pairwise cosine distances (1 - similarity)
        distances = []
        for i in range(len(outfit_vectors)):
            for j in range(i + 1, len(outfit_vectors)):
                sim = np.dot(outfit_vectors[i], outfit_vectors[j])
                distances.append(1 - sim)
        
        return np.mean(distances) if distances else 0.0
    
    @staticmethod
    def calibration_score(predicted_scores: List[float], actual_labels: List[int]) -> float:
        """
        Calibration: do predicted scores match actual acceptance rates?
        Perfect calibration = 1.0.
        
        Args:
            predicted_scores: Model's confidence scores (0-1)
            actual_labels: Actual user acceptance (0-1)
        
        Returns:
            Calibration error (lower is better, 0 = perfect)
        """
        if not predicted_scores:
            return 1.0
        
        predicted_scores = np.array(predicted_scores)
        actual_labels = np.array(actual_labels)
        
        # Bin predictions by score ranges
        bins = np.linspace(0, 1, 11)  # 0-10%, 10-20%, ..., 90-100%
        calibration_error = 0.0
        count = 0
        
        for i in range(len(bins) - 1):
            mask = (predicted_scores >= bins[i]) & (predicted_scores < bins[i + 1])
            if mask.sum() > 0:
                expected = np.mean(predicted_scores[mask])
                actual = np.mean(actual_labels[mask])
                calibration_error += abs(expected - actual)
                count += 1
        
        return calibration_error / count if count > 0 else 0.0
    
    @staticmethod
    def coverage(recommended_items: List[str], catalog_size: int) -> float:
        """
        Catalog coverage: what fraction of items are recommended?
        Higher coverage = less repetitive.
        
        Args:
            recommended_items: List of item IDs recommended (may have duplicates)
            catalog_size: Total items in catalog
        
        Returns:
            Coverage (0-1)
        """
        unique_items = len(set(recommended_items))
        return unique_items / catalog_size if catalog_size > 0 else 0.0
    
    @staticmethod
    def personalization_score(user_profiles: Dict[str, List[str]]) -> float:
        """
        Personalization: do different users get different recommendations?
        
        Args:
            user_profiles: Dict mapping user_id to list of recommended item_ids
        
        Returns:
            Personalization score (0-1, higher = more personalized)
        """
        if len(user_profiles) < 2:
            return 1.0
        
        users = list(user_profiles.values())
        overlaps = []
        
        for i in range(len(users)):
            for j in range(i + 1, len(users)):
                set_i = set(users[i])
                set_j = set(users[j])
                if set_i and set_j:
                    overlap = len(set_i & set_j) / min(len(set_i), len(set_j))
                    overlaps.append(overlap)
        
        return 1 - (np.mean(overlaps) if overlaps else 0)


class OnlineMetrics:
    """Track online evaluation metrics from user interactions."""
    
    def __init__(self):
        self.interactions = defaultdict(lambda: {
            "shown": 0,
            "clicked": 0,
            "applied": 0,
            "purchased": 0,
            "dislikes": 0,
        })
    
    def log_interaction(
        self,
        outfit_id: str,
        event_type: str,  # 'show', 'click', 'apply', 'purchase', 'dislike'
    ):
        """Log a user interaction with an outfit."""
        event_map = {
            "show": "shown",
            "click": "clicked",
            "apply": "applied",
            "purchase": "purchased",
            "dislike": "dislikes",
        }
        if event_type in event_map:
            self.interactions[outfit_id][event_map[event_type]] += 1
    
    def get_ctr(self) -> float:
        """Click-through rate: clicked / shown."""
        total_shown = sum(v["shown"] for v in self.interactions.values())
        total_clicked = sum(v["clicked"] for v in self.interactions.values())
        return total_clicked / total_shown if total_shown > 0 else 0.0
    
    def get_acceptance_rate(self) -> float:
        """Acceptance rate: applied / shown."""
        total_shown = sum(v["shown"] for v in self.interactions.values())
        total_applied = sum(v["applied"] for v in self.interactions.values())
        return total_applied / total_shown if total_shown > 0 else 0.0
    
    def get_conversion_rate(self) -> float:
        """Conversion rate: purchased / applied."""
        total_applied = sum(v["applied"] for v in self.interactions.values())
        total_purchased = sum(v["purchased"] for v in self.interactions.values())
        return total_purchased / total_applied if total_applied > 0 else 0.0
    
    def get_dislike_rate(self) -> float:
        """Dislike rate: dislikes / shown."""
        total_shown = sum(v["shown"] for v in self.interactions.values())
        total_dislikes = sum(v["dislikes"] for v in self.interactions.values())
        return total_dislikes / total_shown if total_shown > 0 else 0.0
    
    def get_summary(self) -> Dict:
        """Get summary of all metrics."""
        return {
            "ctr": self.get_ctr(),
            "acceptance_rate": self.get_acceptance_rate(),
            "conversion_rate": self.get_conversion_rate(),
            "dislike_rate": self.get_dislike_rate(),
            "total_interactions": sum(
                sum(v.values()) for v in self.interactions.values()
            ),
        }


class ABTestFramework:
    """Simple A/B testing framework for comparing recommendation strategies."""
    
    def __init__(self):
        self.variants = {}
    
    def add_variant(self, name: str, metrics_collector: OnlineMetrics):
        """Add a variant (e.g., 'control', 'treatment')."""
        self.variants[name] = metrics_collector
    
    def statistical_test(self, variant_a: str, variant_b: str, metric: str = "ctr") -> Dict:
        """
        Perform simple statistical test (Chi-squared for binary metrics).
        
        Args:
            variant_a: Name of first variant
            variant_b: Name of second variant
            metric: One of 'ctr', 'acceptance_rate', 'conversion_rate', 'dislike_rate'
        
        Returns:
            Dict with test results and significance
        """
        if variant_a not in self.variants or variant_b not in self.variants:
            return {"error": "Variant not found"}
        
        from scipy.stats import chi2_contingency
        
        metrics_a = self.variants[variant_a]
        metrics_b = self.variants[variant_b]
        
        # Simple CTR comparison
        if metric == "ctr":
            total_shown_a = sum(v["shown"] for v in metrics_a.interactions.values())
            total_clicked_a = sum(v["clicked"] for v in metrics_a.interactions.values())
            
            total_shown_b = sum(v["shown"] for v in metrics_b.interactions.values())
            total_clicked_b = sum(v["clicked"] for v in metrics_b.interactions.values())
            
            contingency_table = [
                [total_clicked_a, total_shown_a - total_clicked_a],
                [total_clicked_b, total_shown_b - total_clicked_b],
            ]
            
            chi2, p_value, dof, expected = chi2_contingency(contingency_table)
            
            ctr_a = total_clicked_a / total_shown_a if total_shown_a > 0 else 0
            ctr_b = total_clicked_b / total_shown_b if total_shown_b > 0 else 0
            
            return {
                "metric": metric,
                "variant_a": {"name": variant_a, "value": ctr_a},
                "variant_b": {"name": variant_b, "value": ctr_b},
                "chi2_statistic": chi2,
                "p_value": p_value,
                "is_significant": p_value < 0.05,
                "winner": variant_a if ctr_a > ctr_b else variant_b,
            }
        
        return {"error": f"Metric {metric} not implemented"}


def evaluate_ranking_model(predictions: List[float], labels: List[int], k: int = 3) -> Dict:
    """
    Comprehensive evaluation of ranking model.
    
    Args:
        predictions: Model's prediction scores
        labels: Ground truth binary labels (1=good, 0=bad)
        k: Top-k for NDCG/Precision
    
    Returns:
        Dict of all metrics
    """
    metrics = RecommendationMetrics()
    
    return {
        "ndcg_at_3": metrics.ndcg_at_k(predictions, k=3),
        "ndcg_at_5": metrics.ndcg_at_k(predictions, k=5),
        "ndcg_at_10": metrics.ndcg_at_k(predictions, k=10),
        "precision_at_3": metrics.precision_at_k(labels, k=3),
        "precision_at_5": metrics.precision_at_k(labels, k=5),
        "map_at_5": metrics.map_at_k(labels, k=5),
        "mrr": metrics.mean_reciprocal_rank(labels),
    }


if __name__ == "__main__":
    # Example usage
    print("Recommendation Metrics Module")
    print("="*60)
    
    # Example offline metrics
    metrics = RecommendationMetrics()
    predictions = [0.95, 0.85, 0.72]
    labels = [1, 1, 0]
    
    print("\nOffline Metrics Example:")
    print(f"NDCG@3: {metrics.ndcg_at_k(predictions, k=3):.4f}")
    print(f"Precision@3: {metrics.precision_at_k(labels, k=3):.4f}")
    print(f"MRR: {metrics.mean_reciprocal_rank(labels):.4f}")
    print(f"MAP@3: {metrics.map_at_k(labels, k=3):.4f}")
    
    # Example online metrics
    online = OnlineMetrics()
    for i in range(100):
        online.log_interaction(f"outfit_{i%10}", "show")
        if i % 4 == 0:
            online.log_interaction(f"outfit_{i%10}", "click")
        if i % 10 == 0:
            online.log_interaction(f"outfit_{i%10}", "apply")
    
    print("\nOnline Metrics Example:")
    summary = online.get_summary()
    for key, val in summary.items():
        print(f"{key}: {val:.4f}" if isinstance(val, float) else f"{key}: {val}")
