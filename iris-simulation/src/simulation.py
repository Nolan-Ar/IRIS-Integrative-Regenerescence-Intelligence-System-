"""
IRIS Simulation - Main Simulation Engine
Orchestrates the complete economic simulation
"""

import random
import math
from typing import List, Dict, Any

from core.oracle import Oracle
from core.agent import Agent, Entreprise, creer_agent
from core.bien import Bien
from core.rad import RAD
from core.exchange import Exchange
from core.universe import Universe
from core.chambre_memorielle import ChambreMemorielle
from core.chambre_relance import ChambreRelance
from core.behaviors import (
    decide_agent_actions,
    gerer_entreprise,
    calculer_probabilite_deces
)


class Simulation:
    """
    Main IRIS Economic Simulation

    Simulates a complete thermodynamic economic system over multiple cycles
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize simulation

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.agents: List[Agent] = []
        self.entreprises: List[Entreprise] = []
        self.rad = RAD()
        self.exchange = Exchange()
        self.universe = Universe()
        self.chambre_memorielle = ChambreMemorielle()
        self.chambre_relance = ChambreRelance()
        self.catalogue_biens: List[Bien] = []

        # Metrics collector (will be initialized later)
        self.metrics = None

        # Cycle data (for sensor calculations)
        self.cycle_data = {
            'V_ON_prev': 0,
            'U_burn_total': 0,
            'S_burn_total': 0,
            'RU_total': 0,
            'U_stake_flow': 0
        }

    def run(self) -> None:
        """Execute complete simulation"""
        print("\n" + "=" * 60)
        print("IRIS ECONOMIC SIMULATION")
        print("=" * 60)

        # Initialize
        self._initialize()

        # Import metrics
        from analysis.metrics import MetricsCollector
        self.metrics = MetricsCollector()

        # Run simulation cycles
        print(f"\n{'=' * 60}")
        print(f"RUNNING SIMULATION: {self.config['cycles']} cycles")
        print("=" * 60)

        for cycle in range(self.config['cycles']):
            self._execute_cycle(cycle)

            # Progress display every 12 cycles (1 year)
            if cycle % 12 == 0 or cycle == self.config['cycles'] - 1:
                self._print_status(cycle)

        # Save results
        self._save_results()

        print(f"\n{'=' * 60}")
        print("SIMULATION COMPLETE")
        print("=" * 60)

    def _initialize(self) -> None:
        """Initialize simulation using Oracle"""
        oracle = Oracle(self.config)
        self.agents, self.rad, self.catalogue_biens = oracle.initialize()

        # Extract enterprises from agents
        self.entreprises = [a.entreprise for a in self.agents if a.entreprise]

        # Initialize cycle data
        self.cycle_data['V_ON_prev'] = self.exchange.calculer_V_ON(
            self.agents, self.entreprises
        )

    def _execute_cycle(self, cycle_num: int) -> None:
        """
        Execute one simulation cycle (1 month)

        Sequence:
        1. Age increment (yearly)
        2. Calculate κ and η
        3. Distribute Universal Income
        4. Agent actions (staking, investment, consumption)
        5. Enterprise management
        6. Finalize staking contracts
        7. Burn unused U (perishability)
        8. Demographics (deaths, births)
        9. Collect metrics
        """
        # 0. Age increment (yearly)
        if cycle_num % 12 == 0:
            for agent in self.agents:
                if agent.alive:
                    agent.age += 1

        # 1. Calculate V_ON
        V_ON = self.exchange.calculer_V_ON(self.agents, self.entreprises)

        # 1a. ✓ CORRECTION 4: Recalibrate goods catalog every year
        if cycle_num % 12 == 0 and cycle_num > 0:
            # Store initial V_ON for reference (first time only)
            if not hasattr(self, 'V_ON_initial'):
                self.V_ON_initial = V_ON

            from .core.bien import recalibrer_catalogue
            recalibrer_catalogue(
                self.catalogue_biens,
                V_ON,
                self.V_ON_initial
            )

        # 1b. Automatic debt stabilizer when D/V > 1.5
        # Reinforces amortization to prevent debt explosion
        r = self.rad.get_ratio(V_ON)
        if r > 1.5:
            # Reduce 10% of excess debt (D - V)
            montant = (self.rad.get_total() - V_ON) * 0.1
            self.rad.add_debt(-montant, secteur="regulateur")

        # 2. Calculate sensors and regulate κ, η
        r_ic, nu_eff, tau_eng = self.exchange.calculer_capteurs(
            self.agents, self.entreprises, self.rad, self.cycle_data
        )

        r_thermo = self.rad.get_ratio(V_ON)

        eta_global, kappa = self.exchange.ajuster_parametres(
            r_ic, nu_eff, tau_eng, r_thermo
        )

        # 3. Distribute Universal Income WITH κ
        RU_total = self.universe.distribute_RU(
            self.agents, cycle_num, V_ON, self.rad, kappa, eta_global
        )

        # 4. Agent actions
        U_burn_total = 0.0
        U_stake_nouveaux = 0.0  # ✓ Only NEW staking contracts
        S_burn_total = 0.0
        for agent in self.agents:
            if agent.alive:
                spending = decide_agent_actions(
                    agent, cycle_num, self.entreprises,
                    self.chambre_memorielle, kappa,
                    self.catalogue_biens, self.rad, eta_global
                )
                U_burn_total += spending['total']
                U_stake_nouveaux += spending['staking']  # ✓ NEW contracts only

                # Effort S explicite pour cet agent
                S_burn_total += self._calculer_effort_S_agent(agent, spending)

        # 5. Enterprise management
        V_salaries_total = 0
        V_burned_total = 0
        for entreprise in self.entreprises:
            if entreprise.owner.alive:
                V_sal, V_burn = gerer_entreprise(
                    entreprise, cycle_num, self.agents
                )
                V_salaries_total += V_sal
                V_burned_total += V_burn

        # 6. Finalize staking contracts (collect monthly payments)
        # Note: These are NOT counted in τ_eng (only new engagements count)
        _, U_staking_payments = self.chambre_memorielle.finaliser_contrats(cycle_num, self.rad)
        # Do NOT add to U_stake_nouveaux (τ_eng only counts NEW commitments)

        # 7. Burn unused U (perishability)
        for agent in self.agents:
            if agent.alive:
                agent.wallet_U = 0  # All U burned at cycle end

        # 8. Demographics
        deaths, births = self._gerer_demographie(cycle_num)

        # 9. ✓ CORRECTION 3: Redistribution from Chambre de Relance
        # Redistribute recycled goods to poor agents, reducing D_regulateur
        V_redistribue = self.chambre_relance.redistribuer_biens(
            self.agents,
            self.rad,
            max_per_cycle=10  # Redistribute 10 goods per cycle
        )

        # 10. Apply RAD monthly amortization
        self.rad.apply_monthly_amortization()

        # 10. Collect metrics
        if self.metrics:
            self.metrics.record_cycle(
                cycle=cycle_num,
                agents=self.agents,
                entreprises=self.entreprises,
                kappa=kappa,
                eta=eta_global,
                rad=self.rad,
                V_ON=V_ON,
                RU_total=RU_total,
                U_burn=U_burn_total,
                V_burned=V_burned_total,
                V_salaries=V_salaries_total,
                deaths=deaths,
                births=births,
                r_ic=r_ic,
                nu_eff=nu_eff,
                tau_eng=tau_eng
            )

        # Update cycle data for next iteration
        # S_burn_total was calculated during agent actions loop
        self.cycle_data = {
            'V_ON_prev': V_ON,
            'U_burn_total': U_burn_total,
            'S_burn_total': S_burn_total,  # Explicit effort calculation
            'RU_total': RU_total,
            'U_stake_flow': U_stake_nouveaux  # ✓ Only NEW engagements
        }

    def _gerer_demographie(self, cycle: int) -> tuple[int, int]:
        """
        Manage demographics: deaths and births

        Args:
            cycle: Current cycle number

        Returns:
            Tuple of (number of deaths, number of births)
        """
        # Process deaths
        deces = []
        for agent in self.agents:
            if agent.alive and random.random() < calculer_probabilite_deces(agent):
                agent.alive = False
                deces.append(agent)

                # ✓ CORRECTION 1: Track recycled value to avoid double counting
                biens_recycles_V = 0.0

                # Recycle patrimony
                for bien in agent.biens:
                    if bien.etoiles >= 4:
                        # High-value goods → Chambre Mémorielle
                        self.chambre_memorielle.ajouter_bien(bien)
                    else:
                        # Low-value goods → Chambre de Relance
                        self.chambre_relance.recycler_bien(bien, self.rad)
                        biens_recycles_V += bien.valeur_V  # ✓ Track recycled value

                # Calculate net patrimony EXCLUDING already recycled goods
                # Only count: wallet V + high-value goods (4-5★) - debt
                patrimoine_V_wallet = agent.wallet_V
                patrimoine_V_haute_valeur = sum(
                    b.valeur_V for b in agent.biens if b.etoiles >= 4
                )
                dette_agent = sum(
                    c.montant_total for c in agent.contrats_staking
                )

                patrimoine_net = (
                    patrimoine_V_wallet +
                    patrimoine_V_haute_valeur -
                    dette_agent
                )

                # Only add positive net patrimony
                # Low-value goods (1-3★) were already counted in recycler_bien()
                if patrimoine_net > 0:
                    self.rad.add_debt(patrimoine_net, secteur='regulateur')

        # Process births (slightly higher than deaths for growth)
        taux_mortalite = len(deces) / len([a for a in self.agents if a.alive]) if self.agents else 0
        facteur_croissance = 1.01  # +1% growth
        nb_naissances = int(
            len([a for a in self.agents if a.alive]) *
            taux_mortalite *
            facteur_croissance
        )

        # Create new agents
        nouveaux_agents = []
        for _ in range(nb_naissances):
            # 30% chance of having an enterprise
            avec_entreprise = random.random() < 0.3
            agent = creer_agent(age=18, avec_entreprise=avec_entreprise)
            nouveaux_agents.append(agent)
            self.agents.append(agent)

            if agent.entreprise:
                self.entreprises.append(agent.entreprise)

        return len(deces), len(nouveaux_agents)

    def _calculer_effort_S_agent(self, agent: Agent, spending: dict) -> float:
        """
        Calculate effort S for a single agent this cycle

        Approach:
        - Effort is proportional to U spent by the agent
        - Weighted by agent aptitudes 'croissance' and 'social_up'
        - Different spending types have different effort weights:
          * staking (long-term commitment): 1.2×
          * investment (entrepreneurial effort): 1.0×
          * consumption (immediate satisfaction): 0.6×

        This distinguishes monetary spending (U) from actual effort (S),
        preparing for thermodynamic model where ΔV = η × f(U, S)

        Args:
            agent: Agent whose effort to calculate
            spending: Dictionary with keys 'staking', 'investment', 'consumption', 'total'

        Returns:
            Total effort S burned by this agent

        TODO: Refine weights based on empirical simulation results
        """
        if not agent.alive:
            return 0.0

        # Normalize aptitudes to [0, 1]
        croissance = agent.aptitudes['croissance'] / 100.0
        social_up = agent.aptitudes['social_up'] / 100.0

        # Agent effort factor: higher 'croissance' and 'social_up' mean
        # more of their U spending translates to actual effort
        # Range: [0.5, 1.0]
        facteur_agent = 0.5 + 0.5 * (croissance + social_up) / 2.0

        # Extract spending by type
        U_staking = spending.get('staking', 0.0)
        U_invest = spending.get('investment', 0.0)
        U_conso = spending.get('consumption', 0.0)

        # Effort weights by spending type
        poids_staking = 1.2   # Long-term commitment requires more effort
        poids_invest = 1.0    # Entrepreneurial investment is baseline effort
        poids_conso = 0.6     # Consumption requires less effort

        # Calculate effort by type
        S_staking = U_staking * poids_staking
        S_invest = U_invest * poids_invest
        S_conso = U_conso * poids_conso

        # Total agent effort modulated by aptitudes
        S_total_agent = (S_staking + S_invest + S_conso) * facteur_agent
        return S_total_agent

    def _print_status(self, cycle: int) -> None:
        """Print current simulation status"""
        vivants = [a for a in self.agents if a.alive]
        V_total = sum(a.wallet_V for a in vivants)
        D_total = self.rad.get_total()
        ratio_D_V = self.rad.get_ratio(V_total)

        # Calculate Gini
        patrimoines = [
            a.wallet_V + sum(b.valeur_V for b in a.biens)
            for a in vivants
        ]
        gini = self._calculate_gini(patrimoines)

        print(f"\n--- Cycle {cycle}/{self.config['cycles']} " +
              f"(Year {cycle // 12}) ---")
        print(f"  Population: {len(vivants)} living agents")
        print(f"  Enterprises: {len([e for e in self.entreprises if e.owner.alive])}")
        print(f"  V_total: {V_total:.2f}")
        print(f"  D_total: {D_total:.2f}")
        print(f"  D/V ratio: {ratio_D_V:.4f}")
        print(f"  κ: {self.exchange.kappa:.4f}")
        print(f"  η: {self.exchange.eta_global:.4f}")
        print(f"  Gini: {gini:.4f}")

    def _calculate_gini(self, values: List[float]) -> float:
        """Calculate Gini coefficient"""
        if not values or sum(values) == 0:
            return 0

        import numpy as np
        sorted_values = np.sort(values)
        n = len(values)
        index = np.arange(1, n + 1)
        return (2 * np.sum(index * sorted_values)) / (n * np.sum(sorted_values)) - (n + 1) / n

    def _save_results(self) -> None:
        """Save simulation results"""
        import os
        from datetime import datetime

        # Create output directory
        output_dir = self.config.get('output')
        if not output_dir:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_dir = f"data/runs/run_{timestamp}"

        os.makedirs(output_dir, exist_ok=True)

        print(f"\nSaving results to: {output_dir}")

        # Save metrics
        if self.metrics:
            metrics_path = os.path.join(output_dir, 'metrics.csv')
            self.metrics.save(metrics_path)
            print(f"  ✓ Metrics saved: {metrics_path}")

            # Generate plots if requested
            if self.config.get('generate_plots', True):
                from analysis.plots import generate_all_plots
                df = self.metrics.to_dataframe()
                generate_all_plots(df, output_dir)
                print(f"  ✓ Plots generated in: {output_dir}")

        print(f"\n✓ Simulation results saved successfully")
