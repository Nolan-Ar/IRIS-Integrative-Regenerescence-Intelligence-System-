"""
IRIS Simulation - RAD (Régulateur Automatique Décentralisé)
Manages thermometric debt D segmented into 5 sectors
"""

from dataclasses import dataclass, field


@dataclass
class RAD:
    """
    Régulateur Automatique Décentralisé

    Tracks thermometric debt D segmented into 5 components:
    - D_materiel: Material goods and assets
    - D_services: Services and prestations
    - D_contractuel: TAP contracts (not implemented in simplified version)
    - D_engagement: Staking commitments
    - D_regulateur: Chambre de Relance recycling

    The total D should converge to V_total for thermodynamic equilibrium (D/V → 1)
    """
    D_materiel: float = 0.0      # Material goods debt
    D_services: float = 0.0       # Services debt
    D_contractuel: float = 0.0    # TAP contracts (simplified: unused)
    D_engagement: float = 0.0     # Staking engagements
    D_regulateur: float = 0.0     # Relance chamber

    # Amortization rate (monthly decay ~0.104%)
    # Protocol specifies ~80-year memory horizon
    # Formula: δ_m ≈ 1 / (80 years × 12 months) = 0.00104166
    # Previous values: 0.01 (7-year horizon, too fast), 0.005 (17-year horizon, still too fast)
    delta_m: float = 0.00104166

    def add_debt(self, amount: float, secteur: str) -> None:
        """
        Add debt to specified sector

        Args:
            amount: Debt amount to add (can be negative to reduce)
            secteur: Sector name ('materiel', 'services', 'contractuel', 'engagement', 'regulateur')
        """
        attr_name = f'D_{secteur}'
        if not hasattr(self, attr_name):
            raise ValueError(f"Unknown sector: {secteur}")

        current = getattr(self, attr_name)
        setattr(self, attr_name, current + amount)

    def get_total(self) -> float:
        """
        Calculate total debt D across all sectors

        Returns:
            Total D = sum of all D_* components
        """
        return (
            self.D_materiel +
            self.D_services +
            self.D_contractuel +
            self.D_engagement +
            self.D_regulateur
        )

    def get_ratio(self, V_circ: float) -> float:
        """
        Calculate thermometric ratio r = D/V

        Args:
            V_circ: Total Verum in circulation

        Returns:
            Ratio r (target = 1.0 for equilibrium)
        """
        if V_circ <= 0:
            return 1.0  # Neutral if no V in circulation

        return self.get_total() / V_circ

    def apply_monthly_amortization(self) -> float:
        """
        Apply monthly amortization to all debt components

        D_amort,t = -δ_m × D_{t-1}

        This creates a slow decay of thermometric debt over time.
        Over 80 years (~960 months), this effaces most ancient debt.

        Returns:
            Total amount amortized (negative value)
        """
        amort_amount = -self.delta_m * self.get_total()

        # Apply proportionally to each sector
        total = self.get_total()
        if total > 0:
            self.D_materiel *= (1 - self.delta_m)
            self.D_services *= (1 - self.delta_m)
            self.D_contractuel *= (1 - self.delta_m)
            self.D_engagement *= (1 - self.delta_m)
            self.D_regulateur *= (1 - self.delta_m)

        return amort_amount

    def get_sector_breakdown(self) -> dict[str, float]:
        """
        Get breakdown of debt by sector

        Returns:
            Dictionary mapping sector names to debt amounts
        """
        return {
            'materiel': self.D_materiel,
            'services': self.D_services,
            'contractuel': self.D_contractuel,
            'engagement': self.D_engagement,
            'regulateur': self.D_regulateur,
            'total': self.get_total()
        }

    def __repr__(self) -> str:
        breakdown = self.get_sector_breakdown()
        return (
            f"RAD(D_total={breakdown['total']:.2f}, "
            f"mat={breakdown['materiel']:.2f}, "
            f"svc={breakdown['services']:.2f}, "
            f"eng={breakdown['engagement']:.2f}, "
            f"reg={breakdown['regulateur']:.2f})"
        )
