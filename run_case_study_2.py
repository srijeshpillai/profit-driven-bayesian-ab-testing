"""
@file run_case_study_2.py
@brief Runs the simulation for Case Study 2: The "Clear Winner".

This script configures and runs a multi-variant (A/B/C/D) test scenario designed
to evaluate the statistical power and reliability of each testing methodology.
Variant 'C' is designed to be a clear winner with a significant positive impact
on Revenue Per Visitor (RPV), while other variants introduce statistical noise.
The script runs 5,000 simulations to generate robust performance metrics.
"""

import pandas as pd
from simulation_engine import Simulation

# --- Simulation Configuration ---

# Defines the parameters for the "Clear Winner" A/B/C/D test scenario.
SCENARIO_2_CONFIG = {
    'name': "Case Study 2: Clear Winner",
    'variants': [
        {'name': 'A', 'true_conv_rate': 0.030, 'true_aov': 100.0, 'aov_std_dev': 40.0},  # Control RPV = $3.00
        {'name': 'B', 'true_conv_rate': 0.029, 'true_aov': 100.0, 'aov_std_dev': 40.0},  # Loser RPV = $2.90
        {'name': 'C', 'true_conv_rate': 0.031, 'true_aov': 105.0, 'aov_std_dev': 45.0},  # WINNER RPV = $3.255
        {'name': 'D', 'true_conv_rate': 0.030, 'true_aov': 100.0, 'aov_std_dev': 40.0}   # Flat RPV = $3.00
    ],
    'daily_total_visitors': 4000,  # Split among the 4 variants
    'epsilon': 0.001
}


def main():
    """Main function to execute and print results for Case Study 2."""
    print("--- Running Case Study 2: The Clear Winner ---")

    # Run 5,000 simulations for robust aggregated results
    sim_instance = Simulation(SCENARIO_2_CONFIG)
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
