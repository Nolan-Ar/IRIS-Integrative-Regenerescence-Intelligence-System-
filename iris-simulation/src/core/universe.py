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
    Amount is modulated by individual η
    """

    def __init__(self):
        self.facteur_redistribution = 0.05  # 5% of V_ON per cycle

    def calculate_RU_base(self, V_ON: float, population: int, D_total: float) -> float:
        """
        Calculate base Universal Income for the cycle

        Formula (simplified):
        RU_base = (V_ON / N) × facteur_redistribution × (1 - stress_thermique)

        where stress_thermique = min(0.5, |D/V - 1|)

        Args:
            V_ON: Total active Verum
            population: Number of living agents
            D_total: Total debt

        Returns:
            Base RU amount per agent
        """
        if population == 0:
            return 0

        # Calculate thermometric stress
        if V_ON > 0:
            stress_thermique = min(0.5, abs((D_total / V_ON) - 1.0))
        else:
            stress_thermique = 0.5

        # Base RU formula
        RU_base = (
            (V_ON / population) *
            self.facteur_redistribution *
            (1 - stress_thermique)
        )

        # Ensure minimum vital RU
        return max(10.0, RU_base)

    def distribute_RU(
        self,
        agents: List['Agent'],
        cycle: int,
        V_ON: float,
        rad: 'RAD'
    ) -> float:
        """
        Distribute Universal Income to all living agents

        Each agent receives: RU_individual = RU_base × η_agent

        This modulates RU based on individual productivity coefficient

        Args:
            agents: List of all agents
            cycle: Current cycle number
            V_ON: Total active Verum
            rad: RAD instance for debt calculation

        Returns:
            Total RU distributed
        """
        # Count living agents
        living_agents = [a for a in agents if a.alive]
        population = len(living_agents)

        if population == 0:
            return 0

        # Calculate base RU
        D_total = rad.get_total()
        RU_base = self.calculate_RU_base(V_ON, population, D_total)

        # Distribute to each living agent
        total_distribue = 0
        for agent in living_agents:
            # Individual RU modulated by η
            RU_agent = RU_base * agent.eta
            agent.wallet_U += RU_agent
            total_distribue += RU_agent

        return total_distribue

    def calculate_RU_statistics(self, agents: List['Agent'], RU_base: float) -> dict:
        """
        Calculate RU distribution statistics

        Args:
            agents: List of agents
            RU_base: Base RU amount

        Returns:
            Dictionary with statistics
        """
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
