# Independent EEG companion validation and sensitivity thresholds

Two fixed studies are complete: independent AD-versus-healthy-control evaluation of newly trained EEG-only companion classifiers, and a source-only threshold intervention for the original AD/FTD task. **External validation of the unchanged v3 AD/FTD triage model is not complete.** BrainLat downloads require authorized Synapse access, which was unavailable.

## Findings

Training used 54 Greek participants (25 development AD, 29 healthy controls). Testing used 23 independent Spanish APAVA participants (12 AD, 11 controls). Earlier AD/FTD holdouts were excluded. Every prediction represents one participant, regardless of segment count.

| External model | Threshold | Missed AD / 12 | False positives / 11 | AUROC | Brier |
|---|---:|---:|---:|---:|---:|
| Spectral | 0.5000 | 2 | 1 | 0.8636 | 0.1300 |
| Spectral | Source 0.3372 | 2 | 3 | 0.8636 | 0.1300 |
| Covariance | 0.5000 | 0 | 7 | 0.8636 | 0.1772 |
| Covariance | Source 0.2200 | 0 | 7 | 0.8636 | 0.1772 |

Covariance sensitivity was 100% (Wilson 95% interval 75.8–100%), specificity 36.4% (15.2–64.6%). Its Brier loss was worse than the spectral baseline; paired conditional bootstrap difference +0.0472, interval −0.0479 to +0.1403. Zero observed misses is not a safety guarantee. Lowering thresholds recovered no additional external AD cases. No external tuning followed these results.

In the separate 41-person AD/FTD analysis, lowering training-selected thresholds reduced uncertainty-routing mean misses from 3.67 to 3.33, while false positives rose from 7 to 8. Ridge-routing misses stayed at 3, while false positives rose from 6.67 to 7. These three correlated repeats are descriptive, not independent replications. Both routing policies acquired EEG for 12/41 participants per repeat. Validation-fold batches differ from v3 pooled-repeat ranking; do not compare those numbers as a controlled version-to-version improvement.

## Provenance and limits

- Protocol pushed in `65719eb`; source model/threshold hashes and tested implementation pushed in `02d3e24` **before** external predictions. This is a frozen exploratory study, not a registered trial.
- Source: [ds004504 descriptor](https://doi.org/10.3390/data8060095). External: [Smith et al. 2017](https://doi.org/10.1371/journal.pone.0186164), [OSF data](https://osf.io/jbysn/). Archive digest appears in `results/public_provenance.json`.
- APAVA diagnosis mapping comes from the [LEAD preprocessing notebook](https://github.com/DL4mHealth/LEAD/blob/main/data_preprocessing/APAVA/APAVA_preprocessing.ipynb), blob `b6b9c130b9e519366c2844a8c203b80c9d5d8536`. Original clinical records were not available for independent confirmation. No target labels were used for fitting or selection.
- The shared adapter uses 16 observed channels, up to 24 five-second segments and one average feature vector per participant. APAVA has physician-selected trials; eight participants have fewer than 24 trials, including one with only one. No synthetic training data, invented cognitive measurements or interpolated channels were used.
- ds006036 shares participants with ds004504 and was rejected as independent evidence. ADSZ was not evaluated because its recording-to-person mapping was ambiguous. BrainLat metadata were inspected, but no restricted recordings were downloaded.
- APAVA's OSF metadata did not specify a license. The published release is cited; raw recordings are not redistributed. This project does not grant new rights to source data.

## Reproduction

Use a fresh working copy for an independent replication. Preserve delivered outputs and sentinels; never delete locks to optimize the published external result. The v2 source EEG acquisition and v3 development-feature steps must be completed first, following their READMEs. Those recreate the original development/holdout split and covariance features. Set `BRAINTRIAGE_SOURCE` to the legally obtained root-study input layout described in the main research README.

From `research/extension_v4`, using the recorded ML environment:

```sh
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
mkdir -p data_raw results models
python src/acquire_external.py
python src/acquire_source.py
python src/features.py
python -m unittest discover -s tests -v
python src/sensitivity.py
python src/companion.py train
# Review and archive source models, code hashes and external_freeze.json first.
python src/companion.py evaluate
python src/report.py
```

Use an artifact environment with Matplotlib and python-docx for `src/figures.py` and `src/build_manuscript.py`. Rendering the DOCX additionally requires LibreOffice and Poppler. All model training used Python 3.12.13, NumPy 2.1.1, pandas 2.2.3, SciPy 1.18.0, scikit-learn 1.5.2 and joblib 1.4.2. BLAS/platform differences can affect exact model hashes.

Five scientific tests passed. The audit checked 310 partition records and 1,632 saved source prediction rows. Independent einsum PCA/logistic calculations reproduced final predictions within 3.33e-16. Runtime matrix-multiplication warnings and an unknown `iprint` solver-option warning are recorded, not hidden. Features and predictions were finite; convergence warnings were errors. Final arithmetic checks do not independently reconstruct every intermediate fit.

## Artifacts

- `manuscript/external_eeg_validation.docx`: current eight-page research update, retaining the separate endpoints and all negative findings.
- `figures/`: four scientific figures, each as PNG and vector PDF.
- `results/external_metrics.csv`, `external_contrasts.json`: all external results and paired conditional intervals.
- `results/sensitivity_summary.csv`, `companion_development_summary.csv`: source mean/range summaries; individual repeats are also supplied.
- `results/verification.json`, `public_provenance.json`, `external_freeze.json`: audit and reproducibility evidence.
- `protocol.json`, `dataset_review.json`, `literature.json`: fixed design, dataset eligibility and references.

Raw signals, feature rows, participant predictions, partition identifiers and fitted bundles remain local and are excluded from GitHub and the shareable package. The archive contains code, aggregate evidence and manuscripts. No paper has been submitted. Submission still requires author verification of declarations, contributors, venue format and references; no funding, ethics approval or guaranteed model superiority is invented.
