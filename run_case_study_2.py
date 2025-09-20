# run_case_study_2.py

from simulation_engine import Simulation
import pandas as pd

# Define the configuration for the "Clear Winner" scenario (A/B/C/D Test)
SCENARIO_2_CONFIG = {
    'name': "Case Study 2: Clear Winner",
    'variants': [
        {'name': 'A', 'true_conv_rate': 0.030, 'true_aov': 100.0, 'aov_std_dev': 40.0}, # RPV = $3.00
        {'name': 'B', 'true_conv_rate': 0.029, 'true_aov': 100.0, 'aov_std_dev': 40.0}, # RPV = $2.90
        {'name': 'C', 'true_conv_rate': 0.031, 'true_aov': 105.0, 'aov_std_dev': 45.0}, # RPV = $3.255 (WINNER)
        {'name': 'D', 'true_conv_rate': 0.030, 'true_aov': 100.0, 'aov_std_dev': 40.0}  # RPV = $3.00
    ],
    'daily_total_visitors': 4000, # This will be split among the 4 variants
    'epsilon': 0.01 
}

if __name__ == "__main__":
    print("--- Running Case Study 2: The Clear Winner ---")
    
    # Run 5,000 simulations for aggregated results
    sim_instance = Simulation(SCENARIO_2_CONFIG)
    aggregated_results = sim_instance.run_multiple_simulations(n_runs=5000)
    
    print("\n--- Aggregated Results (5000 runs) ---")
    for name, summary in aggregated_results.items():
        print(f"\nMethodology: {name}")
        print(f"  Average Test Duration: {summary['Avg. Duration (days)']:.1f} days")
        print("  Decision Outcomes:")
        # Sort index for consistent reporting
        print(summary['Decision %'].sort_index().round(1).to_string())