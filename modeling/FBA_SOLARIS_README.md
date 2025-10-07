# Constraint‑based Modeling of Metabolically Engineered *Synechococcus elongatus*

**File:** `FBA__SOLARIS.html`  
**Purpose:** A self‑contained, browser‑viewable walkthrough that demonstrates Flux Balance Analysis (FBA) on *S. elongatus*, adds reactions for the **3‑HP bi‑cycle**, and explores gene deletions—connecting modeling outputs to the SOLARIS design/build choices.

---

## What’s inside
- **FBA primer:** Plain‑language intro to constraint‑based modeling, objective functions, and media/exchange bounds.
- **Baseline model:** Loads the published *S. elongatus* PCC 7942 model **iJB785** via COBRApy and reports WT growth and exchange fluxes.
- **3‑HP additions:** Programmatically adds key reactions (e.g., MCR, PCS1–3, MCL1–3, MCT, MCH, MEH, PCC, MMCE, SMTAB) and shows resulting fluxes.
- **Comparisons:** Correlates WT vs. +3‑HP fluxes and highlights reactions with the largest changes.
- **Knockouts:** Illustrates gene/enzyme deletion analyses (e.g., AGTi, PRK, HCO3E_1_cx, RBPCcx) and viability impacts.  

> The HTML includes code **and** outputs. You can read it without installing anything.

---

## Quick start (no install)
1. Download `FBA__SOLARIS.html` from this repository.
2. Double‑click to open it in any modern web browser.
3. Scroll through the narrative, code, and plots like a mini‑notebook.

---

## Key takeaways (from the shipped run)
- WT maximal biomass ≈ **0.05390 mmol·gDW⁻¹·h⁻¹** (solver‑dependent).  
- After adding 3‑HP reactions, the model routes flux through the new pathway while maintaining similar maximal growth (within numerical tolerance).  
- Flux redistribution is visible in the “largest changes” bar plot.  
- In the WT background shown here, **AGTi** deletion is lethal; **PRK** deletion is tolerated; several RuBisCO/carboxysome‑related genes are essential.

> Numbers can shift slightly with solver/model versions or media settings.

---

## Reproducing the analysis (optional)
If you prefer to re‑run code rather than read the static HTML:

### 1) Create an environment
```bash
conda create -n solaris-fba python=3.10 -y
conda activate solaris-fba
pip install cobra optlang swiglpk matplotlib pandas
```

### 2) Get the model
The tutorial uses `load_model("iJB785")`. If your COBRApy build doesn’t ship iJB785, download an SBML copy and load it explicitly, adjusting reaction/metabolite IDs where needed.

### 3) Run
Copy the code blocks from the HTML into a Jupyter notebook or `.py` script and execute. Ensure a MILP/LP solver (e.g., GLPK via `swiglpk`) is available.

---

## Suggested repository layout
```
/ (repo root)
├── FBA__SOLARIS.html
└── README.md   # this file
```

---
