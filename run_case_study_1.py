"""
@file run_case_study_1.py
@brief Runs the simulation for Case Study 1: The "Revenue Trap".

This script defines the parameters for a classic A/B test scenario where one
variant has a higher conversion rate but a lower average order value, creating
a trap for methodologies that only optimize for proxy metrics. It runs both a
single detailed simulation for narrative purposes and a large-scale simulation
of 5,000 runs to generate robust, aggregated performance metrics.
"""

import pandas as pd
from simulation_engine import Simulation

# --- Simulation Configuration ---

# Defines the parameters for the "Revenue Trap" A/B test scenario.
# Variant B has a higher Conversion Rate (CR) but a lower Average Order Value
# (AOV), resulting in a lower overall Revenue Per Visitor (RPV).
SCENARIO_1_CONFIG = {
    'name': "Case Study 1: Revenue Trap",
    'variants': [
        {'name': 'A', 'true_conv_rate': 0.03, 'true_aov': 100.0, 'aov_std_dev': 40.0},
        {'name': 'B', 'true_conv_rate': 0.032, 'true_aov': 90.0, 'aov_std_dev': 35.0}
    ],
    'daily_total_visitors': 4000,
    # Stop when the expected loss is less than 0.1 cents per visitor
    'epsilon': 0.001
}


def main():
    """Main function to execute and print results for Case Study 1."""
    print("--- Running Case Study 1: The Revenue Trap ---")

    # --- Part 1: Run a single simulation for qualitative analysis ---
    print("\n[1] Running a single detailed simulation for narrative...")
    sim_instance = Simulation(SCENARIO_1_CONFIG)
    single_run_results, daily_log = sim_instance.run_single_simulation(log_daily=True)

    print("\n--- Single Run Results ---")
    for name, result in single_run_results.items():
        print(f"{name}:")
        print(f"  Decision: {result['decision']} on Day {result['stop_day']}")

    # Display key moments from the daily log for the paper's narrative
    if not daily_log.empty:
        print("\n--- Daily Log Sample for Narrative ---")
        stop_day = single_run_results['Bayesian Framework']['stop_day']
        narrative_days = [10, 13, stop_day]
        print(daily_log[daily_log.day.isin(narrative_days)].round(3))

    # --- Part 2: Run 5,000 simulations for robust aggregated results ---
    print("\n[2] Running 5,000 simulations for aggregated metrics...")
    # It's good practice to create a new instance for the aggregated run
    sim_instance_agg = Simulation(SCENARIO_1_CONFIG)
    aggregated_results = sim_instance_agg.run_multiple_simulations(n_runs=5000)

    print("\n--- Aggregated Results (5000 runs) ---")
    for name, summary in aggregated_results.items():
        print(f"\nMethodology: {name}")
        print(f"  Average Test Duration: {summary['Avg. Duration (days)']:.1f} days")
        print("  Decision Outcomes (%):")
        # Use .to_string() for clean, aligned printing of the pandas Series
        print(summary['Decision %'].round(1).to_string())


if __name__ == "__main__":
    main()
