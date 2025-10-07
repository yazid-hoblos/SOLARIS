# Modeling — SOLARIS FBA Assets

This folder contains the models, notebook, and rendered report supporting our **constraint‑based analysis** of engineered *Synechococcus elongatus*. It accompanies the Modeling section of our wiki and supports our **Gold #1: Model** criteria.

## What’s inside

```
modeling/
├── FBA_ANALYSIS_SOLARIS.ipynb               # Reproducible notebook (COBRApy)
├── FBA_ANALYSIS_SOLARIS.html                # Static, readable export of the notebook
├── model_PCC7942_SER_SOLARIS.xml            # SBML: improved baseline model (gap‑filled)
└── model_PCC7942_3HPP_SER_DEL_SOLARIS.xml   # SBML: improved + 3HP cycle + deletions
```

### File details
- **`model_PCC7942_SER_SOLARIS.xml` (SBML)** – Curated PCC 7942 network (derived from iJB785) with **missing reactions added** via literature/database checks. Use as the _baseline_ (“SER = SOLARIS Enhanced Reconstruction”).  
- **`model_PCC7942_3HPP_SER_DEL_SOLARIS.xml` (SBML)** – The enhanced baseline **plus** the engineered **3‑HP bi‑cycle reactions** and the **knockouts** used in silico. This is the _engineered_ model for viability/flux redistribution analyses.  
- **`FBA_ANALYSIS_SOLARIS.ipynb`** – End‑to‑end analysis in Python/COBRApy: load SBML, optimize growth, compare WT vs engineered, inspect added‑reaction fluxes, and explore deletions.  
- **`FBA_ANALYSIS_SOLARIS.html`** – Static export for quick browsing without a Python setup.

## Quick start (COBRApy)

Install deps (Python ≥ 3.9):
```bash
pip install cobra numpy pandas matplotlib
```

Minimal check:
```python
import cobra
from cobra.io import read_sbml_model

wt  = read_sbml_model("model_PCC7942_SER_SOLARIS.xml")
eng = read_sbml_model("model_PCC7942_3HPP_SER_DEL_SOLARIS.xml")

print("WT biomass:", wt.optimize().objective_value)
print("ENG biomass:", eng.optimize().objective_value)

for rxn in ["MCR1","MCR2","PCS1","PCS2","PCS3","MCL1","MCL2","MCL3","MCT","MCH","MEH","PCC","MMCE","SMTAB"]:
    if rxn in eng.reactions:
        print(rxn, eng.optimize().fluxes.get(rxn, 0.0))
```

Or run the full notebook:
```bash
jupyter notebook FBA_ANALYSIS_SOLARIS.ipynb
```

## Provenance & scope

- Baseline started from **iJB785** and was **gap‑filled** where justified.  
- Engineered SBML introduces the **3‑HP bi‑cycle** and **deletions** aligned with our design/build.  
- IDs are kept consistent with the figures so results match the wiki.

## How this supports our Gold claim

- **Design validation:** FBA shows flux redistribution toward the 3‑HP path without catastrophic growth loss.  
- **Community value:** We share the **enhanced SBML** and reproducible notebook for others to reuse/benchmark.  
- **Accessibility:** Both executable (`.ipynb`) and read‑only (`.html`) formats are provided.

## Cite & license

Please cite our team and the original PCC 7942 model:
- Broddrick JT *et al.* 2016. PNAS 113(51):E8344–E8353. iJB785 model of *S. elongatus* PCC 7942.

Code: MIT. SBML models: academic use with attribution.

— SOLARIS Team
