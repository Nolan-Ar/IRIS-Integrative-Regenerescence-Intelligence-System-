"""
IRIS Simulation - Chambre de Relance
Recycles 1-3★ goods from deceased agents and redistributes them
"""

import random
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from .agent import Agent
    from .bien import Bien
    from .rad import RAD


class ChambreRelance:
    """
    Chambre de Relance (Recovery Chamber)

    Enhanced implementation:
    - Stores recycled 1-3★ goods (not destroyed)
    - Periodically redistributes to poor agents
    - Reduces D_regulateur when goods are successfully redistributed
    """

    def __init__(self):
        self.total_recycled_value: float = 0.0
        self.total_recycled_count: int = 0
        self.stock_biens: List['Bien'] = []  # ✓ Store recycled goods

    def recycler_bien(self, bien: 'Bien', rad: 'RAD') -> None:
        """
        Recycle a 1-3★ good

        Process:
        1. Store good in recycling stock
        2. Add its value to RAD as 'regulateur' debt (temporary)
        3. Track statistics
        """
        if bien.etoiles >= 4:
            raise ValueError(f"Chambre de Relance only handles 1-3★ goods, got {bien.etoiles}★")

        # Store good for future redistribution
        self.stock_biens.append(bien)

        # Add to RAD regulator debt (will be reduced upon redistribution)
        rad.add_debt(bien.valeur_V, secteur='regulateur')

        # Update statistics
        self.total_recycled_value += bien.valeur_V
        self.total_recycled_count += 1

    def redistribuer_biens(
        self,
        agents: List['Agent'],
        rad: 'RAD',
        max_per_cycle: int = 10
    ) -> float:
        """
        Redistribute recycled goods to poor agents

        Process:
        1. Select agents with low patrimony (bottom 30%)
        2. Transfer goods from stock to agents
        3. Reduce D_regulateur accordingly

        Args:
            agents: List of all agents
            rad: RAD instance
            max_per_cycle: Max goods to redistribute per cycle

        Returns:
            Total value redistributed
        """
        if not self.stock_biens:
            return 0.0

        # Filter living agents
        vivants = [a for a in agents if a.alive]
        if not vivants:
            return 0.0

        # Sort by total patrimony (ascending)
        vivants_tries = sorted(
            vivants,
            key=lambda a: a.wallet_V + sum(b.valeur_V for b in a.biens)
        )

        # Select poorest 30% as beneficiaries
        nb_beneficiaires = max(1, len(vivants_tries) // 3)
        beneficiaires = vivants_tries[:nb_beneficiaires]

        # Redistribute up to max_per_cycle goods
        V_redistribue = 0.0
        nb_redistribue = 0

        while self.stock_biens and nb_redistribue < max_per_cycle and beneficiaires:
            # Pick a random poor agent
            beneficiaire = random.choice(beneficiaires)

            # Pick first good from stock (FIFO)
            bien = self.stock_biens.pop(0)

            # Transfer good to beneficiary
            beneficiaire.biens.append(bien)

            # Reduce D_regulateur (debt is "paid back" by redistribution)
            rad.add_debt(-bien.valeur_V, secteur='regulateur')

            V_redistribue += bien.valeur_V
            nb_redistribue += 1

        return V_redistribue

    def get_statistics(self) -> dict:
        """Get recycling and redistribution statistics"""
        return {
            'total_recycled_count': self.total_recycled_count,
            'total_recycled_value': self.total_recycled_value,
            'stock_size': len(self.stock_biens),
            'stock_value': sum(b.valeur_V for b in self.stock_biens),
            'average_value': (
                self.total_recycled_value / self.total_recycled_count
                if self.total_recycled_count > 0 else 0
            )
        }
