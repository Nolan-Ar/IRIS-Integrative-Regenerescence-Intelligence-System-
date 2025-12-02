# IRIS Simulation - Diagnostic 960 Cycles avec Effort Explicite

**Date**: 2025-12-02
**Configuration**: 4069 agents, 960 cycles (80 ans), seed=42
**Output**: `data/runs/simulation_960_effort_explicit/`

## Résumé des Modifications

Ce diagnostic porte sur une simulation incluant les modifications suivantes pour introduire **S (effort)** de manière explicite :

### 1. Calcul de S par Agent (`_calculer_effort_S_agent`)
- S calculé individuellement pour chaque agent
- Pondération par type de dépense :
  - **Staking** : poids 1.2 (engagement long terme)
  - **Investment** : poids 1.0 (effort entrepreneurial)
  - **Consumption** : poids 0.6 (satisfaction immédiate)
- Facteur agent basé sur aptitudes `croissance` et `social_up` : range [0.5, 1.0]

### 2. Intégration de S dans la Création de V
- `jouer_casino()` : V_genere × facteur_effort
- `investir_nft_entreprise()` : V_injecte × facteur_effort
- Rapproche la simulation de ΔV = η × f(U, S)

### 3. Utilisation de S dans nu_eff
- `Exchange.calculer_capteurs` : nu_eff = (U_burn + S_burn) / V_ON_prev
- S_burn_total maintenant calculé explicitement par cycle

## Résultats de la Simulation 960 Cycles

### Métriques Clés

| Métrique | T=0 | T=40 ans | T=80 ans | Évolution |
|----------|-----|----------|----------|-----------|
| **V_total** | 23,530 | 40,635 | 25,967 | +10.4% puis -36% |
| **D_total** | 23,530 | 21,255 | 55,623 | +136% |
| **D/V ratio** | 0.999 | 0.523 | 2.142 | Explosion |
| **κ (kappa)** | 1.15 | 2.00 | 2.00 | Collé au max |
| **η (eta)** | 1.15 | 2.00 | 2.00 | Collé au max |
| **Gini** | 0.600 | 0.419 | 0.509 | Amélioration puis dégradation |
| **Population** | 4,069 | 4,069 | 4,069 | Stable |
| **Entreprises** | 1,220 | 1,217 | 1,199 | Légère baisse |

### Évolution Temporelle

#### Phase 1 (Années 0-35) : Expansion Contrôlée
- **V_total** croît de 23.5k à 39.1k (+66%)
- **D/V** descend de 0.999 à 0.503 (amortissement RAD)
- **Gini** s'améliore de 0.60 à 0.415 (meilleure égalité)
- κ et η passent rapidement à 2.0 et y restent

#### Phase 2 (Années 35-60) : Stabilisation puis Inversion
- **V_total** stagne autour de 40k puis commence à décroître
- **D/V** remonte lentement de 0.50 à 1.06
- **Gini** se stabilise autour de 0.42-0.46
- Dette commence à croître à nouveau

#### Phase 3 (Années 60-80) : Effondrement Thermométrique
- **V_total** s'effondre de 35.7k à 26.0k (-27%)
- **D/V** explose de 1.06 à 2.14
- **Gini** remonte légèrement à 0.51
- Entreprises diminuent de 1245 à 1199

## Observations Critiques

### 1. Saturation des Régulateurs
**Problème** : κ et η collés à 2.0 dès le cycle 12

**Cause probable** :
- Avec le facteur effort [0.5, 1.0], la création de V est réduite de 25-50%
- Pour compenser, la régulation pousse κ et η au maximum
- La régulation n'a plus de marge de manœuvre

**Impact** :
- Perte totale du contrôle fin de l'économie
- nu_eff et tau_eng n'ont plus d'effet sur les paramètres
- Le système devient instable sur le long terme

### 2. Divergence D/V sur le Long Terme
**Observation** : D/V passe sous 0.5 (années 25-35) puis explose à 2.14 (année 80)

**Mécanisme** :
1. **Phase descendante** (0-35 ans) :
   - Forte création de V grâce à κ=η=2.0
   - Amortissement mensuel du RAD efficace
   - D diminue plus vite que V n'augmente initialement

2. **Phase ascendante** (35-80 ans) :
   - Création de V ralentit (plateau puis déclin)
   - Dette continue de s'accumuler (staking, décès)
   - Pas de mécanisme de freinage quand D > V

**Implications** :
- D/V > 2 signifie une dette massive non soutenable
- Perte de confiance potentielle dans le système
- Besoin d'un mécanisme de régulation de la dette plus fort

### 3. Stagnation puis Déclin de V
**Courbe de V_total** :
- Montée : 23.5k → 40.6k (années 0-40)
- Plateau : 40k (années 40-50)
- Déclin : 40k → 26k (années 50-80)

**Hypothèses** :
- **Vieillissement de la population** : agents plus âgés, moins productifs
- **Facteur effort** : réduit la conversion U→V de 25-50%
- **Saturation** : V atteint un plafond structurel vers 40k
- **Effet de feedback** : baisse de V → moins de RU → moins de dépenses → moins de V créé

## Analyse de l'Introduction de S (Effort)

### Points Positifs
✅ S est maintenant calculé explicitement par agent
✅ Distinction par type de dépense (staking/invest/conso) cohérente
✅ Intégration dans nu_eff fonctionne correctement
✅ Facteur effort dans création de V implémenté

### Points d'Attention
⚠️ **Réduction excessive de la création de V**
- Facteur effort [0.5, 1.0] divise la création de V par 1.3-2.0
- Compense trop fortement l'effet de κ=η=2.0
- Devrait peut-être être [0.7, 1.2] ou [0.8, 1.3]

⚠️ **Saturation immédiate des régulateurs**
- κ et η passent à 2.0 dès le cycle 12
- Plus de marge de manœuvre pour la régulation
- Suggère que les bornes [0.5, 2.0] sont trop étroites OU que les poids sont mal calibrés

⚠️ **S_burn > U_burn ?**
- Avec poids staking=1.2 et facteur agent [0.5, 1.0], S peut être supérieur à U
- Est-ce souhaitable thermodynamiquement ?
- Devrait-on avoir S ≈ U ou S < U en moyenne ?

## Recommandations

### Priorité 1 : Ajuster les Bornes ou les Coefficients
**Option A** : Élargir les bornes de κ et η
- Passer de [0.5, 2.0] à [0.3, 3.0]
- Permet plus de marge de régulation

**Option B** : Réduire les poids alpha/beta/gamma
- Ralentir la vitesse d'ajustement de κ et η
- Éviter la saturation rapide

**Option C** : Ajuster le facteur effort
- Réduire l'impact : passer de [0.5, 1.0] à [0.8, 1.1]
- Moins de réduction de la création de V

### Priorité 2 : Freinage de la Dette
**Mécanisme proposé** :
- Si D/V > 1.5 : augmenter l'amortissement mensuel du RAD
- Si D/V > 2.0 : ralentir la distribution de RU (réduction progressive)
- Éviter l'explosion incontrôlée de la dette

### Priorité 3 : Revoir la Relation S / U
**Questions à éclaircir** :
1. Thermodynamiquement, S devrait-il être du même ordre que U ?
2. Les poids 1.2 / 1.0 / 0.6 sont-ils réalistes ?
3. Faut-il normaliser S_burn_total pour qu'il soit proche de U_burn_total ?

### Priorité 4 : Diagnostic Détaillé des Capteurs
**Analyse à faire** :
- Tracer nu_eff, tau_eng, r_ic sur 960 cycles
- Voir si tau_eng > 0 grâce aux biens virtuels 4-5★
- Comprendre pourquoi la régulation échoue à stabiliser D/V

## Conclusion

L'introduction explicite de S (effort) fonctionne techniquement mais :

1. **Réduit trop la création de V** → saturation des régulateurs
2. **Instabilité à long terme** → D/V explose après 60 ans
3. **Besoin de recalibrage** → facteurs, poids, bornes

La prochaine itération devrait :
- Ajuster le facteur effort pour éviter la saturation de κ et η
- Introduire un mécanisme de freinage de la dette quand D/V > 1.5
- Analyser les capteurs en détail pour comprendre la dynamique

---

**Fichiers générés** :
- `data/runs/simulation_960_effort_explicit/metrics.csv`
- `data/runs/simulation_960_effort_explicit/*.png` (plots)
