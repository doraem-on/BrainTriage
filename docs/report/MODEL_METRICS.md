# Appendix C Complete model metrics

## C1 Classification and uncertainty

All figures below are development results from the installed model artifacts. Classification and acquisition use run `2.0-20261126T152602Z`. Accuracy applies to classification; regression, survival, segmentation and measurement tasks require different metrics. Dataset sizes are evaluation counts, not total training cohorts.

| Model | n | Accuracy | Macro F1 | Brier | AUROC |
| --- | --- | --- | --- | --- | --- |
| Cognitive | 64 | 65.62% | 0.5214 | 0.4271 | 0.8471 |
| Cognitive plus MRI | 64 | 65.62% | 0.5096 | 0.4309 | 0.8542 |
| Paired fusion | 64 | 68.75% | 0.5186 | 0.4150 | 0.8401 |
| CSF basic baseline | 33 | 72.73% | 0.6567 | 0.4453 | 0.7528 |
| CSF biomarkers | 33 | 66.67% | 0.4642 | 0.4154 | 0.8518 |
| EEG basic baseline | 7 | 85.71% | 0.8571 | 0.2661 | 0.9167 |
| EEG spectral | 7 | 57.14% | 0.3636 | 0.8243 | 0.5833 |

| Model | Set coverage | Mean set size | Misses | False positives |
| --- | --- | --- | --- | --- |
| Cognitive | 93.75% | 1.6875 | 19 | 0 |
| Cognitive plus MRI | 92.19% | 1.5781 | 18 | 0 |
| Paired fusion | 95.31% | 1.7500 | 14 | 1 |
| CSF basic baseline | 84.85% | 1.5758 | 0 | 2 |
| CSF biomarkers | 93.94% | 1.7273 | 1 | 3 |
| EEG basic baseline | 100.00% | 2.0000 | 1 | 0 |
| EEG spectral | 100.00% | 2.0000 | 0 | 3 |

Sets target nominal 90% marginal coverage. Both EEG sets always retain both labels, so their 100% coverage provides no selectivity. Misses count actual nonzero categories predicted as category zero; false positives count category zero predicted as nonzero. Category zero is CDR 0 for OASIS, Control for CSF and FTD for EEG. These are collapsed binary error counts, not complete multiclass confusion matrices.

The basic CSF and EEG baselines use age, sex and MMSE without their acquired biomarkers or spectral features. Their accuracy must not be attributed to the full modality models. Per-class precision/recall and confusion matrices were not saved in these artifacts and are not reconstructed from aggregate scores.

---

# Appendix C Model selection and gain estimation

## C2 Training cross validation

Classifiers were selected by the lowest fitting-partition cross-validation Brier loss. These are selection scores, not independent evaluation results. The final calibrated models are evaluated in C1. The third candidate is histogram gradient boosting for OASIS/CSF and an SVM for EEG.

| Branch | Logistic | Forest | Boost / SVM | Selected |
| --- | --- | --- | --- | --- |
| Cognitive | 0.3903 | 0.3952 | 0.4439 | logistic |
| Cognitive plus MRI | 0.3727 | 0.3746 | 0.3892 | logistic |
| CSF basic baseline | 0.4712 | 0.4634 | 0.5129 | forest |
| CSF biomarkers | 0.5021 | 0.4246 | 0.4697 | forest |
| EEG basic baseline | 0.3848 | 0.4661 | 0.6972 | logistic |
| EEG spectral | 0.3501 | 0.4443 | 0.6855 | logistic |

Paired fusion uses out-of-fold logistic probability stacking. Its manifest records no separate candidate-comparison table. It is evaluated as a complete calibrated model in C1.

## C3 Acquisition regressors

Gain is the reduction in summed Brier loss after obtaining the measurement. Mean squared error (MSE) measures error in estimating that numerical gain. Root mean squared error (RMSE) below is calculated as the square root of the saved evaluation MSE; it is not an independently measured accuracy percentage.

| Test | Selected | Ridge CV MSE | Boost CV MSE | Eval MSE | Eval RMSE |
| --- | --- | --- | --- | --- | --- |
| MRI | ridge | 0.0158 | 0.0160 | 0.0055 | 0.0743 |
| CSF | ridge | 0.0598 | 0.0623 | 0.1083 | 0.3291 |
| EEG | boosting | 0.0872 | 0.0795 | 1.3475 | 1.1608 |

The acquisition regressors use basic pre-test information. A small gain-prediction error does not by itself demonstrate useful allocation or better health outcomes. Policy-level results are reported separately in C4, with the same acquisition capacity for each policy within a cohort.

---

# Appendix C Allocation policy results

## C4 Equal capacity comparisons

These metrics evaluate the resulting predictions after a policy acquires tests for selected cases. They are not the accuracy of the gain regressor itself. Capacity is the ceiling of 30% of the evaluation cohort: 20 of 64 MRI cases, 10 of 33 CSF cases and 3 of 7 EEG cases.

| Test / policy | Acquired / n | Accuracy | Macro F1 | Brier | AUROC |
| --- | --- | --- | --- | --- | --- |
| MRI / Gain | 20/64 | 65.62% | 0.5214 | 0.4254 | 0.8463 |
| MRI / Uncertainty | 20/64 | 65.62% | 0.5096 | 0.4265 | 0.8515 |
| MRI / Risk | 20/64 | 65.62% | 0.5096 | 0.4265 | 0.8515 |
| CSF / Gain | 10/33 | 72.73% | 0.5000 | 0.4193 | 0.8131 |
| CSF / Uncertainty | 10/33 | 66.67% | 0.4576 | 0.4506 | 0.7727 |
| CSF / Risk | 10/33 | 72.73% | 0.6556 | 0.4572 | 0.7791 |
| EEG / Gain | 3/7 | 85.71% | 0.8444 | 0.3433 | 0.6667 |
| EEG / Uncertainty | 3/7 | 85.71% | 0.8444 | 0.3411 | 0.7500 |
| EEG / Risk | 3/7 | 85.71% | 0.8571 | 0.2140 | 0.9167 |

| Test / policy | Misses | False positives |
| --- | --- | --- |
| MRI / Gain | 19 | 0 |
| MRI / Uncertainty | 18 | 0 |
| MRI / Risk | 18 | 0 |
| CSF / Gain | 0 | 3 |
| CSF / Uncertainty | 1 | 3 |
| CSF / Risk | 0 | 2 |
| EEG / Gain | 0 | 1 |
| EEG / Uncertainty | 0 | 1 |
| EEG / Risk | 1 | 0 |

The collapsed error definitions are those in C1. The offline uncertainty policy ranks 1 minus the maximum class probability; the interactive planning screen uses normalised cognitive-model entropy. Learned gain has lower Brier loss for CSF in this run, approximately ties the alternatives for MRI, and loses to risk ranking for EEG. The results do not establish a consistently superior policy or financial savings.

---

# Appendix C Longitudinal and reference metrics

## C5 Similar research profiles

Artifact `oasis2-neighbours-v1` uses 112 fitting and 38 evaluation participants. The majority-class accuracy baseline is 57.89%. Outputs are uncalibrated reference comparisons.

| Mode | k | Accuracy | Balanced accuracy | Macro F1 |
| --- | --- | --- | --- | --- |
| Cognitive | 5 | 63.16% | 41.61% | 0.4144 |
| Cognitive plus MRI | 9 | 71.05% | 48.25% | 0.4750 |

Training cross-validation balanced accuracy selects k:

| Mode | k 5 | k 9 | k 15 |
| --- | --- | --- | --- |
| Cognitive | 65.70% | 63.51% | 57.64% |
| Cognitive plus MRI | 45.42% | 48.19% | 44.24% |

## C6 Survival and next MMSE

The survival forest uses 112 fitting and 38 evaluation participants from 150 people with 31 observed events. Evaluation concordance is 0.6632. Training CV concordance is 0.6144 for Cox and 0.6659 for the selected forest. Concordance measures event-time ranking, not classification accuracy.

| MMSE measure | Value |
| --- | --- |
| Forecast run | mmse-forecast-20261126T164349Z |
| Ridge / forest training CV MAE | 1.3153 / 1.3850 |
| No-change training MAE | 1.2370 |
| Ridge / no-change evaluation MAE | 1.6891 / 1.5952 |
| Evaluation sample | 42 visit pairs from 30 participants |
| Nominal / observed interval coverage | 90.00% / 95.24% |
| Interval radius / mean clipped width | 6.1832 / 8.3389 points |

The forecast did not beat the no-change baseline. Its fit/calibration/evaluation pair counts are 135/44/42 from 89/30/30 eligible participants. Predictions and intervals are bounded to 0–30. MAE is measured in MMSE points; interval coverage does not imply an accurate disease trajectory.

---

# Appendix C Measurement tools and metric definitions

## C7 Components without a local accuracy benchmark

| Component | Relevant evaluation measure | Current evidence |
| --- | --- | --- |
| SynthSeg 1.0 | Dice/IoU overlap; structure-volume error against expert labels | Template inference completed; local labelled-scan accuracy not evaluated |
| MediaPipe Hand Landmarker | Landmark error; tap-count and timing error against annotated video | Runtime integrated; saved teaching hand traces are synthetic |
| Whisper tiny.en | Word error rate or character error rate against reference transcripts | Generated speech processed; independent local transcription benchmark not recorded |
| Silero VAD | Speech-frame precision, recall and F1; interval-boundary error | Speech intervals produced; annotated local VAD benchmark not recorded |
| Isolation Forest | Anomaly precision, recall or AUROC on labelled unusual inputs | Fitted on training partitions; no labelled anomaly benchmark recorded |
| Optional hosted assistant | Task-specific answer quality and factuality evaluation | Separate optional feature; no benchmark recorded |

No percentages from another model version, published benchmark or synthetic demonstration are substituted for these missing local measurements. The Isolation Forest contamination setting of 0.05 is a fitting parameter, not 95% accuracy. Camera tracking coverage, speaking rate and tap counts are task measurements rather than disease-model accuracy.

## C8 Reading the metrics

Accuracy is the fraction of highest-probability labels that are correct. Balanced accuracy averages class recall. Macro F1 averages each class’s precision–recall harmonic mean. Higher values are better, but each emphasises a different aspect of class imbalance. AUROC measures ranking across thresholds; multiclass figures use one-versus-rest.

Brier loss is the average sum of squared class-probability errors; lower is better. MAE measures average absolute numeric error, while MSE squares errors and RMSE returns to the target’s units. Prediction-set coverage measures whether the recorded label belongs to the set; mean set size indicates how selective the set is.

Grouped Shapley is an explanation calculation, and maximum-weight matching is an optimisation procedure. Neither has a classifier accuracy. Reaction and drawing use direct timing or geometry. Their implementation checks, together with 75 backend and two geometry test passes recorded on 27 November 2026, establish software behaviour rather than clinical validity.
