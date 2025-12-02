"""
IRIS Simulation - Chambre Mémorielle
Manages 4-5★ goods from deceased agents via staking contracts
"""

from typing import List, Optional, TYPE_CHECKING
import uuid

if TYPE_CHECKING:
    from .agent import Agent, ContratStaking
    from .bien import Bien
    from .rad import RAD


class ChambreMemorielle:
    """
    Chambre Mémorielle (Memorial Chamber)

    Manages high-value patrimony (4-5★ goods) from deceased agents.
    Living agents can acquire these goods via long-term staking contracts:
    - 4★: 48 months (12 cycles × 4)
    - 5★: 60 months (12 cycles × 5)

    Payment is monthly from agent's U (Unum)
    Upon completion, good is transferred to agent
    """

    def __init__(self):
        self.stock_biens: List['Bien'] = []  # 4-5★ goods available
        self.contrats_actifs: List['ContratStaking'] = []  # Active contracts

    def ajouter_bien(self, bien: 'Bien') -> None:
        """
        Add a 4-5★ good to the memorial stock

        Args:
            bien: Good with 4 or 5 stars
        """
        if bien.etoiles >= 4:
            self.stock_biens.append(bien)

    def proposer_staking(
        self,
        agent: 'Agent',
        budget: float,
        cycle: int,
        kappa: float,
        rad: 'RAD'
    ) -> bool:
        """
        Propose a staking contract to an agent

        Contract terms:
        - Duration: 12 × stars cycles (48 for 4★, 60 for 5★)
        - Monthly cost: (good_value_V × κ) / duration
        - Total: Paid in U over the duration

        If no goods in stock, a virtual 4-5★ good is created with a high value,
        simulating an initial "enterprise" that provides high-end patrimony.
        This ensures tau_eng > 0 and allows staking dynamics to exist.

        Args:
            agent: Agent requesting staking
            budget: Monthly budget available (in U)
            cycle: Current cycle number
            kappa: Current κ coefficient
            rad: RAD instance (for debt tracking)

        Returns:
            True if contract created, False otherwise
        """
        # If stock is empty, create a virtual 4-5★ good
        # This simulates an initial enterprise providing high-value goods
        # ensuring staking is always possible (tau_eng > 0)
        if not self.stock_biens:
            from .bien import Bien
            import random

            # Randomly choose between 4★ and 5★
            etoiles = random.choice([4, 5])
            valeur_base = self._estimer_valeur_bien_5_etoiles(etoiles)

            bien = Bien(
                id=str(uuid.uuid4()),
                etoiles=etoiles,
                valeur_V=valeur_base,
                type='patrimonial',
                actif=True
            )
        else:
            # Choose affordable good from stock
            bien = self._choisir_bien_adapte(budget, kappa)
            if not bien:
                return False

        # Calculate contract terms
        duree = 12 * bien.etoiles  # 48 cycles for 4★, 60 for 5★
        cout_mensuel = (bien.valeur_V * kappa) / duree
        montant_total = cout_mensuel * duree

        # Verify agent can afford first payment
        if agent.wallet_U < cout_mensuel:
            return False

        # Create contract
        from .agent import ContratStaking
        contrat = ContratStaking(
            id=str(uuid.uuid4()),
            agent=agent,
            bien=bien,
            duree=duree,
            cout_mensuel=cout_mensuel,
            cycle_debut=cycle,
            montant_total=montant_total,
            cycles_payes=0
        )

        # Remove good from stock (only if it was in stock, not a virtual good)
        if bien in self.stock_biens:
            self.stock_biens.remove(bien)

        # Add to active contracts
        self.contrats_actifs.append(contrat)
        agent.contrats_staking.append(contrat)

        # First payment
        agent.wallet_U -= cout_mensuel
        contrat.cycles_payes = 1

        # Add engagement debt to RAD
        rad.add_debt(montant_total, secteur='engagement')

        return True

    def finaliser_contrats(self, cycle: int, rad: 'RAD') -> tuple[List['ContratStaking'], float]:
        """
        Process active contracts:
        - Collect monthly payments
        - Transfer goods when complete
        - Clean up finished contracts

        Args:
            cycle: Current cycle number
            rad: RAD instance

        Returns:
            Tuple of (list of completed contracts, total U collected in payments)
        """
        contrats_termines = []
        U_collected = 0.0

        for contrat in self.contrats_actifs[:]:  # Copy to allow modification
            # Skip if agent is dead
            if not contrat.agent.alive:
                # Contract cancelled - return good to stock
                self.stock_biens.append(contrat.bien)
                self.contrats_actifs.remove(contrat)
                if contrat in contrat.agent.contrats_staking:
                    contrat.agent.contrats_staking.remove(contrat)
                # Reduce debt
                rad.add_debt(-contrat.montant_total, secteur='engagement')
                continue

            # Le premier paiement (cycles_payes=1) a déjà été fait dans proposer_staking()
            # On calcule combien de cycles se sont écoulés depuis le début
            cycles_depuis_debut = cycle - contrat.cycle_debut

            # Si on doit faire un paiement ce cycle (pas le premier)
            if cycles_depuis_debut > 0 and cycles_depuis_debut == contrat.cycles_payes:
                if contrat.agent.wallet_U >= contrat.cout_mensuel:
                    contrat.agent.wallet_U -= contrat.cout_mensuel
                    contrat.cycles_payes += 1
                    U_collected += contrat.cout_mensuel
                else:
                    # Cannot pay - contract defaults (simplified: ignore for now)
                    pass

            # Check if contract is complete
            if contrat.cycles_payes >= contrat.duree:
                # Transfer good to agent
                contrat.agent.biens.append(contrat.bien)
                contrat.agent.contrats_staking.remove(contrat)
                contrats_termines.append(contrat)

                # Reduce engagement debt
                rad.add_debt(-contrat.montant_total, secteur='engagement')

        # Remove completed contracts
        for contrat in contrats_termines:
            if contrat in self.contrats_actifs:
                self.contrats_actifs.remove(contrat)

        return contrats_termines, U_collected

    def _choisir_bien_adapte(self, budget: float, kappa: float) -> Optional['Bien']:
        """
        Choose affordable good based on monthly budget

        Args:
            budget: Monthly budget available
            kappa: Current κ coefficient

        Returns:
            Bien if found, None otherwise
        """
        # Sort by value (ascending)
        sorted_biens = sorted(self.stock_biens, key=lambda b: b.valeur_V)

        for bien in sorted_biens:
            duree = 12 * bien.etoiles
            cout_mensuel = (bien.valeur_V * kappa) / duree

            if cout_mensuel <= budget:
                return bien

        return None

    def _estimer_valeur_bien_5_etoiles(self, etoiles: int = 5) -> float:
        """
        Estimate the value_V of a virtual 4-5★ good

        These virtual goods are expensive compared to the economy,
        simulating an initial specialized enterprise providing high-end patrimony.

        Args:
            etoiles: Star level (4 or 5)

        Returns:
            Estimated valeur_V for the virtual good

        TODO: Refine this calculation based on actual economy metrics
        """
        # Simple implementation: fixed high values
        # These ensure monthly costs are significant but not impossible
        if etoiles == 4:
            return 2000.0  # ~41.67 U/month over 48 cycles at κ=1
        else:  # 5 stars
            return 5000.0  # ~83.33 U/month over 60 cycles at κ=1

    def get_statistics(self) -> dict:
        """
        Get Chambre Mémorielle statistics

        Returns:
            Dictionary with statistics
        """
        return {
            'stock_size': len(self.stock_biens),
            'stock_4_stars': len([b for b in self.stock_biens if b.etoiles == 4]),
            'stock_5_stars': len([b for b in self.stock_biens if b.etoiles == 5]),
            'active_contracts': len(self.contrats_actifs),
            'total_stock_value': sum(b.valeur_V for b in self.stock_biens)
        }
