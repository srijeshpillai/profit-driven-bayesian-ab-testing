"""
@file run_case_study_3.py
@brief Runs the simulation for Case Study 3: The "Futility Test".

This script configures an A/B/C test where the challenger variants ('B' and 'C')
offer only trivial, practically insignificant improvements over the control ('A').
The true RPV lifts are designed to be smaller than the Expected Loss threshold (epsilon).
This scenario tests a methodology's ability to correctly stop for futility,
avoiding false positives and saving resources.
"""

import pandas as pd
from simulation_engine import Simulation

# --- Simulation Configuration ---

# Defines the parameters for the "Futility Test" A/B/C scenario.
SCENARIO_3_CONFIG = {
    'name': "Case Study 3: Futility Test",
    'variants': [
        {'name': 'A', 'true_conv_rate': 0.0300, 'true_aov': 100.00, 'aov_std_dev': 40.0},  # Control RPV = $3.00
        {'name': 'B', 'true_conv_rate': 0.0301, 'true_aov': 100.00, 'aov_std_dev': 40.0},  # Trivial lift RPV = $3.01
        {'name': 'C', 'true_conv_rate': 0.0300, 'true_aov': 100.20, 'aov_std_dev': 40.0}   # Trivial lift RPV = $3.006
    ],
    'daily_total_visitors': 3000,  # Split among the 3 variants
    # The true RPV lifts ($0.01 and $0.006) are near or below this threshold.
    'epsilon': 0.01
}


def main():
    """Main function to execute and print results for Case Study 3."""
    print("--- Running Case Study 3: The Futility Test ---")

    # Run 5,000 simulations for robust aggregated results
    sim_instance = Simulation(SCENARIO_3_CONFIG)
    aggregated_results = sim_instance.run_multiple_simulations(n_runs=5000)

    print("\n--- Aggregated Results (5000 runs) ---")
    for name, summary in aggregated_results.items():
        print(f"\nMethodology: {name}")
        print(f"  Average Test Duration: {summary['Avg. Duration (days)']:.1f} days")
        print("  Decision Outcomes (%):")
        # Sort index for consistent, predictable report ordering
        print(summary['Decision %'].sort_index().round(1).to_string())


if __name__ == "__main__":
    main()
