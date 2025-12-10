"""
Example evaluation script demonstrating offline and online metrics.
Run: python -m src.evaluate_example
"""

import json
import numpy as np
from src.metrics import RecommendationMetrics, OnlineMetrics, evaluate_ranking_model


def example_offline_evaluation():
    """Example: Offline evaluation on test set."""
    print("\n" + "="*70)
    print("OFFLINE EVALUATION EXAMPLE")
    print("="*70)
    
    # Simulate model predictions and ground truth labels
    # In production: load from test.jsonl
    test_data = [
        {"predictions": [0.95, 0.85, 0.72], "labels": [1, 1, 0]},
        {"predictions": [0.88, 0.75, 0.60], "labels": [1, 0, 0]},
        {"predictions": [0.92, 0.80, 0.70], "labels": [1, 1, 1]},
        {"predictions": [0.70, 0.65, 0.55], "labels": [1, 0, 0]},
        {"predictions": [0.98, 0.90, 0.85], "labels": [1, 1, 0]},
    ]
    
    metrics = RecommendationMetrics()
    results = {"per_query": [], "aggregated": {}}
    
    # Evaluate each query
    for i, query in enumerate(test_data, 1):
        query_metrics = evaluate_ranking_model(query["predictions"], query["labels"])
        results["per_query"].append(query_metrics)
        print(f"\nQuery {i}:")
        for metric, value in query_metrics.items():
            print(f"  {metric}: {value:.4f}")
    
    # Aggregate
    agg = {}
    for metric in results["per_query"][0].keys():
        values = [q[metric] for q in results["per_query"]]
        agg[metric] = {
            "mean": np.mean(values),
            "std": np.std(values),
            "min": np.min(values),
            "max": np.max(values),
        }
    
    print("\n" + "-"*70)
    print("AGGREGATED METRICS:")
    print("-"*70)
    for metric, stats in agg.items():
        print(f"{metric:20s} | Mean: {stats['mean']:.4f} ± {stats['std']:.4f} "
              f"| Range: [{stats['min']:.4f}, {stats['max']:.4f}]")
    
    results["aggregated"] = agg
    return results


def example_online_evaluation():
    """Example: Online evaluation from user interactions."""
    print("\n" + "="*70)
    print("ONLINE EVALUATION EXAMPLE")
    print("="*70)
    
    # Simulate user interactions over time
    interactions_log = [
        ("outfit_1", "show"), ("outfit_1", "click"), ("outfit_1", "apply"),
        ("outfit_2", "show"), ("outfit_2", "click"),
        ("outfit_3", "show"), ("outfit_3", "dislike"),
        ("outfit_4", "show"), ("outfit_4", "click"), ("outfit_4", "apply"), ("outfit_4", "purchase"),
        ("outfit_5", "show"),
        ("outfit_1", "show"), ("outfit_1", "click"), ("outfit_1", "apply"), ("outfit_1", "purchase"),
        ("outfit_2", "show"), ("outfit_2", "dislike"),
    ]
    
    online = OnlineMetrics()
    for outfit_id, event_type in interactions_log:
        online.log_interaction(outfit_id, event_type)
    
    summary = online.get_summary()
    
    print("\nMetrics Summary:")
    print(f"  Click-Through Rate (CTR): {summary['ctr']:.2%}")
    print(f"  Acceptance Rate: {summary['acceptance_rate']:.2%}")
    print(f"  Conversion Rate: {summary['conversion_rate']:.2%}")
    print(f"  Dislike Rate: {summary['dislike_rate']:.2%}")
    print(f"  Total Interactions: {summary['total_interactions']}")
    
    print("\nPer-outfit breakdown:")
    for outfit_id, metrics in online.interactions.items():
        ctr = metrics['clicked'] / metrics['shown'] if metrics['shown'] > 0 else 0
        print(f"  {outfit_id}: shown={metrics['shown']}, clicked={metrics['clicked']}, "
              f"applied={metrics['applied']}, purchased={metrics['purchased']}, "
              f"ctr={ctr:.2%}")
    
    return summary


def example_diversity_evaluation():
    """Example: Diversity and coverage evaluation."""
    print("\n" + "="*70)
    print("DIVERSITY & COVERAGE EVALUATION EXAMPLE")
    print("="*70)
    
    metrics = RecommendationMetrics()
    
    # Example 1: Diversity of recommended outfits
    outfit_vectors = [
        [0.1, 0.2, 0.3, 0.4],  # Outfit 1 vector
        [0.4, 0.5, 0.6, 0.3],  # Outfit 2 vector
        [0.7, 0.8, 0.1, 0.2],  # Outfit 3 vector
    ]
    diversity = metrics.diversity_score(outfit_vectors)
    print(f"\nDiversity@3: {diversity:.4f}")
    print(f"  (0 = identical outfits, 1 = maximally different)")
    
    # Example 2: Coverage
    # Simulate 100 recommendation requests for different users
    all_recommended = []
    for user in range(50):
        # Each user gets 3 recommendations
        recommended_for_user = np.random.choice(20, size=3, replace=False)
        all_recommended.extend([f"item_{i}" for i in recommended_for_user])
    
    coverage = metrics.coverage(all_recommended, catalog_size=200)
    print(f"\nCatalog Coverage: {coverage:.2%}")
    print(f"  (Unique items recommended / Total items in catalog)")
    print(f"  Unique items recommended: {len(set(all_recommended))}")
    print(f"  Total catalog size: 200")
    
    # Example 3: Personalization
    user_profiles = {
        "user_1": ["item_1", "item_2", "item_3"],
        "user_2": ["item_2", "item_3", "item_4"],
        "user_3": ["item_5", "item_6", "item_7"],
    }
    personalization = metrics.personalization_score(user_profiles)
    print(f"\nPersonalization Score: {personalization:.4f}")
    print(f"  (0 = all users get same recommendations, 1 = all different)")


def example_calibration_evaluation():
    """Example: Model calibration."""
    print("\n" + "="*70)
    print("CALIBRATION EVALUATION EXAMPLE")
    print("="*70)
    
    metrics = RecommendationMetrics()
    
    # Model predictions and ground truth
    predicted_scores = [
        0.9, 0.9, 0.9, 0.85, 0.85, 0.85, 0.7, 0.7, 0.6, 0.5, 0.5, 0.4, 0.3
    ]
    actual_labels = [1, 1, 0, 1, 1, 0, 1, 0, 0, 0, 1, 0, 0]
    
    calibration_error = metrics.calibration_score(predicted_scores, actual_labels)
    
    print(f"\nCalibration Error: {calibration_error:.4f}")
    print(f"  (0 = perfect calibration, higher = less trustworthy)")
    print(f"\nInterpretation:")
    if calibration_error < 0.05:
        print("  ✓ Excellent: Model confidence scores are well-calibrated")
    elif calibration_error < 0.1:
        print("  ○ Good: Model is reasonably well-calibrated")
    else:
        print("  ✗ Poor: Model is poorly calibrated; confidence scores unreliable")


def generate_evaluation_report():
    """Generate comprehensive evaluation report."""
    print("\n" + "#"*70)
    print("# COMPREHENSIVE EVALUATION REPORT")
    print("#"*70)
    
    offline_results = example_offline_evaluation()
    online_results = example_online_evaluation()
    example_diversity_evaluation()
    example_calibration_evaluation()
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY & RECOMMENDATIONS")
    print("="*70)
    
    ndcg_mean = offline_results["aggregated"]["ndcg_at_3"]["mean"]
    ctr = online_results["ctr"]
    acceptance = online_results["acceptance_rate"]
    
    print(f"\nOffline Performance:")
    print(f"  NDCG@3: {ndcg_mean:.4f} {'✓' if ndcg_mean > 0.70 else '✗'} (target: > 0.70)")
    
    print(f"\nOnline Performance:")
    print(f"  CTR: {ctr:.2%} {'✓' if ctr > 0.10 else '✗'} (target: > 10%)")
    print(f"  Acceptance Rate: {acceptance:.2%} {'✓' if acceptance > 0.15 else '✗'} (target: > 15%)")
    
    print(f"\nStatus: {'✓ READY FOR PRODUCTION' if ndcg_mean > 0.70 and ctr > 0.10 else '✗ NEEDS IMPROVEMENT'}")


if __name__ == "__main__":
    generate_evaluation_report()
