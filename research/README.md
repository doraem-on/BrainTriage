# BrainTriage measured-data research

Start with extension_v3/README.md for the current nested-selection extension and extension_v2/README.md for the completed earlier study. The application demonstration is separate from these experiments: synthetic PET and cross-person modality combinations are not research evidence.

The v2 study includes measured OASIS, CSF and EEG data, 16 local fitted bundles, a twelve-page manuscript and ten figures. Its method did not reliably outperform baselines. Earlier holdouts are exposed and are not reused in v3. The v3 protocol is committed before its performance evaluation; its development analysis remains exploratory because earlier findings informed it.

Use src/acquire_data.py for clinical source acquisition and the v2 EEG helper for OpenNeuro data, subject to provider terms. Public source defaults to this research/data_raw directory for portability; the original local pilot used an environment-specific fallback. BRAINTRIAGE_SOURCE overrides either. Raw patient data, individual predictions, credentials and fitted bundles containing training IDs are excluded from this research directory.

Author: Lalit Kishore R, Department of Computer Science and Engineering, Thapar University. Correspondence: lr_be24@thapar.edu.

No clinical validation, ethics approval or publication acceptance is asserted. AI assistance supported implementation, analysis and drafting; author verification and venue disclosure remain required.


The completed v3 study adds 108 outer pipeline fits, nine local frozen bundles, a seven-page manuscript, four figures and all aggregate outcomes. On the small EEG development cohort, rich blended nonlinear acquisition reduced mean Brier from 0.1789 (fixed uncertainty) to 0.1662. It did not consistently beat matched uncertainty across repeats, a ridge gate scored slightly better, and missed AD cases increased relative to the fixed baseline. The clinical cohorts did not consistently improve. This is exploratory evidence, not state-of-the-art or external validation.

Artifacts:
- [Current manuscript](extension_v3/manuscript/nested_model_research_update.docx)
- [Current results and reproduction](extension_v3/README.md)
- [Earlier manuscript](extension_v2/manuscript/measurement_benefit_manuscript.docx)
- [Current figures](extension_v3/figures)

Figures and manuscript builders can run from the published aggregate tables without participant data. Training and numerical model verification require independently acquired source data and locally regenerated model artifacts. The repository excludes those participant-level artifacts.
