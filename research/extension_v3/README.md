# Improving the measured data research models

This is a research-paper extension, with a fixed experiment matrix and publication of unfavorable results. It tests richer EEG measurements, nested model selection and shrinkage of advanced predictions. It does not guarantee that a method will beat baselines. The preceding twelve-page manuscript and all v1/v2 outcomes are preserved.

## Research question

Can training-only regularization and a learned basic/advanced probability blend improve feature acquisition more reliably than adding a posterior penalty to a linear benefit gate?

The closest ADNI triage paper establishes the basic/advanced/gate framework. Recent EEG studies motivate spectral ratios, compact complexity summaries and band-specific covariance representations. `literature.json` records seven methodological sources and distinguishes our adaptations from exact replications. These ingredients already exist in the literature; the contribution under examination is their controlled combination, error analysis and capacity-matched comparison. We do not claim a first-ever algorithm or compare our AD/FTD scores directly with published AD/healthy-control scores.

## Validation boundary

Only the original development participants are used. All earlier holdouts, including the eighteen-person EEG holdout, are now exposed and are not evaluated again here. Three repeats of four outer folds contain all selection, calibration, gain-target cross-fitting and blend fitting. These are exploratory development estimates because the datasets and previous results informed the extension. An independently acquired cohort is still needed for a confirmatory claim. The user currently has no approved ADNI access; no restricted ADNI measurements are downloaded or fabricated.

The fixed primary comparison is nonlinear benefit ranking versus uncertainty ranking with identical tuned classifiers and nominal 30% acquisition capacity. Stronger base prediction alone is not evidence that the referral mechanism improved. Every raw/blended and original/rich configuration is retained.

## Mathematical addition

For paired training probabilities, define d_i=p_a,i-p_b,i and q_i(alpha)=p_b,i+alpha*d_i. The cross-fitted empirical Brier objective is a convex quadratic:

L(alpha) = mean((y-p_b)^2) - 2*alpha*mean((y-p_b)*d) + alpha^2*mean(d^2).

Its minimizer over [0,1] is alpha=clip(sum((y-p_b)*d)/sum(d^2),0,1). A denominator at most 1e-12 uses alpha=0. For a denominator above that numerical threshold, on those particular cross-fitted predictions the fitted loss cannot exceed either endpoint, because both endpoints are in the feasible set. This does **not** guarantee improvement for final refitted models or new participants. Only the outer validation predictions assess generalization of the blending procedure.

## Reproduction

Retain this directory inside the parent research package, alongside `extension_v2`. Use the pinned numerical requirements in the parent directory. Obtain the original clinical tables with `src/acquire_data.py`, set `BRAINTRIAGE_SOURCE` to that data directory, and acquire EEG with `extension_v2/src/acquire_eeg.py`. From a fresh copy with no v3 outputs:

```sh
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
python extension_v3/src/extract_features.py
python -m unittest discover -s extension_v3/tests -v
python extension_v3/src/experiment.py
python extension_v3/src/report.py
```

Actual source records and participant-level artifacts stay local. GitHub receives source code, public-source provenance, aggregate outputs and manuscript artifacts. `protocol.json` is committed before v3 performance evaluation. The analysis remains exploratory rather than publicly preregistered, since earlier results already informed it.


## Completed results

The fixed matrix completed 108 outer pipeline fits, nine final development-fitted bundles and 2,352 aggregate metric rows, with zero earlier-holdout evaluations. Five scientific tests passed. All 48 outer partitions and 42 prediction files passed the development-only audit. Independent arithmetic reproduced the 18 final calibrated classifiers within 2.11e-15. Runtime warning counts are retained in results/runtime_warnings.json; verification does not cover every intermediate BLAS calculation.

Mean Brier scores at nominal 30% capacity (lower is better):

| Cohort | Fixed uncertainty | Matched tuned uncertainty | Tuned nonlinear gain |
| --- | ---: | ---: | ---: |
| OASIS 2 | 0.1223 | 0.1278 | 0.1268 |
| OASIS 1 | 0.1377 | 0.1394 | 0.1410 |
| CSF | 0.1590 | 0.1637 | 0.1661 |
| EEG AD vs FTD | 0.1789 | 0.1742 | 0.1662 |

The rich EEG pipeline beat fixed uncertainty in all three repeats, but its matched-comparator advantage appeared in only one repeat. The mean matched difference was -0.00801, spanning -0.02476 to +0.00070 across correlated repeats. Rich blended ridge acquisition scored 0.1656, slightly better than the nonlinear policy; full acquisition scored 0.1648 with every EEG acquired. Mean missed AD cases were 3.33 for the new nonlinear policy versus 2.33 for fixed uncertainty, among 25 positives per repeat. There is no uniform superiority or clinical safety claim.

Covariance/PCA classifiers were selected in all twelve rich EEG outer fits. Full-acquisition Brier improved from 0.2510 for tuned original features to 0.1655 for tuned rich features without blending. Adding blending to rich nonlinear acquisition did not improve its mean Brier (0.1659 raw, 0.1662 blended). The clinical cohorts did not beat the fixed uncertainty baseline. All variants remain available in results/aggregate_metrics.csv; no unfavorable configuration was removed.

Read manuscript/nested_model_research_update.docx for the seven-page research update with thirteen references. Four scientific figures are available as PNG and vector PDF in figures/. Rebuild them with `python extension_v3/src/figures.py` and the document with `python extension_v3/src/build_manuscript.py`. The earlier v2 manuscript is preserved separately.

Next scientific step: obtain an independent cohort with paired cognitive/EEG measurements and the same AD/FTD endpoint, then lock the representation, routing comparator, capacity and missed-case criterion before evaluating outcomes. ADNI progression is a different study and requires access approval and its own protocol. Further outcome-driven tuning on these participants would not provide confirmatory evidence.
