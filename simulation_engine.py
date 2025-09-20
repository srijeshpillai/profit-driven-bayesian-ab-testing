# simulation_engine.py (Updated for A/B/n)

import numpy as np
import pandas as pd
from scipy import stats as sps
from statsmodels.stats.proportion import proportions_ztest
from tqdm import tqdm

class Variant:
    """Represents a single variant in the experiment, managing its true parameters and observed data."""
    def __init__(self, name, true_conv_rate, true_aov, aov_std_dev):
        self.name = name
        self.true_conv_rate = true_conv_rate
        self.true_aov = true_aov
        
        variance = aov_std_dev**2
        self.gamma_scale = variance / self.true_aov
        self.gamma_shape = self.true_aov / self.gamma_scale

        self.visitors = 0
        self.conversions = 0
        self.revenues = []
        self.conversion_revenues = []

    def add_visitors(self, n_visitors):
        """Simulates n_visitors arriving at the variant."""
        new_conversions = np.random.binomial(n_visitors, self.true_conv_rate)
        
        self.visitors += n_visitors
        self.conversions += new_conversions
        
        new_revs = np.random.gamma(self.gamma_shape, self.gamma_scale, new_conversions)
        self.conversion_revenues.extend(new_revs)
        
        all_new_visitor_revs = [0.0] * n_visitors
        all_new_visitor_revs[:new_conversions] = new_revs
        self.revenues.extend(all_new_visitor_revs)
        
class Methodology:
    """Base class for all testing methodologies."""
    def __init__(self, variants, name):
        self.variants = {v.name: v for v in variants}
        self.name = name
        self.is_stopped = False
        self.decision = "N/A"
        self.stop_day = -1

    def run_check(self, day):
        raise NotImplementedError

class PeekingProxyMethod(Methodology):
    """Simulates peeking at p-values for conversion rate (Z-test) in an A/B/n context."""
    def run_check(self, day):
        if self.is_stopped:
            return

        control = self.variants.get('A')
        if not control: # Ensure there is a control variant
            return
            
        for name, variant in self.variants.items():
            if name == 'A':
                continue
            
            if variant.conversions < 10 or control.conversions < 10:
                continue

            counts = np.array([variant.conversions, control.conversions])
            nobs = np.array([variant.visitors, control.visitors])
            
            try:
                # Check if variant is better than control
                if counts[0] > counts[1]:
                    stat, p_value = proportions_ztest(counts, nobs, alternative='larger')
                    if p_value < 0.05:
                        self.is_stopped = True
                        self.decision = f"Declared '{name}' winner over 'A'"
                        self.stop_day = day
                        return # Stop at the first significant winner
            except Exception as e:
                pass

class BayesianFramework(Methodology):
    """Implements our full Bayesian decision framework for A/B/n."""
    def __init__(self, variants, name, epsilon=0.01, S=20000):
        super().__init__(variants, name)
        self.epsilon = epsilon
        self.S = S 

        self.posteriors = {v.name: {} for v in variants}

    def run_check(self, day):
        if self.is_stopped:
            return
            
        rpd_samples = {}
        for name, variant in self.variants.items():
            # Conversion posterior
            conv_alpha = 1.0 + variant.conversions
            conv_beta = 1.0 + (variant.visitors - variant.conversions)
            
            p_samples = np.random.beta(conv_alpha, conv_beta, self.S)
            
            # Value posterior (Student-T)
            if variant.conversions > 1:
                mu_0, n_0, alpha_0, beta_0 = 100, 1.0, 1.0, 1.0
                k = variant.conversions
                x_bar = np.mean(variant.conversion_revenues)
                
                mu_k = (n_0 * mu_0 + k * x_bar) / (n_0 + k)
                n_k = n_0 + k
                alpha_k = alpha_0 + k / 2
                beta_k = beta_0 + 0.5 * np.sum((np.array(variant.conversion_revenues) - x_bar)**2) + (k * n_0 / (n_0 + k)) * 0.5 * ((x_bar-mu_0)**2)
                
                scale_t = np.sqrt(beta_k / (alpha_k * n_k))
                df_t = 2 * alpha_k
                mu_samples = sps.t.rvs(df=df_t, loc=mu_k, scale=scale_t, size=self.S)
            else:
                mu_samples = np.full(self.S, 100)

            rpd_samples[name] = p_samples * mu_samples

        all_samples_df = pd.DataFrame(rpd_samples)
        max_rpd_per_draw = all_samples_df.max(axis=1)
        
        expected_losses = {}
        for name in self.variants:
            loss_samples = max_rpd_per_draw - all_samples_df[name]
            expected_losses[name] = loss_samples.mean()

        min_loss_variant = min(expected_losses, key=expected_losses.get)
        min_loss_value = expected_losses[min_loss_variant]

        if min_loss_value < self.epsilon:
            self.is_stopped = True
            self.stop_day = day
            if min_loss_variant == 'A':
                self.decision = "Stopped for Futility / Control is best"
            else:
                self.decision = f"Declared '{min_loss_variant}' winner"

class Simulation:
    """Orchestrates the running of the entire simulation."""
    def __init__(self, config):
        self.config = config

    def run_single_simulation(self, max_days=200):
        # Initialize fresh variants and methodologies for a single run
        variants = [Variant(**v_config) for v_config in self.config['variants']]
        methodologies = [
            PeekingProxyMethod(variants, name="Peeking (Proxy)"),
            BayesianFramework(variants, name="Bayesian Framework", epsilon=self.config['epsilon'])
        ]

        for day in range(1, max_days + 1):
            daily_visitors = self.config['daily_total_visitors'] // len(variants)
            for variant in variants:
                variant.add_visitors(daily_visitors)

            for method in methodologies:
                method.run_check(day)

            if all(m.is_stopped for m in methodologies):
                break
        
        return {m.name: {'decision': m.decision, 'stop_day': m.stop_day} for m in methodologies}

    def run_multiple_simulations(self, n_runs=5000):
        """Runs the simulation n_runs times and aggregates the results."""
        all_results = []
        for _ in tqdm(range(n_runs), desc=f"Running {self.config.get('name', 'Simulations')}"):
            run_result = self.run_single_simulation()
            all_results.append(run_result)
        
        decisions = {
            "Peeking (Proxy)": [r["Peeking (Proxy)"]['decision'] for r in all_results],
            "Bayesian Framework": [r["Bayesian Framework"]['decision'] for r in all_results]
        }
        stop_days = {
            "Peeking (Proxy)": [r["Peeking (Proxy)"]['stop_day'] for r in all_results],
            "Bayesian Framework": [r["Bayesian Framework"]['stop_day'] for r in all_results]
        }
        
        summary = {}
        for method_name in ["Peeking (Proxy)", "Bayesian Framework"]:
            decision_series = pd.Series(decisions[method_name])
            stop_day_series = pd.Series(stop_days[method_name])
            
            decision_summary = decision_series.value_counts(normalize=True) * 100
            avg_duration = stop_day_series[decision_series != 'N/A'].mean()
            
            summary[method_name] = {
                "Decision %": decision_summary,
                "Avg. Duration (days)": avg_duration
            }
        return summary