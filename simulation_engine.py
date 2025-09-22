"""
@file simulation_engine.py
@brief Core engine for simulating and evaluating A/B/n testing methodologies.

This file contains the primary classes that power the simulation study:
- Variant: Manages the state and data generation for a single experimental group.
- Methodology: A base class for different decision-making frameworks.
- PeekingProxyMethod: Implements the flawed but common practice of peeking at
  p-values of a proxy metric (conversion rate).
- BayesianFramework: Implements the proposed profit-driven Bayesian framework
  using a two-part model for RPV and a decision rule based on Expected Loss.
- Simulation: Orchestrates the execution of single or multiple simulation runs.
"""

import numpy as np
import pandas as pd
from scipy import stats as sps
from statsmodels.stats.proportion import proportions_ztest
from tqdm import tqdm


class Variant:
    """Represents a single variant in an experiment."""

    def __init__(self, name, true_conv_rate, true_aov, aov_std_dev):
        """
        Initializes a variant with its ground-truth parameters.

        Args:
            name (str): The name of the variant (e.g., 'A', 'B').
            true_conv_rate (float): The true probability of conversion.
            true_aov (float): The true average order value.
            aov_std_dev (float): The standard deviation of order values.
        """
        self.name = name
        self.true_conv_rate = true_conv_rate
        self.true_aov = true_aov

        # Pre-calculate Gamma distribution parameters for efficient revenue generation
        variance = aov_std_dev**2
        self.gamma_scale = variance / self.true_aov
        self.gamma_shape = self.true_aov / self.gamma_scale

        # Accumulated observational data
        self.visitors = 0
        self.conversions = 0
        self.conversion_revenues = []

    def add_visitors(self, n_visitors):
        """Simulates n new visitors arriving at this variant."""
        # Simulate new conversions based on the true conversion rate
        new_conversions = np.random.binomial(n_visitors, self.true_conv_rate)

        self.visitors += n_visitors
        self.conversions += new_conversions

        # Generate revenue values only for the visitors who converted
        new_revenues = np.random.gamma(
            self.gamma_shape, self.gamma_scale, new_conversions
        )
        self.conversion_revenues.extend(new_revenues)


class Methodology:
    """Base class for all testing methodologies."""

    def __init__(self, variants, name):
        """Initializes a methodology with a set of variants."""
        self.variants = {v.name: v for v in variants}
        self.name = name
        self.is_stopped = False
        self.decision = "N/A (Timed Out)"
        self.stop_day = -1

    def run_check(self, day):
        """Abstract method to run a daily check and decide whether to stop."""
        raise NotImplementedError


class PeekingProxyMethod(Methodology):
    """
    Simulates the flawed practice of continuously checking p-values on a
    proxy metric (conversion rate) in an A/B/n context.
    """

    def run_check(self, day):
        """
        Performs a two-proportion Z-test for each variant against the control.
        Stops at the first variant that shows a p-value < 0.05.
        """
        if self.is_stopped:
            return

        control = self.variants.get('A')
        if not control or control.visitors == 0:
            return

        for name, variant in self.variants.items():
            if name == 'A':
                continue

            # Ensure sufficient data to avoid statistical errors
            if variant.conversions < 5 or control.conversions < 5:
                continue

            counts = np.array([variant.conversions, control.conversions])
            nobs = np.array([variant.visitors, control.visitors])

            # Use a one-sided test to check if the variant is better
            if counts[0] / nobs[0] > counts[1] / nobs[1]:
                try:
                    _, p_value = proportions_ztest(counts, nobs, alternative='larger')
                    if p_value < 0.05:
                        self.is_stopped = True
                        self.decision = f"Declared '{name}' winner"
                        self.stop_day = day
                        return  # Stop at the first significant winner
                except Exception:
                    # Ignore potential statistical errors from low data counts
                    pass


class BayesianFramework(Methodology):
    """
    Implements the proposed two-part Bayesian model for RPV with a
    decision-theoretic stopping rule based on Expected Loss.
    """

    def __init__(self, variants, name, epsilon=0.001, S=20000):
        """Initializes the framework with a loss threshold and sample size."""
        super().__init__(variants, name)
        self.epsilon = epsilon
        self.S = S  # Number of Monte Carlo samples

    def run_check(self, day):
        """
        Updates posteriors, calculates Expected Loss for each variant,
        and stops if the minimum expected loss falls below the epsilon threshold.
        """
        if self.is_stopped:
            return

        rpd_samples = {}
        for name, variant in self.variants.items():
            # 1. Conversion Model (Beta-Binomial)
            # Posterior for conversion rate 'p' is Beta(1+k, 1+N-k)
            conv_alpha = 1.0 + variant.conversions
            conv_beta = 1.0 + (variant.visitors - variant.conversions)
            p_samples = np.random.beta(conv_alpha, conv_beta, self.S)

            # 2. Value Model (Normal-Inverse-Gamma -> Student-T posterior for mean)
            if variant.conversions > 1:
                # Priors for the value model (mean and variance of revenue)
                mu_0, n_0, alpha_0, beta_0 = 100.0, 1.0, 1.0, 1.0
                k = variant.conversions
                x_bar = np.mean(variant.conversion_revenues)
                ssd = np.sum((np.array(variant.conversion_revenues) - x_bar)**2)

                # Posterior parameters for the NIG distribution
                mu_k = (n_0 * mu_0 + k * x_bar) / (n_0 + k)
                n_k = n_0 + k
                alpha_k = alpha_0 + k / 2.0
                beta_k = beta_0 + 0.5 * ssd + (k * n_0 / (n_0 + k)) * 0.5 * (x_bar - mu_0)**2

                # Marginal posterior for the mean 'mu' is a Student-T distribution
                scale_t = np.sqrt(beta_k / (alpha_k * n_k))
                df_t = 2 * alpha_k
                mu_samples = sps.t.rvs(df=df_t, loc=mu_k, scale=scale_t, size=self.S)
            else:
                # If there's not enough data, draw from a wide prior centered at 100
                mu_samples = sps.norm.rvs(loc=100, scale=50, size=self.S)

            # 3. Combine posteriors to get RPV = p * mu
            rpd_samples[name] = p_samples * mu_samples

        # 4. Decision Theory: Calculate Expected Loss
        all_samples_df = pd.DataFrame(rpd_samples)
        max_rpd_per_draw = all_samples_df.max(axis=1)

        expected_losses = {}
        for name in self.variants:
            loss_samples = max_rpd_per_draw - all_samples_df[name]
            expected_losses[name] = loss_samples.mean()

        # Find the variant with the minimum expected loss (the current best choice)
        min_loss_variant = min(expected_losses, key=expected_losses.get)
        min_loss_value = expected_losses[min_loss_variant]

        # 5. Stopping Rule
        if min_loss_value < self.epsilon:
            self.is_stopped = True
            self.stop_day = day
            if min_loss_variant == 'A':
                self.decision = "Stopped for Futility"
            else:
                self.decision = f"Declared '{min_loss_variant}' winner"


class Simulation:
    """Orchestrates the running and aggregation of simulation results."""

    def __init__(self, config):
        """Initializes the simulation with a specific scenario config."""
        self.config = config

    def run_single_simulation(self, max_days=200, log_daily=False):
        """
        Runs a single end-to-end simulation for a maximum number of days.
        """
        variants = [Variant(**v_config) for v_config in self.config['variants']]
        methodologies = [
            PeekingProxyMethod(variants, name="Peeking (Proxy)"),
            BayesianFramework(variants, name="Bayesian Framework", epsilon=self.config['epsilon'])
        ]
        
        daily_log_data = []

        for day in range(1, max_days + 1):
            daily_visitors = self.config['daily_total_visitors'] // len(variants)
            for variant in variants:
                variant.add_visitors(daily_visitors)

            for method in methodologies:
                method.run_check(day)
            
            if log_daily and not methodolog
