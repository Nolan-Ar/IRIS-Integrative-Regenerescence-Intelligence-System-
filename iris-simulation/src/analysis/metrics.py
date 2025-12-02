"""
IRIS Simulation - Metrics Collection
Collects and stores all simulation indicators
"""

from typing import List, TYPE_CHECKING
import numpy as np
import pandas as pd

if TYPE_CHECKING:
    from ..core.agent import Agent, Entreprise
    from ..core.rad import RAD


class MetricsCollector:
    """
    Collects metrics at each simulation cycle

    Tracks:
    - Thermodynamic indicators (V, U, D, ratios)
    - Distribution indicators (Gini, top shares)
    - Demographics (population, age)
    - Economic flows (RU, burns, salaries)
    - Regulation parameters (κ, η, sensors)
    """

    def __init__(self):
        self.timeseries: List[dict] = []

    def record_cycle(
        self,
        cycle: int,
        agents: List['Agent'],
        entreprises: List['Entreprise'],
        kappa: float,
        eta: float,
        rad: 'RAD',
        V_ON: float,
        RU_total: float,
        U_burn: float,
        V_burned: float,
        V_salaries: float,
        deaths: int,
        births: int,
        r_ic: float,
        nu_eff: float,
        tau_eng: float
    ) -> None:
        """Record all metrics for a cycle"""

        agents_vivants = [a for a in agents if a.alive]

        # Calculate patrimony distribution
        patrimoines = [
            a.wallet_V + sum(b.valeur_V for b in a.biens)
            for a in agents_vivants
        ]

        # Distribution metrics
        gini = self._calculate_gini(patrimoines)
        top10_share = self._calculate_top_share(patrimoines, 0.1)
        top20_share = self._calculate_top_share(patrimoines, 0.2)
        median_wealth = np.median(patrimoines) if patrimoines else 0

        # Productivity
        eta_mean = np.mean([a.eta for a in agents_vivants]) if agents_vivants else 1.0
        eta_std = np.std([a.eta for a in agents_vivants]) if agents_vivants else 0

        # Age statistics
        ages = [a.age for a in agents_vivants]
        age_median = np.median(ages) if ages else 0
        age_mean = np.mean(ages) if ages else 0

        # RAD breakdown
        rad_breakdown = rad.get_sector_breakdown()

        # Compile metrics
        metrics = {
            # Cycle info
            'cycle': cycle,
            'year': cycle // 12,

            # Thermodynamic
            'V_total': sum(a.wallet_V for a in agents_vivants),
            'U_circ': sum(a.wallet_U for a in agents_vivants),
            'D_total': rad.get_total(),
            'ratio_D_V': rad.get_ratio(V_ON),
            'kappa': kappa,
            'eta_global': eta,
            'V_ON': V_ON,

            # Distribution
            'gini': gini,
            'top10_share': top10_share,
            'top20_share': top20_share,
            'median_wealth': median_wealth,
            'mean_wealth': np.mean(patrimoines) if patrimoines else 0,
            'eta_mean': eta_mean,
            'eta_std': eta_std,

            # Demographics
            'population': len(agents_vivants),
            'entreprises': len([e for e in entreprises if e.owner.alive]),
            'age_median': age_median,
            'age_mean': age_mean,
            'deaths': deaths,
            'births': births,

            # Flows
            'RU_total': RU_total,
            'U_burn': U_burn,
            'V_burned': V_burned,
            'V_salaries': V_salaries,
            'staking_volume': sum(len(a.contrats_staking) for a in agents_vivants),

            # Sensors
            'r_ic': r_ic,
            'nu_eff': nu_eff,
            'tau_eng': tau_eng,

            # RAD sectors
            'D_materiel': rad_breakdown['materiel'],
            'D_services': rad_breakdown['services'],
            'D_contractuel': rad_breakdown['contractuel'],
            'D_engagement': rad_breakdown['engagement'],
            'D_regulateur': rad_breakdown['regulateur'],
        }

        self.timeseries.append(metrics)

    def _calculate_gini(self, values: List[float]) -> float:
        """Calculate Gini coefficient"""
        if not values or sum(values) == 0:
            return 0

        sorted_values = np.sort(values)
        n = len(values)
        index = np.arange(1, n + 1)

        return (2 * np.sum(index * sorted_values)) / (n * np.sum(sorted_values)) - (n + 1) / n

    def _calculate_top_share(self, values: List[float], percentile: float) -> float:
        """Calculate wealth share of top X%"""
        if not values:
            return 0

        sorted_values = sorted(values, reverse=True)
        top_n = max(1, int(len(sorted_values) * percentile))
        total = sum(sorted_values)

        if total == 0:
            return 0

        return sum(sorted_values[:top_n]) / total

    def to_dataframe(self) -> pd.DataFrame:
        """Convert metrics to pandas DataFrame"""
        return pd.DataFrame(self.timeseries)

    def save(self, filepath: str) -> None:
        """Save metrics to CSV"""
        df = self.to_dataframe()
        df.to_csv(filepath, index=False)

    def get_summary(self) -> dict:
        """Get summary statistics"""
        if not self.timeseries:
            return {}

        df = self.to_dataframe()

        return {
            'total_cycles': len(self.timeseries),
            'final_population': self.timeseries[-1]['population'],
            'final_gini': self.timeseries[-1]['gini'],
            'final_ratio_D_V': self.timeseries[-1]['ratio_D_V'],
            'mean_ratio_D_V': df['ratio_D_V'].mean(),
            'std_ratio_D_V': df['ratio_D_V'].std(),
            'mean_kappa': df['kappa'].mean(),
            'mean_eta': df['eta_global'].mean(),
            'convergence_last_12': abs(df['ratio_D_V'].iloc[-12:].mean() - 1.0) < 0.1
        }
