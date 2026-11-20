# BrainTriage measured-data research

Start with extension_v3/README.md for the current nested-selection extension and extension_v2/README.md for the completed earlier study. The application demonstration is separate from these experiments: synthetic PET and cross-person modality combinations are not research evidence.

The v2 study includes measured OASIS, CSF and EEG data, 16 local fitted bundles, a twelve-page manuscript and ten figures. Its method did not reliably outperform baselines. Earlier holdouts are exposed and are not reused in v3. The v3 protocol is committed before its performance evaluation; its development analysis remains exploratory because earlier findings informed it.

Use src/acquire_data.py for clinical source acquisition and the v2 EEG helper for OpenNeuro data, subject to provider terms. Public source defaults to this research/data_raw directory for portability; the original local pilot used an environment-specific fallback. BRAINTRIAGE_SOURCE overrides either. Raw patient data, individual predictions, credentials and fitted bundles containing training IDs are excluded from this research directory.

Author: Lalit Kishore R, Department of Computer Science and Engineering, Thapar University. Correspondence: lr_be24@thapar.edu.

No clinical validation, ethics approval or publication acceptance is asserted. AI assistance supported implementation, analysis and drafting; author verification and venue disclosure remain required.
