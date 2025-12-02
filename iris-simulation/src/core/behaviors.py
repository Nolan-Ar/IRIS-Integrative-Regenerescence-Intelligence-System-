"""
IRIS Simulation - Agent Behaviors
Implements economic decision-making for agents and enterprises
"""

import random
import math
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .agent import Agent, Entreprise, NFTFinancier
    from .bien import Bien
    from .chambre_memorielle import ChambreMemorielle
    from .rad import RAD


def decide_agent_actions(
    agent: 'Agent',
    cycle: int,
    entreprises: List['Entreprise'],
    chambre_memorielle: 'ChambreMemorielle',
    kappa: float,
    catalogue_biens: List['Bien'],
    rad: 'RAD'
) -> float:
    """
    Agent decides economic actions based on 5 aptitudes

    Priority order:
    1. Staking (social_up) - Long-term investment 4-5★
    2. Investment (épargne) - Finance enterprises via NFT
    3. Consumption (conso) - Play enterprise casinos
    4. Rest → passive savings (U burned at cycle end)

    Args:
        agent: Agent making decisions
        cycle: Current cycle number
        entreprises: List of available enterprises
        chambre_memorielle: Memorial chamber for staking
        kappa: Current κ coefficient
        catalogue_biens: Goods catalog
        rad: RAD instance

    Returns:
        Total U spent by agent
    """
    if not agent.alive:
        return 0

    U_spent = 0
    RU_disponible = agent.wallet_U

    # 1. STAKING (social_up > 60)
    if agent.aptitudes['social_up'] > 60 and RU_disponible > 0:
        budget_staking = RU_disponible * (agent.aptitudes['social_up'] / 100) * 0.4
        U_avant = agent.wallet_U

        # proposer_staking() prélève automatiquement le premier paiement mensuel
        if chambre_memorielle.proposer_staking(agent, budget_staking, cycle, kappa, rad):
            # Calculer le montant réellement prélevé
            U_apres = agent.wallet_U
            montant_preleve = U_avant - U_apres
            U_spent += montant_preleve
            RU_disponible -= montant_preleve

    # 2. INVESTMENT NFT (épargne > 50)
    if agent.aptitudes['épargne'] > 50 and RU_disponible > 0:
        budget_invest = RU_disponible * (agent.aptitudes['épargne'] / 100) * 0.3
        entreprise_cible = choisir_meilleure_entreprise(entreprises)
        if entreprise_cible:
            U_invested = investir_nft_entreprise(
                agent, entreprise_cible, budget_invest, kappa, cycle
            )
            U_spent += U_invested
            RU_disponible -= U_invested

    # 3. CONSUMPTION (conso > 40)
    if agent.aptitudes['conso'] > 40 and RU_disponible > 0:
        budget_conso = RU_disponible * (agent.aptitudes['conso'] / 100) * 0.5
        entreprise_cible = choisir_entreprise_ponderee(entreprises)
        if entreprise_cible:
            U_consumed = jouer_casino(
                agent, entreprise_cible, budget_conso, kappa, catalogue_biens
            )
            U_spent += U_consumed
            RU_disponible -= U_consumed

    return U_spent


def jouer_casino(
    agent: 'Agent',
    entreprise: 'Entreprise',
    budget_U: float,
    kappa: float,
    catalogue_biens: List['Bien']
) -> float:
    """
    Agent plays enterprise casino to acquire 1-3★ goods

    Process:
    1. Agent pays U (entry fee)
    2. Enterprise receives V (via simplified Stipulat conversion)
    3. Agent receives random good (1-3★) based on enterprise level

    Args:
        agent: Agent playing
        entreprise: Enterprise casino
        budget_U: U budget available
        kappa: Current κ coefficient
        catalogue_biens: Goods catalog

    Returns:
        Amount of U spent
    """
    # Entry price depends on enterprise level and κ
    prix_entree = entreprise.niveau * 10 * kappa

    if agent.wallet_U < prix_entree:
        return 0

    # Payment
    agent.wallet_U -= prix_entree

    # Conversion U→V (simplified Stipulat)
    # Formula: ΔV = U_burn / κ × efficiency
    V_genere = (prix_entree / kappa) * 0.8  # 80% efficiency

    entreprise.wallet_V += V_genere
    entreprise.historique_participants += 1

    # Random good drop based on enterprise level
    probas_drop = {
        1: [0.70, 0.25, 0.05],  # Level 1: 70% 1★, 25% 2★, 5% 3★
        2: [0.50, 0.35, 0.15],
        3: [0.30, 0.45, 0.25],
        4: [0.20, 0.40, 0.40],
        5: [0.10, 0.35, 0.55]   # Level 5: 55% 3★
    }

    etoiles = random.choices(
        [1, 2, 3],
        weights=probas_drop[entreprise.niveau]
    )[0]

    # Create good from catalog
    from .bien import creer_bien_aleatoire
    bien = creer_bien_aleatoire(etoiles, catalogue_biens)
    agent.biens.append(bien)

    return prix_entree


def investir_nft_entreprise(
    agent: 'Agent',
    entreprise: 'Entreprise',
    montant_U: float,
    kappa: float,
    cycle: int
) -> float:
    """
    Agent invests in enterprise via financial NFT

    Process:
    1. Agent pays U
    2. V is injected into enterprise
    3. Agent receives NFT financier (future dividends - not implemented)

    Args:
        agent: Investor
        entreprise: Target enterprise
        montant_U: Amount to invest (in U)
        kappa: Current κ coefficient
        cycle: Current cycle

    Returns:
        Amount of U spent
    """
    if agent.wallet_U < montant_U:
        return 0

    # Payment
    agent.wallet_U -= montant_U

    # Convert to V
    V_injecte = montant_U / kappa

    entreprise.wallet_V += V_injecte

    # Create NFT financier
    from .agent import NFTFinancier
    import uuid

    nft = NFTFinancier(
        id=str(uuid.uuid4()),
        entreprise=entreprise,
        investisseur=agent,
        montant_U=montant_U,
        V_injecte=V_injecte,
        duree=24,  # 2 years
        cycle_creation=cycle
    )
    agent.nft_financiers.append(nft)

    return montant_U


def choisir_meilleure_entreprise(entreprises: List['Entreprise']) -> Optional['Entreprise']:
    """
    Choose enterprise with highest trust (confiance)

    Args:
        entreprises: Available enterprises

    Returns:
        Best enterprise or None
    """
    actives = [e for e in entreprises if e.owner.alive]
    if not actives:
        return None

    return max(actives, key=lambda e: e.confiance)


def choisir_entreprise_ponderee(entreprises: List['Entreprise']) -> Optional['Entreprise']:
    """
    Choose enterprise weighted by level (higher level = more attractive)

    Args:
        entreprises: Available enterprises

    Returns:
        Chosen enterprise or None
    """
    actives = [e for e in entreprises if e.owner.alive]
    if not actives:
        return None

    # Weight by level
    weights = [e.niveau for e in actives]
    return random.choices(actives, weights=weights)[0]


def gerer_entreprise(
    entreprise: 'Entreprise',
    cycle: int,
    agents: List['Agent']
) -> tuple[float, float]:
    """
    Manage enterprise behavior

    Based on owner's aptitudes:
    - 'croissance': Campaign frequency
    - 'confiance': Campaign success rate

    Distribution:
    - 40% of V → salaries (distributed to random agents)
    - 60% of V → burned (simulates B2B exchanges)

    Args:
        entreprise: Enterprise to manage
        cycle: Current cycle number
        agents: All agents (for salary distribution)

    Returns:
        Tuple of (V_salaries, V_burned)
    """
    if not entreprise.owner.alive:
        return 0, 0

    owner = entreprise.owner

    # Check for NFT campaign (fundraising)
    croissance = owner.aptitudes['croissance']
    if croissance > 70:
        frequence_campagne = 6  # Every 6 months
    elif croissance > 40:
        frequence_campagne = 12  # Every year
    else:
        frequence_campagne = 24  # Every 2 years

    if cycle % frequence_campagne == 0:
        lancer_campagne_nft(entreprise, agents)

    # Distribute V (with reserve)
    V_minimum_reserve = 50  # Minimum reserve to maintain operations

    if entreprise.wallet_V <= V_minimum_reserve:
        return 0, 0

    # Only distribute 80% of available V, keep 20% as reserve
    V_distribuable = (entreprise.wallet_V - V_minimum_reserve) * 0.8

    V_salaires = V_distribuable * 0.4
    V_brule = V_distribuable * 0.6

    # Pay salaries to random agents
    distribuer_salaires_aleatoires(V_salaires, agents)

    # Update wallet: subtract distributed amount
    entreprise.wallet_V -= V_distribuable

    return V_salaires, V_brule


def lancer_campagne_nft(entreprise: 'Entreprise', agents: List['Agent']) -> None:
    """
    Launch NFT fundraising campaign

    Success depends on owner's 'confiance' aptitude
    If successful: enterprise level increases

    Args:
        entreprise: Enterprise launching campaign
        agents: Potential investors
    """
    chance_succes = entreprise.owner.aptitudes['confiance'] / 100
    montant_cible = entreprise.niveau * 1000  # Target scales with level

    # Filter potential investors (épargne > 60)
    investisseurs_potentiels = [
        a for a in agents
        if a.alive and a.aptitudes['épargne'] > 60 and a.wallet_U > 100
    ]

    if not investisseurs_potentiels:
        return

    montant_leve = 0
    for agent in random.sample(
        investisseurs_potentiels,
        min(10, len(investisseurs_potentiels))  # Max 10 investors
    ):
        if random.random() < chance_succes:
            contribution = min(agent.wallet_U * 0.2, montant_cible - montant_leve)
            # Direct investment (simplified)
            agent.wallet_U -= contribution
            entreprise.wallet_V += contribution
            montant_leve += contribution

            if montant_leve >= montant_cible:
                break

    # If successful (≥70% of target), level up
    if montant_leve >= montant_cible * 0.7:
        entreprise.niveau = min(5, entreprise.niveau + 1)


def distribuer_salaires_aleatoires(montant_total: float, agents: List['Agent']) -> None:
    """
    Distribute salaries to random living agents

    Args:
        montant_total: Total amount to distribute (in V)
        agents: All agents
    """
    vivants = [a for a in agents if a.alive]
    if not vivants:
        return

    # Choose random subset (10% of population)
    nb_salaries = max(1, len(vivants) // 10)
    salaries = random.sample(vivants, min(nb_salaries, len(vivants)))

    if not salaries:
        return

    salaire_individuel = montant_total / len(salaries)

    for agent in salaries:
        agent.wallet_V += salaire_individuel


def calculer_probabilite_deces(agent: 'Agent') -> float:
    """
    Calculate death probability based on age (Gompertz model)

    Formula:
    - age < 60: ~0.08% per month (~0.96% per year)
    - age ≥ 60: exponential increase

    Args:
        agent: Agent to evaluate

    Returns:
        Death probability for this cycle
    """
    if agent.age < 18:
        return 0.0
    elif agent.age < 60:
        return 0.00008  # ~0.96% per year
    else:
        # Gompertz: exp(0.1 × (age - 60))
        return 0.00008 * math.exp(0.1 * (agent.age - 60))
