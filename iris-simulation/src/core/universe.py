"""
IRIS Simulation - Universe (Revenu Universel)
Distributes Universal Income (RU) to all living agents
"""

from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from .agent import Agent
    from .rad import RAD


class Universe:
    """
    Manages Universal Income (RU) distribution

    RU is distributed monthly to all living agents
    Formula: RU = (V_ON / N) × κ × facteur × (1 - stress) × R_t

    With smoothing constraint: |RU_t - RU_{t-1}| ≤ α × RU_{t-1}
    """

    def __init__(self):
        self.facteur_redistribution = 0.05  # 5% of V_ON per cycle
        self.alpha_lissage = 0.10  # Max 10% variation per cycle
        self.RU_base_precedent = 0.0  # Memory of previous RU for smoothing

    def calculate_RU_base(
        self,
        V_ON: float,
        population: int,
        D_total: float,
        kappa: float,  # ✓ CRITICAL ADDITION
        R_t: float = 1.0  # Activity flux (simplified to 1.0 for now)
    ) -> float:
        """
        Calculate base Universal Income for the cycle

        Formula (from protocol section 3.2.2):
        RU_base = (V_ON / N) × facteur × κ × (1 - stress) × R_t

        With smoothing (Proposition 3.14):
        |RU_t - RU_{t-1}| ≤ α × RU_{t-1} where α = 0.1 (10%)

        Args:
            V_ON: Total active Verum
            population: Number of living agents
            D_total: Total debt
            kappa: Liquidity regulator (CRITICAL: modulates V→U conversion)
            R_t: Real activity flux (default 1.0)

        Returns:
            Base RU amount per agent (smoothed)
        """
        if population == 0:
            return 0

        # Calculate thermometric stress: stress = min(0.5, |D/V - 1|)
        if V_ON > 0:
            stress_thermique = min(0.5, abs((D_total / V_ON) - 1.0))
        else:
            stress_thermique = 0.5

        # Raw RU calculation WITH κ (CRITICAL)
        # κ > 1 → facilitation → more U distributed
        # κ < 1 → restriction → less U distributed
        RU_brut = (
            (V_ON / population) *
            self.facteur_redistribution *
            kappa *  # ✓ CRITICAL: κ modulates V→U conversion
            (1 - stress_thermique) *
            R_t
        )

        # Apply smoothing constraint: max ±10% change
        if self.RU_base_precedent > 0:
            delta_max = self.alpha_lissage * self.RU_base_precedent
            RU_lisse = max(
                self.RU_base_precedent - delta_max,
                min(self.RU_base_precedent + delta_max, RU_brut)
            )
        else:
            # First cycle: no previous RU to smooth from
            RU_lisse = RU_brut

        # Store for next cycle
        self.RU_base_precedent = RU_lisse

        # Ensure minimum vital RU
        return max(10.0, RU_lisse)

    def distribute_RU(
        self,
        agents: List['Agent'],
        cycle: int,
        V_ON: float,
        rad: 'RAD',
        kappa: float,  # ✓ ADDED
        eta_global: float = 1.0
    ) -> float:
        """
        Distribute Universal Income to all living agents

        Each agent receives: RU_individual = RU_base × η_agent × η_global

        Args:
            agents: List of all agents
            cycle: Current cycle number
            V_ON: Total active Verum
            rad: RAD instance for debt calculation
            kappa: Liquidity regulator (CRITICAL)
            eta_global: Global productivity coefficient from Exchange

        Returns:
            Total RU distributed
        """
        living_agents = [a for a in agents if a.alive]
        population = len(living_agents)

        if population == 0:
            return 0

        # Calculate base RU WITH κ
        D_total = rad.get_total()
        RU_base = self.calculate_RU_base(V_ON, population, D_total, kappa)

        # Distribute to each living agent
        total_distribue = 0
        for agent in living_agents:
            # Individual RU modulated by η_agent AND η_global
            RU_agent = RU_base * agent.eta * eta_global
            agent.wallet_U += RU_agent
            total_distribue += RU_agent

        return total_distribue

    def calculate_RU_statistics(self, agents: List['Agent'], RU_base: float) -> dict:
        """Calculate RU distribution statistics"""
        living = [a for a in agents if a.alive]

        if not living:
            return {
                'RU_base': 0,
                'RU_min': 0,
                'RU_max': 0,
                'RU_mean': 0,
                'RU_median': 0
            }

        RU_amounts = [RU_base * a.eta for a in living]

        return {
            'RU_base': RU_base,
            'RU_min': min(RU_amounts),
            'RU_max': max(RU_amounts),
            'RU_mean': sum(RU_amounts) / len(RU_amounts),
            'RU_median': sorted(RU_amounts)[len(RU_amounts) // 2]
        }
