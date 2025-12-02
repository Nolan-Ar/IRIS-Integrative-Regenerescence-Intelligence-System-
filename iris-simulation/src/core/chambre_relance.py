"""
IRIS Simulation - Chambre de Relance
Recycles 1-3★ goods from deceased agents
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .bien import Bien
    from .rad import RAD


class ChambreRelance:
    """
    Chambre de Relance (Recovery Chamber)

    Recycles low-value goods (1-3★) from deceased agents.

    Simplified implementation:
    - Goods are destroyed (not reintroduced to market)
    - Value creates debt in RAD secteur 'regulateur'
    - This simulates the thermodynamic recycling process
    """

    def __init__(self):
        self.total_recycled_value: float = 0.0
        self.total_recycled_count: int = 0

    def recycler_bien(self, bien: 'Bien', rad: 'RAD') -> None:
        """
        Recycle a 1-3★ good

        Process:
        1. Destroy the good (remove from circulation)
        2. Add its value to RAD as 'regulateur' debt
        3. Track statistics

        Args:
            bien: Good to recycle (must be 1-3★)
            rad: RAD instance
        """
        if bien.etoiles >= 4:
            raise ValueError(f"Chambre de Relance only handles 1-3★ goods, got {bien.etoiles}★")

        # Add to RAD regulator debt
        rad.add_debt(bien.valeur_V, secteur='regulateur')

        # Update statistics
        self.total_recycled_value += bien.valeur_V
        self.total_recycled_count += 1

        # Good is implicitly destroyed (not stored anywhere)

    def get_statistics(self) -> dict:
        """
        Get recycling statistics

        Returns:
            Dictionary with statistics
        """
        return {
            'total_recycled_count': self.total_recycled_count,
            'total_recycled_value': self.total_recycled_value,
            'average_value': (
                self.total_recycled_value / self.total_recycled_count
                if self.total_recycled_count > 0 else 0
            )
        }
