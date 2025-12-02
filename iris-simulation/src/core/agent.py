"""
IRIS Simulation - Economic Agents and Enterprises
Implements agent behavior based on 5 aptitudes
"""

from dataclasses import dataclass, field
from typing import Optional
import uuid
import random


@dataclass
class Entreprise:
    """
    Enterprise owned by an agent
    Can produce goods 1-3★ via casino mechanism
    Funded via NFT financiers
    """
    id: str
    owner: 'Agent'  # Forward reference
    niveau: int  # 1-5 stars (starts 1-3)
    confiance: float  # Based on owner's 'confiance' aptitude
    wallet_V: float = 0.0
    historique_participants: int = 0  # Total casino plays

    def __post_init__(self):
        assert 1 <= self.niveau <= 5, f"Niveau must be 1-5, got {self.niveau}"
        assert 0 <= self.confiance <= 100, f"Confiance must be 0-100, got {self.confiance}"


@dataclass
class NFTFinancier:
    """
    Financial NFT representing investment in an enterprise
    Gives right to future dividends (not implemented in simplified version)
    """
    id: str
    entreprise: Entreprise
    investisseur: 'Agent'
    montant_U: float
    V_injecte: float
    duree: int  # Cycles remaining
    cycle_creation: int


@dataclass
class ContratStaking:
    """
    Staking contract for 4-5★ goods from Chambre Mémorielle
    Agent pays monthly installments to acquire patrimony
    """
    id: str
    agent: 'Agent'
    bien: 'Bien'  # From core.bien
    duree: int  # Total cycles
    cout_mensuel: float
    cycle_debut: int
    montant_total: float
    cycles_payes: int = 0


@dataclass
class Agent:
    """
    Economic agent in IRIS simulation

    Each agent has:
    - 5 aptitudes summing to 100
    - Individual η (productivity coefficient)
    - Wallets for V (Verum) and U (Unum)
    - NFT patrimony (goods owned)
    - Optional enterprise
    """
    id: str
    age: int  # 18-65+ years
    aptitudes: dict[str, float]  # 5 aptitudes summing to 100
    eta: float  # Individual productivity [0.5-1.5]
    wallet_V: float = 0.0
    wallet_U: float = 0.0
    biens: list = field(default_factory=list)  # List[Bien]
    nft_financiers: list[NFTFinancier] = field(default_factory=list)
    contrats_staking: list[ContratStaking] = field(default_factory=list)
    alive: bool = True
    entreprise: Optional[Entreprise] = None

    def __post_init__(self):
        # Validate aptitudes
        required_aptitudes = {'croissance', 'confiance', 'conso', 'social_up', 'épargne'}
        if set(self.aptitudes.keys()) != required_aptitudes:
            raise ValueError(f"Agent must have exactly these aptitudes: {required_aptitudes}")

        total = sum(self.aptitudes.values())
        if not (99.9 <= total <= 100.1):  # Allow small floating point errors
            raise ValueError(f"Aptitudes must sum to 100, got {total}")

    def get_patrimoine_total(self) -> float:
        """Calculate total patrimony (V + value of goods owned)"""
        biens_value = sum(b.valeur_V for b in self.biens)
        return self.wallet_V + biens_value


def generer_aptitudes_aleatoires() -> dict[str, float]:
    """
    Generate random aptitudes summing to 100

    5 aptitudes:
    - croissance: Entrepreneurial ambition
    - confiance: Fundraising ability
    - conso: Consumption propensity
    - social_up: Long-term investment (staking)
    - épargne: Enterprise investment
    """
    # Generate 5 random values
    values = [random.uniform(0, 100) for _ in range(5)]

    # Normalize to sum to 100
    total = sum(values)
    normalized = [v / total * 100 for v in values]

    return {
        'croissance': normalized[0],
        'confiance': normalized[1],
        'conso': normalized[2],
        'social_up': normalized[3],
        'épargne': normalized[4]
    }


def calculer_eta(agent: Agent) -> float:
    """
    Calculate individual η (productivity coefficient)

    Based on aptitudes:
    η = base + bonus_social + bonus_croissance - malus_conso

    Bounded to [0.5, 1.5]

    Args:
        agent: Agent with aptitudes

    Returns:
        Individual η coefficient
    """
    base = 0.7
    bonus_social = agent.aptitudes['social_up'] / 200      # +0 to +0.5
    bonus_croissance = agent.aptitudes['croissance'] / 200  # +0 to +0.5
    malus_conso = agent.aptitudes['conso'] / 300           # -0 to -0.33

    eta = base + bonus_social + bonus_croissance - malus_conso

    # Bound to [0.5, 1.5]
    return max(0.5, min(1.5, eta))


def creer_agent(age: int = None, avec_entreprise: bool = False) -> Agent:
    """
    Create a new agent with random aptitudes

    Args:
        age: Age in years (random 18-65 if not specified)
        avec_entreprise: Whether to create an enterprise for this agent

    Returns:
        New Agent instance
    """
    if age is None:
        age = random.randint(18, 65)

    aptitudes = generer_aptitudes_aleatoires()

    agent = Agent(
        id=str(uuid.uuid4()),
        age=age,
        aptitudes=aptitudes,
        eta=0.0,  # Will be calculated below
        wallet_V=0.0,
        wallet_U=0.0,
        biens=[],
        nft_financiers=[],
        contrats_staking=[],
        alive=True,
        entreprise=None
    )

    # Calculate eta based on aptitudes
    agent.eta = calculer_eta(agent)

    # Create enterprise if requested
    if avec_entreprise:
        agent.entreprise = Entreprise(
            id=str(uuid.uuid4()),
            owner=agent,
            niveau=random.randint(1, 3),  # Start at 1-3 stars
            confiance=agent.aptitudes['confiance'],
            wallet_V=0.0,
            historique_participants=0
        )

    return agent
