# run_case_study_3.py

from simulation_engine import Simulation
import pandas as pd

# Define the configuration for the "Futility Test" scenario (A/B/C Test)
# Here, variants B and C have trivially small differences from A.
# The differences are much smaller than our epsilon threshold.
SCENARIO_3_CONFIG = {
    'name': "Case Study 3: Futility Test",
    'variants': [
        {'name': 'A', 'true_conv_rate': 0.03000, 'true_aov': 100.00, 'aov_std_dev': 40.0}, # RPV = $3.00
        {'name': 'B', 'true_conv_rate': 0.03010, 'true_aov': 100.00, 'aov_std_dev': 40.0}, # RPV = $3.01
        {'name': 'C', 'true_conv_rate': 0.03000, 'true_aov': 100.20, 'aov_std_dev': 40.0}  # RPV = $3.006
    ],
    'daily_total_visitors': 3000, # This will be split among the 3 variants
    'epsilon': 0.01 # Stop when expected loss is less than 1 cent RPV. 
                     # Note: The true RPV differences are smaller than epsilon.
}

if __name__ == "__main__":
    print("--- Running Case Study 3: The Futility Test ---")
    
    # Run 5,000 simulations for aggregated results
    sim_instance = Simulation(SCENARIO_3_CONFIG)
    aggregated_results = sim_instance.run_multiple_simulations(n_runs=5000)
    
    print("\n--- Aggregated Results (5000 runs) ---")
    for name, summary in aggregated_results.items():
        print(f"\nMethodology: {name}")
        print(f"  Average Test Duration: {summary['Avg. Duration (days)']:.1f} days")
        print("  Decision Outcomes:")
        # Sort index for consistent reporting
        print(summary['Decision %'].sort_index().round(1).to_string())