"""
IRIS Simulation - Statistical Analysis
Provides convergence tests and statistical validation
"""

import pandas as pd
import numpy as np
from typing import Dict, Any


def analyze_convergence(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Test thermodynamic convergence (D/V → 1)

    Uses Augmented Dickey-Fuller test for stationarity

    Args:
        df: Metrics DataFrame

    Returns:
        Dictionary with convergence analysis
    """
    try:
        from statsmodels.tsa.stattools import adfuller

        # ADF test on ratio_D_V
        result = adfuller(df['ratio_D_V'].dropna())
        adf_stat, p_value, _, _, critical_values, _ = result

        # Check convergence to 1.0
        last_12_mean = df['ratio_D_V'].iloc[-12:].mean()
        converges_to_1 = abs(last_12_mean - 1.0) < 0.1

        return {
            'adf_statistic': float(adf_stat),
            'p_value': float(p_value),
            'critical_values': {k: float(v) for k, v in critical_values.items()},
            'stationary': p_value < 0.05,
            'last_12_mean': float(last_12_mean),
            'converges_to_1': converges_to_1,
            'interpretation': (
                'CONVERGED: D/V ratio is stable around 1.0' if converges_to_1
                else 'DIVERGENT: D/V ratio has not converged to 1.0'
            )
        }

    except ImportError:
        # Fallback if statsmodels not available
        last_12_mean = df['ratio_D_V'].iloc[-12:].mean()
        last_12_std = df['ratio_D_V'].iloc[-12:].std()

        return {
            'adf_statistic': None,
            'p_value': None,
            'critical_values': None,
            'stationary': None,
            'last_12_mean': float(last_12_mean),
            'last_12_std': float(last_12_std),
            'converges_to_1': abs(last_12_mean - 1.0) < 0.1,
            'interpretation': 'Convergence test (simplified - statsmodels not available)'
        }


def analyze_inequality_evolution(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze evolution of inequality (Gini coefficient)

    Args:
        df: Metrics DataFrame

    Returns:
        Dictionary with inequality analysis
    """
    gini_start = df['gini'].iloc[:12].mean()
    gini_end = df['gini'].iloc[-12:].mean()
    delta_gini = gini_end - gini_start

    # Linear trend
    from scipy import stats
    slope, intercept, r_value, p_value, std_err = stats.linregress(
        df['cycle'], df['gini']
    )

    return {
        'gini_initial': float(gini_start),
        'gini_final': float(gini_end),
        'delta_gini': float(delta_gini),
        'trend': 'decreasing' if delta_gini < 0 else 'increasing',
        'trend_slope': float(slope),
        'trend_r_squared': float(r_value ** 2),
        'interpretation': (
            f"Gini {'decreased' if delta_gini < 0 else 'increased'} by "
            f"{abs(delta_gini):.4f} ({abs(delta_gini/gini_start*100):.2f}%)"
        )
    }


def analyze_regulation_efficiency(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze efficiency of κ and η regulation

    Args:
        df: Metrics DataFrame

    Returns:
        Dictionary with regulation efficiency metrics
    """
    # Calculate variations
    df_copy = df.copy()
    df_copy['delta_kappa'] = df_copy['kappa'].diff()
    df_copy['delta_ratio'] = df_copy['ratio_D_V'].diff()
    df_copy['delta_eta'] = df_copy['eta_global'].diff()

    # Correlations
    corr_kappa_ratio = df_copy[['delta_kappa', 'delta_ratio']].corr().iloc[0, 1]
    corr_eta_velocity = df_copy[['eta_global', 'nu_eff']].corr().iloc[0, 1]

    # Stability metrics
    kappa_mean = df['kappa'].mean()
    kappa_std = df['kappa'].std()
    kappa_range = (df['kappa'].min(), df['kappa'].max())

    eta_mean = df['eta_global'].mean()
    eta_std = df['eta_global'].std()
    eta_range = (df['eta_global'].min(), df['eta_global'].max())

    # Count extreme adjustments (near bounds)
    kappa_extreme = len(df[(df['kappa'] <= 0.6) | (df['kappa'] >= 1.9)])
    eta_extreme = len(df[(df['eta_global'] <= 0.6) | (df['eta_global'] >= 1.9)])

    return {
        'kappa': {
            'mean': float(kappa_mean),
            'std': float(kappa_std),
            'range': (float(kappa_range[0]), float(kappa_range[1])),
            'extreme_adjustments': int(kappa_extreme),
            'correlation_with_D_V': float(corr_kappa_ratio) if not np.isnan(corr_kappa_ratio) else 0
        },
        'eta': {
            'mean': float(eta_mean),
            'std': float(eta_std),
            'range': (float(eta_range[0]), float(eta_range[1])),
            'extreme_adjustments': int(eta_extreme),
            'correlation_with_velocity': float(corr_eta_velocity) if not np.isnan(corr_eta_velocity) else 0
        },
        'interpretation': (
            f"κ oscillates around {kappa_mean:.3f} (±{kappa_std:.3f}), "
            f"η oscillates around {eta_mean:.3f} (±{eta_std:.3f}). "
            f"Regulation is {'stable' if kappa_std < 0.2 and eta_std < 0.2 else 'volatile'}."
        )
    }


def analyze_demographic_resilience(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze demographic resilience (population stability)

    Args:
        df: Metrics DataFrame

    Returns:
        Dictionary with demographic analysis
    """
    pop_start = df['population'].iloc[0]
    pop_end = df['population'].iloc[-1]
    pop_growth = (pop_end - pop_start) / pop_start

    # Calculate volatility
    pop_std = df['population'].std()
    pop_cv = pop_std / df['population'].mean()  # Coefficient of variation

    # Birth/death balance
    total_births = df['births'].sum()
    total_deaths = df['deaths'].sum()
    net_migration = total_births - total_deaths

    return {
        'population_start': int(pop_start),
        'population_end': int(pop_end),
        'population_growth': float(pop_growth),
        'population_volatility': float(pop_cv),
        'total_births': int(total_births),
        'total_deaths': int(total_deaths),
        'net_migration': int(net_migration),
        'interpretation': (
            f"Population {'grew' if pop_growth > 0 else 'declined'} by "
            f"{abs(pop_growth)*100:.2f}% over simulation. "
            f"Demographic volatility: {pop_cv:.4f}"
        )
    }


def generate_full_report(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate complete statistical analysis report

    Args:
        df: Metrics DataFrame

    Returns:
        Dictionary with all analyses
    """
    report = {
        'simulation_summary': {
            'total_cycles': len(df),
            'total_years': len(df) // 12,
            'final_cycle': int(df['cycle'].iloc[-1])
        },
        'convergence': analyze_convergence(df),
        'inequality': analyze_inequality_evolution(df),
        'regulation': analyze_regulation_efficiency(df),
        'demographics': analyze_demographic_resilience(df)
    }

    return report


def save_report_txt(report: Dict[str, Any], filepath: str) -> None:
    """
    Save statistical report as text file

    Args:
        report: Report dictionary
        filepath: Output file path
    """
    with open(filepath, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("IRIS SIMULATION - STATISTICAL ANALYSIS REPORT\n")
        f.write("=" * 80 + "\n\n")

        # Simulation summary
        f.write("SIMULATION SUMMARY\n")
        f.write("-" * 80 + "\n")
        for key, value in report['simulation_summary'].items():
            f.write(f"  {key}: {value}\n")
        f.write("\n")

        # Convergence
        f.write("THERMODYNAMIC CONVERGENCE (D/V → 1)\n")
        f.write("-" * 80 + "\n")
        for key, value in report['convergence'].items():
            f.write(f"  {key}: {value}\n")
        f.write("\n")

        # Inequality
        f.write("INEQUALITY EVOLUTION\n")
        f.write("-" * 80 + "\n")
        for key, value in report['inequality'].items():
            f.write(f"  {key}: {value}\n")
        f.write("\n")

        # Regulation
        f.write("REGULATION EFFICIENCY (κ and η)\n")
        f.write("-" * 80 + "\n")
        f.write("Kappa (κ):\n")
        for key, value in report['regulation']['kappa'].items():
            f.write(f"  {key}: {value}\n")
        f.write("\nEta (η):\n")
        for key, value in report['regulation']['eta'].items():
            f.write(f"  {key}: {value}\n")
        f.write(f"\n{report['regulation']['interpretation']}\n\n")

        # Demographics
        f.write("DEMOGRAPHIC RESILIENCE\n")
        f.write("-" * 80 + "\n")
        for key, value in report['demographics'].items():
            f.write(f"  {key}: {value}\n")
        f.write("\n")

        f.write("=" * 80 + "\n")
        f.write("END OF REPORT\n")
        f.write("=" * 80 + "\n")
