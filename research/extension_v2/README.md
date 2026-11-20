# Measurement benefit and referral uncertainty

This extension adds actual model training, mathematical derivations, a new measured EEG cohort, development experiments and a separately documented holdout analysis. All artifacts from the initial study remain unchanged.

## Research contribution and limits

The central experiment compares a Bayesian estimate of expected Brier improvement with the same estimate minus one conditional posterior standard deviation. The contribution is a controlled empirical comparison and failure analysis, supported by explicit allocation and regret derivations. Active acquisition, information gain, Bayesian regression and posterior penalties are existing ideas. No first-ever algorithm, clinical safety guarantee, or state-of-the-art result is asserted.

`THEORY.md` gives three propositions with proofs: optimal equal-cost allocation; a 2k epsilon total-loss regret bound under uniform gain-estimation error; and the conditional-variance identity for the Brier value of information under coherent Bayes probabilities. These mathematical assumptions are not claimed to have been established empirically.

## Actual data and models

- Existing recorded OASIS 2, OASIS 1 and CSF clinical tables use their original participant partitions. Their earlier test results are already known; every reused holdout result is exploratory.
- New OpenNeuro **ds004504**, dataset DOI `10.18112/openneuro.ds004504.v1.0.9`, provides measured EEG recordings. The extension includes all 36 recorded AD and 23 FTD participants, excluding healthy controls. The public source license is CC0.
- Each EEG participant contributes one row of 20 measured spectral features. The first 120 seconds of the provider-denoised recording are analyzed with a 2-second Welch window and 50% overlap. Within each of five predefined scalp regions, mean channel-relative band power is computed and then log-transformed. Bands are delta 0.5–4, theta 4–8, alpha 8–13 and beta 13–30 Hz; normalization uses 0.5–30 Hz. Flat channels are excluded within a region. No epochs are treated as independent patients.
- EEG source bytes are obtained with HTTP Range requests to avoid downloading unused minutes. Per-range SHA-256, object length, ETag when available, source URL, window checksum, source duration and channel metadata are retained in `results/eeg_provenance.json`. These are **range checksums**, not whole-source-object hashes. Feature extraction was checked against complete-file extraction for three downloaded recordings and matched exactly.
- Four configurations are trained per cohort: calibrated logistic; calibrated additive spline logistic; uncalibrated logistic; and calibrated logistic without MMSE. The latter two are ablations. Sixteen final bundles include the classifiers, Bayesian and ridge gates, cost gates, and conditional feature model. No neural-network or raw-MRI-image training is claimed.
- The Gaussian draws used by the information comparator are numerical integration samples from a fitted conditional model. They are not real measurements, synthetic training participants, or substituted clinical records. Classifier training and evaluation use the measured cohort values.

Original data: [OASIS](https://sites.wustl.edu/oasisbrains/), [CSF repository](https://doi.org/10.34810/DATA614), [EEG dataset](https://openneuro.org/datasets/ds004504/versions/1.0.9), [EEG descriptor](https://doi.org/10.3390/data8060095). Source-specific terms apply. The CSF original repository could not be downloaded in the first study; its clinical subset was verified against a public mirror. OASIS releases are not combined as independent external cohorts. EEG models are refitted for AD versus FTD; this is **not external transport validation of the MRI classifier**.

## Validation and completed experiment design

The locally specified `protocol.json` predates extension performance evaluation but follows knowledge of the original study. It is not publicly preregistered. EEG receives a fresh stratified 70/30 development/holdout partition. The endpoint differs from both the OASIS and CSF tasks, so results are never pooled.

Development uses three repeats of four outer folds, with three inner folds for gain targets and three-fold sigmoid calibration. All preprocessing and conditional feature modeling are training-only. The implemented experiment matrix includes:

- 0–100% acquisition capacity curves, uncertainty/risk/confidence/ridge/Bayesian/information/random baselines, and an outcome-informed oracle shown only as a retrospective diagnostic bound.
- Learning curves retaining 50%, 75% or 100% of each outer training set.
- Calibration and MMSE ablations, plus an additive nonlinear classifier.
- Twenty complete refits per cohort on 80% development-only subsamples, with referral stability evaluated on a fixed development-only validation group. Samples are without replacement to prevent duplicate-person leakage across nested folds.
- Controlled basic-input missingness at 10% and 30%, and noise at 0.1 and 0.3 training standard deviations. These are explicitly simulated stress conditions, not newly observed patients. One deterministic perturbation realization per outer fold and level limits the scope of robustness inference.
- Hypothetical false-negative weights 1, 2, 5 and 10, and advanced-panel costs 0, 0.01, 0.05, 0.1, 0.2 and 0.5 false-positive-error units. A separate cost gate uses the corresponding cross-fitted weighted-loss targets. These are sensitivity scenarios, not clinical or monetary estimates.

Posterior gate uncertainty is conditional on fixed cross-fitted targets and empirical-Bayes hyperparameters. It excludes upstream model and calibration uncertainty. The adjusted score is not a distribution-free confidence bound. Holdout bootstrap intervals condition on the fitted models and realized referral assignments; no retraining or reranking occurs. Development repetitions and stability pairs are dependent, so their ranges and distributions are descriptive, not independent-sample confidence intervals.

## Completed findings and verification

The extension saved 16 fitted bundles and evaluated 3,696 development and 1,232 holdout policy-budget rows, plus learning, stress, stability and cost experiments. These rows are repeated analyses, not additional patients. Ten figures and the revised 12-page manuscript include unfavorable findings.

At nominal 30% capacity, the adjusted-minus-mean Brier differences were −0.00015 in OASIS 2, +0.00298 in OASIS 1 and +0.00041 in CSF; each conditional 95% interval included zero. EEG selected the same five participants under both rules, producing identical Brier scores (0.1956) and a degenerate conditional difference interval. That zero interval does not establish population equivalence. Full EEG acquisition had Brier 0.1997 but missed one AD case rather than two. No reliable superiority or clinically safe test reduction is demonstrated.

Five scientific invariant tests passed, covering allocation/regret, the Brier identity, outcome-independent gates, weighted decisions and all four patient partitions. All 16 saved bundles reproduced their recorded holdout predictions. Independent scalar probability calculations agreed within 2.23e-16; all 236 cached EEG byte ranges matched their recorded hashes, and complete-file extraction matched the range method exactly for three recordings. `results/numerical_verification.json` preserves these checks. The platform emitted matrix-multiplication runtime warnings; final outputs were finite and independently checked. This audit does not replace validation of model generalization.

## Files

- `manuscript/measurement_benefit_manuscript.docx`: revised standalone research manuscript.
- `THEORY.md`: full derivations and assumptions.
- `literature.json`: research references and their precise relationship to the implementation.
- `src/research.py`: training, gates, acquisition policies and experiments.
- `src/acquire_eeg.py` and `src/eeg_ranges.py`: source acquisition and exact signal-window feature extraction.
- `src/analyze.py` and `src/figures.py`: result summaries and ten standalone figures, each in PNG and vector PDF.
- `results/`: full aggregate outputs, conditionally paired contrasts, provenance and local patient-level audit artifacts.
- `models/`: sixteen final fitted bundles, preserved locally. Only load trusted joblib artifacts.

## Reproduce

Use Python 3.12 and the original study's pinned numerical dependencies. The extension imports the original `src/study.py`; retain this directory as `extension_v2` within the original research package. Original-data reproduction uses `BRAINTRIAGE_SOURCE` as described in the parent README. Do not delete delivered holdout sentinels or retune against these outcomes.

For a fresh reproduction, copy source, literature and protocol files into a new directory tree, excluding the delivered `results`, `models`, `figures` and data caches. From that fresh research directory:

```sh
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
python extension_v2/src/acquire_eeg.py
python extension_v2/src/research.py --mode audit
python -m unittest discover -s extension_v2/tests -v
python extension_v2/src/research.py --mode develop
python extension_v2/src/research.py --mode stability
python extension_v2/src/research.py --mode holdout
python extension_v2/src/analyze.py
python extension_v2/src/figures.py
python extension_v2/src/build_manuscript.py
```

For a fresh local reproduction, `src/verify_artifacts.py` can check saved outputs against its evaluation lock after training. It also expects the three original complete-file comparison recordings and the recorded lock; those local audit inputs are intentionally excluded from the shareable package. The delivered verification report records the completed original audit. The shareable archive includes the parent acquisition helper, protocol and `src/study.py` required by the extension, while the original pilot manuscript remains separate.

The EEG reader deliberately fails on unsupported MATLAB encodings, changed participant counts, inconsistent object identities within range reads, missing channels or insufficient signal length. If provider files change, compare the saved byte-range hashes and metadata before making any reproducibility claim. The endpoint is never read from filenames or passed as a predictor.

## Submission status

This is research software and a manuscript for author review. No paper has been submitted and no clinical deployment is authorized. Human verification of references, authorship, data use, institutional requirements, funding/conflict statements and venue-specific formatting remains necessary. AI assistance supported research, code, analysis and drafting and should be disclosed as required by the venue. No fabricated author contribution, ethics approval or funding declaration is included.
