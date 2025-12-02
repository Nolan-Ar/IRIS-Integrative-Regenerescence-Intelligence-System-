"""
IRIS Simulation - Exchange Module
Implements thermodynamic regulation via κ and η coefficients
"""

from typing import List, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .agent import Agent, Entreprise
    from .rad import RAD


class Exchange:
    """
    Exchange module - Thermodynamic regulation

    Calculates and adjusts:
    - κ (kappa): Liquidity regulator (V→U conversion)
    - η (eta): Creation multiplier (production efficiency)

    Based on 3 system sensors:
    - r (thermometric ratio D/V)
    - ν_eff (circulation velocity)
    - τ_eng (engagement rate)
    """

    def __init__(self):
        # Current regulation coefficients
        self.kappa: float = 1.0
        self.eta_global: float = 1.0

        # Sensor configuration
        self.nu_target: float = 0.20      # Target circulation velocity
        self.tau_target: float = 0.35     # Target engagement rate

        # Adjustment coefficients for η
        self.alpha_eta: float = 0.3       # Weight for thermometer
        self.beta_eta: float = 0.4        # Weight for velocity
        self.gamma_eta: float = 0.2       # Weight for engagement

        # Adjustment coefficients for κ
        self.alpha_kappa: float = 0.4     # Weight for velocity
        self.beta_kappa: float = 0.3      # Weight for engagement
        self.gamma_kappa: float = 0.2     # Weight for thermometer

        # Bounds
        self.eta_min: float = 0.5
        self.eta_max: float = 2.0
        self.kappa_min: float = 0.5
        self.kappa_max: float = 2.0
        self.delta_max: float = 0.15      # Max change per cycle

    def calculer_V_ON(self, agents: List['Agent'], entreprises: List['Entreprise']) -> float:
        """
        Calculate V_ON (total active Verum in circulation)

        V_ON = sum of all V in agent wallets + enterprise wallets

        Args:
            agents: List of agents
            entreprises: List of enterprises

        Returns:
            Total V_ON
        """
        V_agents = sum(a.wallet_V for a in agents if a.alive)
        V_entreprises = sum(e.wallet_V for e in entreprises if e.owner.alive)

        return V_agents + V_entreprises

    def calculer_capteurs(
        self,
        agents: List['Agent'],
        entreprises: List['Entreprise'],
        rad: 'RAD',
        cycle_data: dict
    ) -> Tuple[float, float, float]:
        """
        Calculate the 3 system sensors

        Args:
            agents: List of agents
            entreprises: List of enterprises
            rad: RAD instance
            cycle_data: Previous cycle data with keys:
                - U_burn_total: U burned in cycle
                - S_burn_total: S burned in cycle (simplified: ~= U_burn)
                - V_ON_prev: V_ON from previous cycle

        Returns:
            Tuple of (r_ic, nu_eff, tau_eng)
        """
        V_ON = self.calculer_V_ON(agents, entreprises)

        # Sensor 1: Investment/consumption ratio (simplified: staking ratio)
        D_TAP = 0  # TAP not implemented in simplified version
        D_stack = sum(
            c.montant_total for a in agents if a.alive
            for c in a.contrats_staking
        )
        r_ic = (D_TAP + D_stack) / V_ON if V_ON > 0 else 0

        # Sensor 2: Effective circulation velocity
        U_burn = cycle_data.get('U_burn_total', 0)
        S_burn = cycle_data.get('S_burn_total', U_burn)  # Simplified: S ≈ U
        V_ON_prev = cycle_data.get('V_ON_prev', V_ON)
        nu_eff = (U_burn + S_burn) / V_ON_prev if V_ON_prev > 0 else 0.2

        # Sensor 3: Engagement rate (flow-based)
        # tau_eng = U spent on staking / RU distributed
        # Uses previous cycle's flow data
        RU_total = cycle_data.get('RU_total', 0)
        U_stake_flow = cycle_data.get('U_stake_flow', 0)
        tau_eng = U_stake_flow / RU_total if RU_total > 0 else 0

        return r_ic, nu_eff, tau_eng

    def calculer_kappa(self, rad: 'RAD', V_ON: float) -> float:
        """
        Calculate κ (liquidity regulator) based on thermometric ratio

        Formula (Layer 1 simplified):
        κ = κ_base × (1 + α × Δr)

        where Δr = r - 1 (deviation from equilibrium)

        κ > 1.0: Facilitation (stimulates demand)
        κ = 1.0: Neutrality
        κ < 1.0: Restriction (cools economy)

        Range: κ ∈ [0.5, 2.0]

        Args:
            rad: RAD instance
            V_ON: Total V in circulation

        Returns:
            Kappa coefficient
        """
        kappa_base = 1.0
        alpha_kappa_thermo = 0.5  # Sensitivity to thermometric deviation

        # Thermometric ratio
        r = rad.get_ratio(V_ON)
        Delta_r = r - 1.0  # Deviation from equilibrium

        # Formula: κ = κ_base × (1 + α × Δr)
        kappa = kappa_base * (1 + alpha_kappa_thermo * Delta_r)

        # Bound to [0.5, 2.0]
        return max(self.kappa_min, min(self.kappa_max, kappa))

    def calculer_eta(self, nu_eff: float) -> float:
        """
        Calculate η (creation multiplier) based on circulation velocity

        Formula (Layer 1 simplified):
        η = η_base × (1 + α × Δν)

        where Δν = ν_target - ν_eff

        η > 1.0: Boost (stimulates production)
        η = 1.0: Neutrality
        η < 1.0: Brake (avoids overheating)

        Range: η ∈ [0.5, 2.0]

        Args:
            nu_eff: Effective circulation velocity

        Returns:
            Eta coefficient
        """
        eta_base = 1.0
        alpha_eta_velo = 1.0  # Sensitivity to velocity deviation

        # Velocity deviation
        Delta_nu = self.nu_target - nu_eff

        # Formula: η = η_base × (1 + α × Δν)
        eta = eta_base * (1 + alpha_eta_velo * Delta_nu)

        # Bound to [0.5, 2.0]
        return max(self.eta_min, min(self.eta_max, eta))

    def ajuster_parametres(
        self,
        r_ic: float,
        nu_eff: float,
        tau_eng: float,
        r_thermo: float
    ) -> Tuple[float, float]:
        """
        Adjust η and κ based on full sensor feedback (Layer 1 complete)

        Formulas from IRIS protocol (section 3.3.1):

        Δη_t = +α_η × (1 - r_{t-1}) + β_η × (ν_target - ν_{t-1}) - γ_η × (τ_eng - τ_target)
        Δκ_t = +α_κ × (ν_target - ν_{t-1}) - β_κ × (τ_eng - τ_target) + γ_κ × (1 - r_{t-1})

        Constraints:
        - |Δη|, |Δκ| ≤ 0.15 (max 15% change per cycle)
        - η, κ ∈ [0.5, 2.0]

        Args:
            r_ic: Investment/consumption ratio
            nu_eff: Circulation velocity
            tau_eng: Engagement rate
            r_thermo: Thermometric ratio D/V

        Returns:
            Tuple of (new_eta, new_kappa)
        """
        # Calculate Δη (eta variation)
        Delta_eta = (
            self.alpha_eta * (1 - r_thermo) +
            self.beta_eta * (self.nu_target - nu_eff) -
            self.gamma_eta * (tau_eng - self.tau_target)
        )

        # Calculate Δκ (kappa variation)
        Delta_kappa = (
            self.alpha_kappa * (self.nu_target - nu_eff) -
            self.beta_kappa * (tau_eng - self.tau_target) +
            self.gamma_kappa * (1 - r_thermo)
        )

        # Apply max change constraint
        Delta_eta = max(-self.delta_max, min(self.delta_max, Delta_eta))
        Delta_kappa = max(-self.delta_max, min(self.delta_max, Delta_kappa))

        # Update parameters
        new_eta = self.eta_global + Delta_eta
        new_kappa = self.kappa + Delta_kappa

        # Apply bounds [0.5, 2.0]
        new_eta = max(self.eta_min, min(self.eta_max, new_eta))
        new_kappa = max(self.kappa_min, min(self.kappa_max, new_kappa))

        # Store for next cycle
        self.eta_global = new_eta
        self.kappa = new_kappa

        return new_eta, new_kappa

    def convert_V_to_U(self, amount_V: float) -> float:
        """
        Convert Verum to Unum

        U_obtained = V_converted × κ

        Args:
            amount_V: Amount of V to convert

        Returns:
            Amount of U obtained
        """
        return amount_V * self.kappa

    def convert_U_to_V(self, amount_U: float) -> float:
        """
        Convert Unum to Verum (inverse operation)

        V_obtained = U_converted / κ

        Args:
            amount_U: Amount of U to convert

        Returns:
            Amount of V obtained
        """
        return amount_U / self.kappa if self.kappa > 0 else 0

    def get_status(self) -> dict:
        """
        Get current Exchange status

        Returns:
            Dictionary with current parameters
        """
        return {
            'kappa': self.kappa,
            'eta_global': self.eta_global,
            'nu_target': self.nu_target,
            'tau_target': self.tau_target,
            'bounds': {
                'eta': [self.eta_min, self.eta_max],
                'kappa': [self.kappa_min, self.kappa_max],
                'delta_max': self.delta_max
            }
        }
