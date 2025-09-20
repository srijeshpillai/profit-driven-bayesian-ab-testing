# run_case_study_1.py

from simulation_engine import Simulation
import pandas as pd

# Define the configuration for the "Revenue Trap" scenario
SCENARIO_1_CONFIG = {
    'variants': [
        {'name': 'A', 'true_conv_rate': 0.03, 'true_aov': 100.0, 'aov_std_dev': 40.0},
        {'name': 'B', 'true_conv_rate': 0.032, 'true_aov': 90.0, 'aov_std_dev': 35.0} # Higher CR, lower AOV
    ],
    'daily_visitors_per_variant': 2000,
    'epsilon': 0.01 # Stop when expected loss is less than 1 cent RPV
}

if __name__ == "__main__":
    print("--- Running Case Study 1: The Revenue Trap ---")
    
    # --- Part 1: Run a single simulation to generate the narrative ---
    print("\n[1] Running a single detailed simulation for the case study narrative...")
    sim_instance = Simulation(SCENARIO_1_CONFIG)
    single_run_results, daily_log = sim_instance.run_single_simulation(log_daily=True)
    
    print("\n--- Single Run Results ---")
    for name, result in single_run_results.items():
        print(f"{name}:")
        print(f"  Decision: {result['decision']} on Day {result['stop_day']}")
    
    print("\n--- Daily Log Sample for Narrative (Table 1) ---")
    # Display the log at the specific days mentioned in the narrative
    narrative_days = [10, 20, 30, single_run_results['Bayesian Framework']['stop_day']]
    print(daily_log[daily_log.day.isin(narrative_days)].round(3))
    
    # --- Part 2: Run 5,000 simulations for aggregated results ---
    print("\n[2] Running 5,000 simulations for robust aggregated results...")
    sim_instance_agg = Simulation(SCENARIO_1_CONFIG)
    aggregated_results = sim_instance_agg.run_multiple_simulations(n_runs=5000)
    
    print("\n--- Aggregated Results (5000 runs) ---")
    for name, summary in aggregated_results.items():
        print(f"\nMethodology: {name}")
        print(f"  Average Test Duration: {summary['Avg. Duration (days)']:.1f} days")
        print("  Decision Outcomes:")
        print(summary['Decision %'].round(1).to_string())