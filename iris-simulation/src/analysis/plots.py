"""
IRIS Simulation - Visualization
Generates plots for analysis
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import os

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 300


def generate_all_plots(df: pd.DataFrame, output_dir: str) -> None:
    """
    Generate all analysis plots

    Args:
        df: Metrics DataFrame
        output_dir: Directory to save plots
    """
    print("  Generating plots...")

    plot_thermodynamique(df, output_dir)
    plot_distribution(df, output_dir)
    plot_demographie(df, output_dir)
    plot_flux_economiques(df, output_dir)
    plot_capteurs(df, output_dir)
    plot_rad_sectors(df, output_dir)

    print("  ✓ All plots generated")


def plot_thermodynamique(df: pd.DataFrame, output_dir: str) -> None:
    """Plot thermodynamic indicators"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # D/V ratio
    axes[0, 0].plot(df['cycle'], df['ratio_D_V'], label='D/V', color='red', linewidth=2)
    axes[0, 0].axhline(y=1.0, linestyle='--', color='black', label='Target', alpha=0.5)
    axes[0, 0].fill_between(df['cycle'], 0.85, 1.15, alpha=0.2, color='green', label='Stable zone')
    axes[0, 0].set_xlabel('Cycle')
    axes[0, 0].set_ylabel('Ratio D/V')
    axes[0, 0].set_title('Thermometric Ratio D/V')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)

    # Kappa
    axes[0, 1].plot(df['cycle'], df['kappa'], label='κ', color='blue', linewidth=2)
    axes[0, 1].axhline(y=1.0, linestyle='--', color='black', alpha=0.5)
    axes[0, 1].fill_between(df['cycle'], 0.5, 2.0, alpha=0.1, color='blue')
    axes[0, 1].set_xlabel('Cycle')
    axes[0, 1].set_ylabel('κ (kappa)')
    axes[0, 1].set_title('Liquidity Regulator κ')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)

    # Eta
    axes[1, 0].plot(df['cycle'], df['eta_global'], label='η global', color='green', linewidth=2)
    axes[1, 0].axhline(y=1.0, linestyle='--', color='black', alpha=0.5)
    axes[1, 0].fill_between(df['cycle'], 0.5, 2.0, alpha=0.1, color='green')
    axes[1, 0].set_xlabel('Cycle')
    axes[1, 0].set_ylabel('η (eta)')
    axes[1, 0].set_title('Creation Multiplier η')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)

    # V_ON
    axes[1, 1].plot(df['cycle'], df['V_ON'], label='V_ON', color='purple', linewidth=2)
    axes[1, 1].set_xlabel('Cycle')
    axes[1, 1].set_ylabel('Verum')
    axes[1, 1].set_title('Active Value in Circulation (V_ON)')
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'thermodynamique.png'))
    plt.close()


def plot_distribution(df: pd.DataFrame, output_dir: str) -> None:
    """Plot wealth distribution indicators"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Gini coefficient
    axes[0, 0].plot(df['cycle'], df['gini'], color='orange', linewidth=2)
    axes[0, 0].set_xlabel('Cycle')
    axes[0, 0].set_ylabel('Gini Coefficient')
    axes[0, 0].set_title('Inequality: Gini Coefficient')
    axes[0, 0].set_ylim(0, 1)
    axes[0, 0].grid(True, alpha=0.3)

    # Top shares
    axes[0, 1].plot(df['cycle'], df['top10_share'] * 100, label='Top 10%', linewidth=2)
    axes[0, 1].plot(df['cycle'], df['top20_share'] * 100, label='Top 20%', linewidth=2)
    axes[0, 1].set_xlabel('Cycle')
    axes[0, 1].set_ylabel('Wealth Share (%)')
    axes[0, 1].set_title('Wealth Concentration')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)

    # Median wealth
    axes[1, 0].plot(df['cycle'], df['median_wealth'], color='teal', linewidth=2)
    axes[1, 0].set_xlabel('Cycle')
    axes[1, 0].set_ylabel('Verum')
    axes[1, 0].set_title('Median Patrimony')
    axes[1, 0].grid(True, alpha=0.3)

    # Eta distribution
    axes[1, 1].plot(df['cycle'], df['eta_mean'], label='Mean η', linewidth=2)
    axes[1, 1].fill_between(
        df['cycle'],
        df['eta_mean'] - df['eta_std'],
        df['eta_mean'] + df['eta_std'],
        alpha=0.3,
        label='±1 std'
    )
    axes[1, 1].set_xlabel('Cycle')
    axes[1, 1].set_ylabel('η (individual)')
    axes[1, 1].set_title('Individual Productivity Distribution')
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'distribution.png'))
    plt.close()


def plot_demographie(df: pd.DataFrame, output_dir: str) -> None:
    """Plot demographic indicators"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Population
    axes[0, 0].plot(df['cycle'], df['population'], color='darkblue', linewidth=2)
    axes[0, 0].set_xlabel('Cycle')
    axes[0, 0].set_ylabel('Agents')
    axes[0, 0].set_title('Total Population')
    axes[0, 0].grid(True, alpha=0.3)

    # Enterprises
    axes[0, 1].plot(df['cycle'], df['entreprises'], color='darkgreen', linewidth=2)
    axes[0, 1].set_xlabel('Cycle')
    axes[0, 1].set_ylabel('Enterprises')
    axes[0, 1].set_title('Number of Active Enterprises')
    axes[0, 1].grid(True, alpha=0.3)

    # Births and Deaths
    axes[1, 0].plot(df['cycle'], df['deaths'], label='Deaths', color='red', linewidth=2)
    axes[1, 0].plot(df['cycle'], df['births'], label='Births', color='green', linewidth=2)
    axes[1, 0].set_xlabel('Cycle')
    axes[1, 0].set_ylabel('Agents')
    axes[1, 0].set_title('Natality / Mortality')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)

    # Median age
    axes[1, 1].plot(df['cycle'], df['age_median'], color='brown', linewidth=2)
    axes[1, 1].set_xlabel('Cycle')
    axes[1, 1].set_ylabel('Years')
    axes[1, 1].set_title('Median Age')
    axes[1, 1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'demographie.png'))
    plt.close()


def plot_flux_economiques(df: pd.DataFrame, output_dir: str) -> None:
    """Plot economic flows"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Universal Income
    axes[0, 0].plot(df['cycle'], df['RU_total'], color='gold', linewidth=2)
    axes[0, 0].set_xlabel('Cycle')
    axes[0, 0].set_ylabel('Unum')
    axes[0, 0].set_title('Universal Income Distributed')
    axes[0, 0].grid(True, alpha=0.3)

    # U burned
    axes[0, 1].plot(df['cycle'], df['U_burn'], color='crimson', linewidth=2)
    axes[0, 1].set_xlabel('Cycle')
    axes[0, 1].set_ylabel('Unum')
    axes[0, 1].set_title('U Burned per Cycle')
    axes[0, 1].grid(True, alpha=0.3)

    # Enterprise V flows
    axes[1, 0].plot(df['cycle'], df['V_burned'], label='V burned (60%)', linewidth=2)
    axes[1, 0].plot(df['cycle'], df['V_salaries'], label='V salaries (40%)', linewidth=2)
    axes[1, 0].set_xlabel('Cycle')
    axes[1, 0].set_ylabel('Verum')
    axes[1, 0].set_title('Enterprise V Flows')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)

    # Staking volume
    axes[1, 1].plot(df['cycle'], df['staking_volume'], color='indigo', linewidth=2)
    axes[1, 1].set_xlabel('Cycle')
    axes[1, 1].set_ylabel('Active Contracts')
    axes[1, 1].set_title('Active Staking Volume')
    axes[1, 1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'flux.png'))
    plt.close()


def plot_capteurs(df: pd.DataFrame, output_dir: str) -> None:
    """Plot system sensors"""
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    # Investment/Consumption ratio
    axes[0].plot(df['cycle'], df['r_ic'], color='navy', linewidth=2)
    axes[0].axhline(y=1.0, linestyle='--', color='red', alpha=0.5, label='Target')
    axes[0].set_xlabel('Cycle')
    axes[0].set_ylabel('Ratio')
    axes[0].set_title('Investment/Consumption Ratio (r_ic)')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # Circulation velocity
    axes[1].plot(df['cycle'], df['nu_eff'], color='darkgreen', linewidth=2)
    axes[1].axhline(y=0.20, linestyle='--', color='red', alpha=0.5, label='Target (0.20)')
    axes[1].set_xlabel('Cycle')
    axes[1].set_ylabel('Velocity')
    axes[1].set_title('Effective Circulation Velocity (ν_eff)')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    # Engagement rate
    axes[2].plot(df['cycle'], df['tau_eng'], color='purple', linewidth=2)
    axes[2].axhline(y=0.35, linestyle='--', color='red', alpha=0.5, label='Target (0.35)')
    axes[2].axhline(y=0.55, linestyle='--', color='orange', alpha=0.5, label='Critical (0.55)')
    axes[2].set_xlabel('Cycle')
    axes[2].set_ylabel('Rate')
    axes[2].set_title('Engagement Rate (τ_eng)')
    axes[2].legend()
    axes[2].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'capteurs.png'))
    plt.close()


def plot_rad_sectors(df: pd.DataFrame, output_dir: str) -> None:
    """Plot RAD debt sectors"""
    fig, ax = plt.subplots(figsize=(14, 6))

    # Stacked area plot
    ax.stackplot(
        df['cycle'],
        df['D_materiel'],
        df['D_services'],
        df['D_engagement'],
        df['D_regulateur'],
        labels=['Material', 'Services', 'Engagement', 'Regulator'],
        alpha=0.7
    )

    ax.set_xlabel('Cycle')
    ax.set_ylabel('Debt (D)')
    ax.set_title('RAD Debt Segmentation')
    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'rad_sectors.png'))
    plt.close()
