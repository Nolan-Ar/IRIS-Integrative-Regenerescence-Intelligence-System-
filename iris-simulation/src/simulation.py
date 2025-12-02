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
            'S_burn_total': 0
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

        # 2. Calculate sensors and regulate κ, η
        r_ic, nu_eff, tau_eng = self.exchange.calculer_capteurs(
            self.agents, self.entreprises, self.rad, self.cycle_data
        )

        r_thermo = self.rad.get_ratio(V_ON)

        eta_global, kappa = self.exchange.ajuster_parametres(
            r_ic, nu_eff, tau_eng, r_thermo
        )

        # 3. Distribute Universal Income
        RU_total = self.universe.distribute_RU(
            self.agents, cycle_num, V_ON, self.rad
        )

        # 4. Agent actions
        U_burn_total = 0
        for agent in self.agents:
            if agent.alive:
                U_spent = decide_agent_actions(
                    agent, cycle_num, self.entreprises,
                    self.chambre_memorielle, kappa,
                    self.catalogue_biens, self.rad
                )
                U_burn_total += U_spent

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

        # 6. Finalize staking contracts
        self.chambre_memorielle.finaliser_contrats(cycle_num, self.rad)

        # 7. Burn unused U (perishability)
        for agent in self.agents:
            if agent.alive:
                agent.wallet_U = 0  # All U burned at cycle end

        # 8. Demographics
        deaths, births = self._gerer_demographie(cycle_num)

        # 9. Apply RAD monthly amortization
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
        self.cycle_data = {
            'V_ON_prev': V_ON,
            'U_burn_total': U_burn_total,
            'S_burn_total': U_burn_total  # Simplified: S ≈ U
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

                # Recycle patrimony
                for bien in agent.biens:
                    if bien.etoiles >= 4:
                        self.chambre_memorielle.ajouter_bien(bien)
                    else:
                        self.chambre_relance.recycler_bien(bien, self.rad)

                # Add patrimony to RAD as regulator debt
                patrimoine_total = agent.wallet_V + sum(
                    b.valeur_V for b in agent.biens
                )
                if patrimoine_total > 0:
                    self.rad.add_debt(patrimoine_total, secteur='regulateur')

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
