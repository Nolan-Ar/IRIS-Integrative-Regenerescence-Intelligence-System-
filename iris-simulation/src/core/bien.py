"""
IRIS Simulation - Goods (Biens) Module
Implements NFT goods with star ratings (1-5 stars)
"""

import random
import uuid
from dataclasses import dataclass
from typing import Literal


@dataclass
class Bien:
    """
    Represents a good/asset in the IRIS economy
    Biens are NFTs with 1-5 star ratings representing value tiers
    """
    id: str
    etoiles: int  # 1-5 stars
    valeur_V: float  # Value in Verum
    type: Literal['consommable', 'durable', 'patrimonial']
    actif: bool = True  # Active in CNP or archived

    def __post_init__(self):
        assert 1 <= self.etoiles <= 5, f"Stars must be 1-5, got {self.etoiles}"
        assert self.valeur_V >= 0, f"Value must be non-negative, got {self.valeur_V}"


def generer_catalogue_biens(V_total: float) -> list[Bien]:
    """
    Generate goods catalog with Fibonacci distribution

    Quantity distribution (descending):
    - 1★: 55% of items, 5% of value
    - 2★: 34% of items, 8% of value
    - 3★: 11% of items, 13% of value
    - 4★: 0% initial (from Chambre Mémorielle), 21% of value
    - 5★: 0% initial (from Chambre Mémorielle), 53% of value

    Args:
        V_total: Total Verum to distribute across catalog

    Returns:
        List of Bien objects representing the catalog
    """
    # Value distribution per star level
    repartition_valeur = {
        1: 0.05,  # 5% of V_total
        2: 0.08,  # 8% of V_total
        3: 0.13,  # 13% of V_total
        4: 0.21,  # 21% of V_total (reserved for CM)
        5: 0.53   # 53% of V_total (reserved for CM)
    }

    # Quantity distribution (for initial 1-3 stars only)
    repartition_quantite = {
        1: 0.55,  # 55% of items
        2: 0.34,  # 34% of items
        3: 0.11   # 11% of items
    }

    catalogue = []

    # Base number of items (scales with economy size)
    nb_items_base = int(V_total * 0.5)  # Roughly 0.5 items per V unit

    # Generate 1-3 star items (4-5 stars come from Chambre Mémorielle)
    for etoiles in [1, 2, 3]:
        valeur_totale = V_total * repartition_valeur[etoiles]
        nb_biens = int(nb_items_base * repartition_quantite[etoiles])

        if nb_biens == 0:
            continue

        valeur_unitaire = valeur_totale / nb_biens

        # Determine type based on stars
        if etoiles == 1:
            item_type = 'consommable'  # Consumables (food, transport)
        elif etoiles == 2:
            item_type = 'durable'       # Durables (clothes, leisure)
        else:
            item_type = 'patrimonial'   # Assets (electronics, furniture)

        for _ in range(nb_biens):
            catalogue.append(Bien(
                id=str(uuid.uuid4()),
                etoiles=etoiles,
                valeur_V=valeur_unitaire,
                type=item_type,
                actif=True
            ))

    return catalogue


def creer_bien_aleatoire(etoiles: int, catalogue: list[Bien]) -> Bien:
    """
    Create a random good of specified star level from catalog
    Used when agents acquire goods through casino/purchases

    Args:
        etoiles: Star level (1-5)
        catalogue: Available goods catalog

    Returns:
        New Bien instance (copy from catalog)
    """
    # Filter catalog by star level
    biens_disponibles = [b for b in catalogue if b.etoiles == etoiles]

    if not biens_disponibles:
        # If no goods available, create a default one
        # This shouldn't happen in normal operation
        valeur_default = {1: 10, 2: 50, 3: 200, 4: 1000, 5: 5000}
        return Bien(
            id=str(uuid.uuid4()),
            etoiles=etoiles,
            valeur_V=valeur_default.get(etoiles, 100),
            type='durable',
            actif=True
        )

    # Pick a random template and create a new instance
    template = random.choice(biens_disponibles)

    return Bien(
        id=str(uuid.uuid4()),  # New unique ID
        etoiles=template.etoiles,
        valeur_V=template.valeur_V,
        type=template.type,
        actif=True
    )


def recalibrer_catalogue(catalogue: list[Bien], V_ON: float, V_initial: float) -> None:
    """
    ✓ CORRECTION 4: Recalibrate goods catalog based on current V_ON

    Formula: new_value = initial_value × (V_ON / V_initial)

    This ensures goods values scale with economy size

    Args:
        catalogue: Goods catalog to recalibrate
        V_ON: Current total active Verum
        V_initial: Initial V_ON at system start
    """
    if V_initial <= 0 or V_ON <= 0:
        return

    # Calculate scaling factor
    facteur_echelle = V_ON / V_initial

    # Recalibrate each good
    for bien in catalogue:
        # Store initial value if not already stored
        if not hasattr(bien, 'valeur_initiale'):
            bien.valeur_initiale = bien.valeur_V

        # Scale value proportionally to V_ON
        bien.valeur_V = bien.valeur_initiale * facteur_echelle
