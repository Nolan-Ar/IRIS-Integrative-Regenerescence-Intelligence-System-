# Diagnostic: 960-Cycle Simulation (80 Years)

**Date**: December 2, 2025
**Configuration**: 500 agents, seed 42, refactored regulation
**Output**: `data/runs/simulation_960cycles/`

## Executive Summary

The simulation reveals **catastrophic thermodynamic failure**. After 80 years, the D/V ratio reached 5.87 (should be 1.0), representing a complete economic collapse with 78% destruction of value and 29% increase in debt.

## Critical Finding: tau_eng = 0 Throughout

**Most Important Discovery**: The tau_eng sensor remained at **exactly 0.0** for all 960 cycles, indicating **zero staking activity**.

| Cycle | Year | D/V   | κ    | η    | nu_eff | tau_eng |
|-------|------|-------|------|------|--------|---------|
| 0     | 0    | 0.999 | 1.15 | 1.15 | 0.000  | **0.0** |
| 119   | 10   | 0.801 | 2.00 | 2.00 | 0.005  | **0.0** |
| 479   | 40   | 0.701 | 2.00 | 2.00 | 0.005  | **0.0** |
| 839   | 70   | 2.199 | 1.21 | 0.50 | 0.000  | **0.0** |
| 958   | 80   | 4.389 | 0.50 | 0.50 | 0.001  | **0.0** |

### Root Cause: Empty Memorial Chamber

Staking requires 4-5★ goods from the `chambre_memorielle`. At initialization:
- Stock: **0 goods** (empty)
- Agents cannot stake without available high-tier goods
- tau_eng = U_stake_flow / RU_total = 0 / 8346 = 0

This creates a **chicken-and-egg problem**:
1. Need 4-5★ goods to stake
2. Get 4-5★ goods by completing staking contracts
3. Cannot complete contracts without initial goods

## Timeline of Collapse

### Phase 1: Hidden Deficit (Years 0-30)
**D/V trajectory**: 0.999 → 0.713

- κ and η max out at 2.0 immediately
- System in "full stimulus" mode
- D amortization (0.1%/month) outpaces V creation
- Despite η doubling V creation, not enough to compensate

**Why V can't keep up**:
```python
# With η = 2.0 and κ = 2.0:
V_from_RU = RU_total * agent.eta * eta_global
V_from_casino = (U_burn / kappa) * 0.8 * eta_global
V_from_investment = (U_invest / kappa) * eta_global

# Total V creation ≈ 8346 * 0.83 * 2.0 = ~13,850 per cycle
# D amortization = D_total * 0.001041666 ≈ 24.5 per cycle
# Net: V grows faster, so D/V should decrease... but it doesn't!
```

**The paradox**: V is growing in absolute terms (23,530 → 25,345), but D amortization is too aggressive.

### Phase 2: Equilibrium Crossing (Years 30-52)
**D/V trajectory**: 0.713 → 1.033

- D/V reaches minimum at Year 30 (0.713)
- System overshoots and crosses equilibrium
- V_total continues growing but slowing down
- Regulation remains maxed (κ=2.0, η=2.0)

### Phase 3: Accelerating Collapse (Years 52-66)
**D/V trajectory**: 1.033 → 1.917

- V_total peaks at 25,345 (Year 25) then declines
- D_total crosses V_total at Year 52
- "Death spiral" begins: less V → less U → less V creation
- κ and η still maxed, unable to prevent collapse

### Phase 4: Regulation Inversion (Years 66-79)
**D/V trajectory**: 1.917 → 5.874

**Year 66** - Critical transition:
- D/V = 1.917 (finally triggers r_thermo > 1)
- η drops to 1.76 (first movement in 66 years!)
- System realizes it's in debt excess, reverses policy

**Years 67-79** - Too late:
- κ and η crash to 0.5 (minimum)
- Attempting to cool economy by restricting supply
- **Counterproductive**: Less V creation accelerates collapse
- V_total: 12,890 → 5,170 (60% loss in 13 years!)
- D_total: 26,883 → 30,369 (13% gain)

**Final state**:
- V_total: 5,170 (78% below initial)
- D_total: 30,369 (29% above initial)
- D/V: 5.874 (487% above target)

## Regulation Analysis

### Sensor Values

**r_ic** (Investment/Consumption ratio):
- Always 0.0 (no staking debt)
- Formula: (D_TAP + D_stack) / V_ON
- Cannot function without staking

**nu_eff** (Circulation velocity):
- Range: 0.0004 - 0.0051
- Target: 0.20
- **96-98% below target!**
- Indicates severe economic stagnation
- U_burn is tiny relative to V_ON

**tau_eng** (Engagement rate):
- Always 0.0 (no staking flow)
- Target: 0.35
- **100% below target!**

### Regulation Formula Behavior

```python
# Years 0-65 (D/V < 1):
Delta_eta = +0.3*(1-0.7) + 0.4*(0.2-0.005) - 0.2*(0-0.35)
          = +0.09 + 0.078 + 0.07 = +0.238 (capped to +0.15)
Delta_kappa = +0.4*(0.2-0.005) - 0.3*(0-0.35) + 0.2*(1-0.7)
            = +0.078 + 0.105 + 0.06 = +0.243 (capped to +0.15)
# Both push upward strongly → hit 2.0 bounds

# Years 67-79 (D/V > 2):
Delta_eta = +0.3*(1-2.5) + 0.4*(0.2-0.0005) - 0.2*(0-0.35)
          = -0.45 + 0.08 + 0.07 = -0.30 (capped to -0.15)
Delta_kappa = +0.4*(0.2-0.0005) - 0.3*(0-0.35) + 0.2*(1-2.5)
            = +0.08 + 0.105 - 0.30 = -0.115
# Eta drops hard, kappa follows → hit 0.5 bounds
```

### Extreme Adjustments

- **Kappa**: 928 out of 960 cycles at bounds (96.7%)
- **Eta**: 932 out of 960 cycles at bounds (97.1%)

**Interpretation**: Regulation spending 97% of time at extremes indicates the system is **fundamentally unstable**, not just poorly tuned.

## Inequality Evolution

- **Gini coefficient**: 0.60 → 0.70 (+17%)
- **Trend slope**: +0.00013 per cycle (r² = 0.70)
- **Interpretation**: Wealth concentration accelerates during collapse
- Top 10%: 39.8% → 39.7% (relatively stable)
- Top 20%: 78.7% → 78.6% (relatively stable)

Interesting: Despite collapse, wealth distribution remains similar. The collapse affects everyone proportionally.

## Demographics

- **Population**: Stable at 500 agents
- **Births**: 453
- **Deaths**: 453
- **Volatility**: 0.0000

Demographic system functioning perfectly, ironic given economic collapse.

## Statistical Tests

### Augmented Dickey-Fuller Test
- **ADF statistic**: 4.021
- **p-value**: 1.0
- **Critical values**: -3.44 (1%), -2.86 (5%), -2.57 (10%)
- **Result**: Non-stationary, not converging

The D/V ratio is **explosive** (unit root present), confirming divergence.

## Key Insights

### 1. Staking Is Critical
Without staking:
- tau_eng sensor non-functional
- No long-term engagement debt to balance short-term flows
- r_ic sensor also broken
- Regulation operates blind on 2 of 3 sensors

### 2. nu_eff Too Low
Circulation velocity 96% below target indicates:
- Agents not spending their U
- Economic activity too low
- RU distribution too high relative to consumption

**Possible causes**:
- RU_base = V_ON / 50 might be too generous
- Agents save most of their U (then it's burned)
- Prices too high relative to income

### 3. Amortization vs Creation Imbalance

**D amortization**: 0.1041666% per cycle
- At D = 23,500: Removes ~24.5 D per cycle
- At D = 30,000: Removes ~31.2 D per cycle

**V creation** (with η = 2.0):
- RU base: ~8,346 U/cycle (becomes ~13,900 V with η=2.0)
- Casino: ~50 U/cycle (becomes ~20 V with η=2.0, κ=2.0)
- Investment: ~0 U/cycle (agents don't invest much)

V creation should vastly exceed D amortization, yet the system collapses. Why?

**Answer**: The problem isn't creation/destruction balance. It's that **D is being created somewhere not accounted for**.

Looking at RAD sectors in final state:
- D_materiel: dominant
- D_regulateur: growing (from agent deaths)
- D_engagement: 0 (no staking)

The D is coming from:
1. Initial D₀ = V₀ (material sector)
2. Agent death patrimony (regulateur sector)
3. Enterprise operations

### 4. Regulation Paradox

**Years 0-65**: Maximum stimulus (κ=2, η=2)
- Trying to create more V
- Actually working: V grows 23,530 → 25,345
- But D amortization is faster

**Years 65-79**: Maximum restriction (κ=0.5, η=0.5)
- Trying to cool economy
- **Counterproductive**: Less V creation accelerates collapse
- V crashes 13,722 → 5,170

**The trap**: No matter what the regulation does, it's wrong!
- Stimulus → D amortizes too fast, can't keep up
- Restriction → V creation stops, collapse accelerates

## Recommendations

### Immediate Fixes Required

1. **Initialize Memorial Chamber** with 4-5★ goods
   ```python
   # In oracle.py __init__:
   high_tier_goods = [b for b in catalogue_biens if b.etoiles >= 4]
   initial_stock = random.sample(high_tier_goods, k=50)
   chambre_memorielle.stock_biens = initial_stock
   ```

2. **Reduce D Amortization Rate**
   - Current: 0.1041666% per cycle
   - Suggested: 0.02% per cycle (5x slower)
   - This gives V creation time to catch up

3. **Increase nu_eff** (circulation velocity)
   - Reduce RU_base formula: V_ON / 100 instead of V_ON / 50
   - Or increase consumption incentives
   - Or reduce prices

4. **Adjust Regulation Bounds**
   - Expand range: [0.3, 3.0] instead of [0.5, 2.0]
   - Gives more room for adjustment
   - Or use non-linear scaling near bounds

5. **Fix D Creation at Death**
   - Already implemented: Use net patrimony (V - D)
   - Verify it's working correctly

### Research Questions

1. **Where is the hidden D coming from?**
   - Investigate all RAD.add_debt() calls
   - Check if enterprise operations create untracked debt
   - Verify conservation law: ΔD = ΔV at all times

2. **Why is nu_eff so low?**
   - Are agents rational in not spending?
   - Is RU distribution mismatched with prices?
   - Should there be inflation/deflation mechanics?

3. **Can the system ever be stable?**
   - Or is it inherently chaotic due to:
     - Monthly amortization (deterministic decay)
     - Stochastic consumption (random spending)
     - Demographic noise (deaths/births)
   - May need PID controller instead of linear feedback

## Conclusion

The refactored system successfully connects η and κ to the economy, but reveals fundamental instability. The simulation demonstrates that without staking engagement (tau_eng > 0), the thermodynamic equilibrium cannot be maintained.

**Next steps**: Fix memorial chamber initialization and rerun to test if staking enables convergence.

---

**Full data available in**: `data/runs/simulation_960cycles/`
- `metrics.csv` (379 KB, 960 rows × 35 columns)
- Statistical report
- 7 visualization plots
