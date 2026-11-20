# Complete BrainTriage research paper

[Read the complete manuscript](manuscript/braintriage_complete_research_paper.docx). This is the main reading copy, consolidating the measurement-benefit benchmark, nested model comparison, and independent EEG companion validation. The versioned papers remain available as historical records.

The 32-page manuscript includes 20 figures (18 result figures and two workflow diagrams), 16 numbered equations, 10 study tables, three notation tables, and 28 references. All text remains black, including figure labels and captions; plots and diagrams use colour, with distinct markers and line styles. The acquisition-versus-Brier curves appear as Figure 4 on page 7. Mathematical derivations begin on page 4; blending is on page 13; external-model and statistical formulas are on pages 18–20.

Appendix C, pages 30–32, defines 53 groups of symbols, operators and abbreviations. It links symbols to their equations and distinguishes reused letters such as m (posterior vector or batch size), q (acquisition fraction or observed proportion), z (EEG feature vector or normal critical value), and c (acquisition cost or interval centre). The editable glossary is in `notation.json`.

## Evidence covered

- **Study A:** Measured OASIS, CSF and Greek AD/FTD inputs; acquisition comparisons, equal-cost allocation and estimation-error derivations, learning curves, ablations, referral stability, benefit reliability, perturbations, hypothetical costs, missed cases and calibration. Clinical holdouts had already been exposed.
- **Study B:** Nested model selection, spectral/complexity and covariance representations, probability blending and matched routing comparisons on the earlier development participants. Favorable mean EEG results were not consistent across repeats or clinical cohorts.
- **Study C:** Source-only sensitivity analyses and one frozen independent AD-versus-healthy-control test on 23 Spanish participants. Covariance detected all 12 AD cases but falsely flagged 7 of 11 controls. The original clinical-input AD/FTD acquisition model still lacks compatible external validation.

This revision adds no model fits, target tuning or external evaluations. All numerical results come from retained aggregate outputs. It does not establish overall superiority, prospective safety or clinical deployment. The author must review the complete manuscript and satisfy the chosen venue's formatting, authorship and AI-assistance disclosure requirements before submission.

## Rebuild the document and figures

Run from the research directory with Python, NumPy, pandas, Matplotlib and python-docx installed:

```sh
python consolidated/src/figures_stage_a.py
python consolidated/src/figures_stage_b.py
python consolidated/src/figures_stage_c.py
python consolidated/src/diagrams.py
python consolidated/src/build_manuscript.py
```

The builders read versioned narratives, literature records and aggregate results in `extension_v2`, `extension_v3` and `extension_v4`; keep those directories beside `consolidated`. All result figures are rebuilt from saved aggregates. No participant files or trained bundles are needed to rebuild the paper. Training reproduction is documented separately in each study directory and requires independently acquired source data under provider terms.

The manuscript was rendered and every page visually reviewed. `delivery_checks.json` records the document checks and confirms that the external experiment's frozen code, protocol and models were unchanged. Public files exclude raw recordings, individual predictions, participant identifiers and trained bundles.
