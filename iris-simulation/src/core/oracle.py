"""
IRIS Simulation - Oracle d'initialisation
Initializes the system with thermodynamic equilibrium D₀ = V₀
"""

import random
from typing import Tuple, List

from .agent import Agent, creer_agent
from .bien import Bien, generer_catalogue_biens
from .rad import RAD


class Oracle:
    """
    Oracle d'initialisation

    Responsibilities:
    1. Create economic agents with initial wealth distribution
    2. Generate goods catalog
    3. Initialize RAD with D₀ = V₀ (thermodynamic equilibrium)
    """

    def __init__(self, config: dict):
        """
        Initialize Oracle with configuration

        Args:
            config: Configuration dictionary with keys:
                - agents: Number of agents
                - v_total: Total Verum to distribute
                - entreprises_ratio: Ratio of agents with enterprises
                - distribution: Distribution type ('pareto_80_20', 'equal')
                - seed: Random seed (optional)
        """
        self.config = config
        self.agents: List[Agent] = []
        self.rad = RAD()
        self.catalogue_biens: List[Bien] = []

        # Set random seed if provided
        if config.get('seed'):
            random.seed(config['seed'])

    def initialize(self) -> Tuple[List[Agent], RAD, List[Bien]]:
        """
        Complete initialization sequence

        Returns:
            Tuple of (agents, rad, catalogue_biens)
        """
        print("=== ORACLE INITIALIZATION ===")

        # Step 1: Create agents
        print(f"Creating {self.config['agents']} agents...")
        self._creer_agents()

        # Step 2: Distribute patrimony
        print(f"Distributing V_total={self.config['v_total']} with {self.config['distribution']}...")
        self._distribuer_patrimoine()

        # Step 3: Initialize RAD with D₀ = V₀
        print("Initializing RAD with D₀ = V₀...")
        self._initialiser_rad()

        # Step 4: Generate goods catalog
        print("Generating goods catalog...")
        self.catalogue_biens = generer_catalogue_biens(self.config['v_total'])

        # Verification
        V_total = sum(a.wallet_V for a in self.agents)
        D_total = self.rad.get_total()
        print(f"\n✓ Initialization complete:")
        print(f"  Agents: {len(self.agents)}")
        print(f"  V₀ total: {V_total:.2f}")
        print(f"  D₀ total: {D_total:.2f}")
        print(f"  |V₀ - D₀|: {abs(V_total - D_total):.6f}")
        print(f"  Goods catalog: {len(self.catalogue_biens)} items")

        # Assert equilibrium
        assert abs(V_total - D_total) < 0.01, \
            f"Initialization failed: V₀={V_total} != D₀={D_total}"

        return self.agents, self.rad, self.catalogue_biens

    def _creer_agents(self) -> None:
        """Create economic agents with optional enterprises"""
        n_agents = self.config['agents']
        entreprises_ratio = self.config.get('entreprises_ratio', 0.3)
        n_entreprises = int(n_agents * entreprises_ratio)

        # Create agents with enterprises (30%)
        for i in range(n_entreprises):
            agent = creer_agent(avec_entreprise=True)
            self.agents.append(agent)

        # Create simple agents (70%)
        for i in range(n_agents - n_entreprises):
            agent = creer_agent(avec_entreprise=False)
            self.agents.append(agent)

        # Shuffle to mix agents with/without enterprises
        random.shuffle(self.agents)

    def _distribuer_patrimoine(self) -> None:
        """
        Distribute initial patrimony according to specified distribution

        Supports:
        - 'pareto_80_20': 20% of agents receive 80% of wealth
        - 'equal': Equal distribution
        """
        V_total = self.config['v_total']
        distribution = self.config.get('distribution', 'pareto_80_20')

        if distribution == 'pareto_80_20':
            self._distribuer_pareto(V_total)
        elif distribution == 'equal':
            self._distribuer_equal(V_total)
        else:
            raise ValueError(f"Unknown distribution: {distribution}")

    def _distribuer_pareto(self, V_total: float) -> None:
        """
        Pareto distribution: 20% of agents → 80% of wealth
                            80% of agents → 20% of wealth

        Args:
            V_total: Total Verum to distribute
        """
        n = len(self.agents)
        top_20_percent = int(n * 0.2)

        # Shuffle agents for randomness
        shuffled = self.agents.copy()
        random.shuffle(shuffled)

        # Top 20% receives 80% of V
        V_top = V_total * 0.8
        for i in range(top_20_percent):
            shuffled[i].wallet_V = V_top / top_20_percent

        # Bottom 80% receives 20% of V
        V_bottom = V_total * 0.2
        for i in range(top_20_percent, n):
            shuffled[i].wallet_V = V_bottom / (n - top_20_percent)

    def _distribuer_equal(self, V_total: float) -> None:
        """
        Equal distribution: Each agent receives V_total / N

        Args:
            V_total: Total Verum to distribute
        """
        n = len(self.agents)
        V_per_agent = V_total / n

        for agent in self.agents:
            agent.wallet_V = V_per_agent

    def _initialiser_rad(self) -> None:
        """
        Initialize RAD with D₀ = V₀

        Critical: Protocol requires ΣV₀ = ΣD₀ for thermodynamic equilibrium
        All initial V is mirrored as material debt
        """
        # Sum all agent wealth
        V_total = sum(a.wallet_V for a in self.agents)

        # Mirror as material debt in RAD
        self.rad.add_debt(V_total, secteur='materiel')

        # Verification
        assert abs(self.rad.get_total() - V_total) < 0.01, \
            "RAD initialization failed: D₀ != V₀"
