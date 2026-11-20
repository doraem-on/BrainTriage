"""Create the standalone research manuscript from recorded aggregate results."""
from pathlib import Path
import csv,json
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH

ROOT=Path(__file__).resolve().parents[1]
def read(name):
    with open(ROOT/'results'/name) as f:return list(csv.DictReader(f))
summary=read('holdout_summary.csv');contrasts=read('paired_contrasts.csv')
COHORTS={'oasis2':'OASIS 2','oasis1':'OASIS 1','csf':'CSF','eeg_ad_ftd':'EEG AD vs FTD'}
def result(c,p):return next(r for r in summary if r['cohort']==c and r['config']=='logistic' and r['policy']==p)
def value(c,p,k='brier',digits=4):return f"{float(result(c,p)[k]):.{digits}f}"
def contrast(c):return next(r for r in contrasts if r['cohort']==c and r['config']=='logistic' and r['contrast']=='bayes_lcb_1 minus bayes_mean')

doc=Document();section=doc.sections[0]
section.page_width=Inches(8.27);section.page_height=Inches(11.69)
section.top_margin=section.bottom_margin=Inches(.65)
section.left_margin=section.right_margin=Inches(.75)
for name,size in [('Normal',11),('Title',20),('Heading 1',14),('Heading 2',11.5),('Caption',9)]:
    style=doc.styles[name];style.font.name='Times New Roman';style.font.size=Pt(size);style.font.color.rgb=RGBColor(0,0,0)
    style.paragraph_format.space_after=Pt(5);style.paragraph_format.line_spacing=1.03
    if name.startswith('Heading'):style.paragraph_format.space_before=Pt(8)
    if name=='Caption':style.font.bold=False;style.font.italic=False
for style in doc.styles:
    for border in list(style.element.iter(qn('w:pBdr'))):border.getparent().remove(border)
    rf=style.element.get_or_add_rPr().find(qn('w:rFonts'))
    if rf is not None:
        for key in list(rf.attrib):
            if 'theme' in key.lower():del rf.attrib[key]
doc.core_properties.author='Lalit Kishore R'
doc.core_properties.title='Estimating measurement benefit and referral uncertainty in dementia assessment'
doc.core_properties.subject='Mathematical formulation and retrospective evaluation on measured clinical and EEG data'
footer=section.footer.paragraphs[0];footer.alignment=WD_ALIGN_PARAGRAPH.CENTER
field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');footer._p.append(field)
def p(text,style=None):
    after_table=doc.element.body[-2].tag==qn('w:tbl') if len(doc.element.body)>1 else False
    pp=doc.add_paragraph(text,style)
    if after_table:pp.paragraph_format.space_before=Pt(5)
    return pp
def h(text):return doc.add_heading(text,1)
def sub(text):return doc.add_heading(text,2)
def page():doc.add_page_break()
def eq(text):
    pp=p(text);pp.paragraph_format.left_indent=Inches(.2);pp.paragraph_format.space_after=Pt(7)
    for run in pp.runs:run.font.name='Cambria Math';run.font.size=Pt(11)
def table(headers,rows,widths):
    t=doc.add_table(rows=1,cols=len(headers));t.autofit=False
    for col,w in zip(t.columns,widths):col.width=Inches(w)
    for cell,text in zip(t.rows[0].cells,headers):cell.text=text
    for row in rows:
        for cell,text in zip(t.add_row().cells,row):cell.text=str(text)
    repeat=OxmlElement('w:tblHeader');t.rows[0]._tr.get_or_add_trPr().append(repeat)
    for i,row in enumerate(t.rows):
        row._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))
        for cell,w in zip(row.cells,widths):
            cell.width=Inches(w)
            for pp in cell.paragraphs:
                pp.paragraph_format.space_after=Pt(4);pp.paragraph_format.space_before=Pt(4)
                for run in pp.runs:run.font.size=Pt(9);run.bold=(i==0)
            if i==0:
                shade=OxmlElement('w:shd');shade.set(qn('w:fill'),'EEEEEE');cell._tc.get_or_add_tcPr().append(shade)
    borders=OxmlElement('w:tblBorders')
    for edge in ['top','bottom','left','right','insideH','insideV']:
        b=OxmlElement('w:'+edge);b.set(qn('w:val'),'single');b.set(qn('w:sz'),'4');b.set(qn('w:color'),'BBBBBB');borders.append(b)
    t._tbl.tblPr.append(borders)
    return t
def figure(name,caption,width=6.6):
    pp=p('');pp.alignment=WD_ALIGN_PARAGRAPH.CENTER;pp.paragraph_format.space_after=Pt(2);pp.paragraph_format.keep_with_next=True
    pic=pp.add_run().add_picture(str(ROOT/'figures'/f'{name}.png'),width=Inches(width))
    pic._inline.docPr.set('descr',caption)
    p(caption,'Caption')

p('Estimating measurement benefit and referral uncertainty in dementia assessment','Title')
p('Lalit Kishore R')
p('Department of Computer Science and Engineering, Thapar University\nCorrespondence: lr_be24@thapar.edu')
h('Abstract')
p('Background: A useful acquisition policy must estimate whether an additional measurement will improve prediction. A confident estimate of benefit can still be inaccurate, and uncertainty in a learned referral ranking is rarely visible in headline classification results. We examined whether a conditional posterior uncertainty penalty improves budgeted acquisition in small dementia datasets.')
p('Methods: Separate analyses used OASIS 2 (150 participants), OASIS 1 (198), a measured cerebrospinal-fluid cohort (178), and newly acquired OpenNeuro EEG recordings from 36 participants with Alzheimer disease and 23 with frontotemporal dementia. EEG features were computed from measured signals, with one row per person. We derived equal-cost allocation and regret results and fitted calibrated logistic and additive spline classifiers, Bayesian and ridge benefit gates, an information comparator, and calibration and MMSE ablations. Development used nested patient-level cross-fitting. Three earlier holdouts were explicitly exploratory; the EEG task had a fresh 18-person holdout.')
primary=contrast('oasis2')
p(f'Results: At nominal 30% capacity, the uncertainty-adjusted minus posterior-mean Brier difference in OASIS 2 was {float(primary["difference"]):.5f} (conditional 95% bootstrap interval {float(primary["low"]):.5f} to {float(primary["high"]):.5f}). No consistent advantage appeared across cohorts. In EEG, both rules selected the same 5 of 18 participants and had Brier score {value("eeg_ad_ftd","bayes_lcb_1")}, versus {value("eeg_ad_ftd","advanced")} with acquisition for all; they missed two AD cases versus one with full acquisition. Development-only referral stability improved for EEG but deteriorated in both OASIS cohorts. Removing MMSE worsened development Brier scores in all four cohorts.')
p('Conclusions: Conditional uncertainty adjustment did not reliably improve held-out acquisition performance. Stability, probabilistic accuracy and missed-case counts measure different properties and should be evaluated separately. The findings support a reproducible failure analysis and motivate independent validation, without establishing a clinically useful referral rule.')
p('Keywords: dementia; active feature acquisition; Bayesian regression; Brier score; EEG; referral stability')
h('1 Introduction')
p('Additional measurements are valuable when they change prediction in a useful direction. A model may become more confident after observing MRI summaries, CSF biomarkers or EEG features while making a larger error. Even a gate trained directly on error reduction may learn an unstable ranking from noisy, cross-fitted targets. We therefore ask whether penalizing uncertainty in estimated benefit improves allocation under an identical capacity constraint. Our contribution is an explicit decision-theoretic formulation and a controlled empirical comparison, including negative findings and source-level provenance.')

page();h('2 Related work and research question')
p('Hou, Tang and Jin describe adaptive dementia triage based on predicted confidence gain [1]. We retain a continuous confidence-gain comparator while examining expected loss reduction and uncertainty in its estimation. The tasks, data and gate implementation differ, so our numerical results are not a reproduction or direct performance comparison with that framework.')
p('Information-based acquisition is established in EDDI [2] and generative surrogate methods [3]. Acquisition Conditioned Oracle addresses nongreedy acquisition [4], while explainability-based ranking [5] and Learning-To-Measure [6] extend individualized acquisition. POSEIDON applies adaptive marker sequencing to dementia assessment [7]. These studies preclude a claim that adaptive measurement selection or uncertainty-guided acquisition is new. Our narrower question concerns whether subtracting conditional posterior mean uncertainty helps a simple benefit gate at fixed panel capacity. The Gaussian information comparator and retrospective outcome-informed oracle are not implementations of those published algorithms.')
h('3 Cohorts and measured inputs')
p('We analyzed each cohort separately using recorded outcomes and within-person basic and advanced measurements. OASIS endpoints represent concurrent Clinical Dementia Rating (CDR) greater than zero, not biomarker-confirmed Alzheimer disease or future progression [8,9]. Provider guidance discourages combining OASIS releases [17]; their results are not pooled or treated as independent external validation.')
p('Table 1. Analysis populations and participant partitions. Positive class is CDR > 0 in OASIS and recorded AD in the other tasks. Basic features include age, recorded sex and MMSE; OASIS additionally includes socioeconomic status, and OASIS 2 includes education.','Caption')
table(['Cohort','Analysis N\nPositive N','Development\nHoldout','Advanced panel','Task'],[
['OASIS 2','150 / 65','120 / 30','eTIV and nWBV','Earliest visit CDR > 0'],
['OASIS 1','198 / 100','158 / 40','eTIV and nWBV','Age 60 or older CDR > 0'],
['CSF','178 / 91','142 / 36','Amyloid, total tau, phosphorylated tau','AD versus MCI'],
['EEG','59 / 36','41 / 18','20 regional spectral features','AD versus FTD']],
[.8,.95,1.05,2.05,1.9])
p('The CSF analysis retains symptomatic participants with all three biomarkers [10,11]. Its downloaded clinical table contains 212 records, compared with 213 participants in the source publication; source-repository bytes could not be checked directly. Public-mirror hashes are documented. Complete-panel selection may introduce bias. Missing basic inputs are imputed within training folds; missing advanced panels are not fabricated.')
sub('3 1 EEG acquisition and feature extraction')
p('OpenNeuro ds004504 provides measured scalp EEG from the AHEPA cohort [12–14]. We used all 36 AD and 23 FTD participants and excluded 29 healthy controls to focus on symptomatic differential diagnosis and avoid the documented MMSE ceiling among controls. From each provider-denoised recording, the first 120 seconds were analyzed at 500 Hz using Welch spectra with a 2-second Hann window, 50% overlap and constant detrending. Delta 0.5–4, theta 4–8, alpha 8–13 and beta 13–30 Hz power was normalized over 0.5–30 Hz. Mean channel-relative power within five fixed regions was log-transformed, yielding 20 features per participant.')
p('Regions were frontal (Fp1, Fp2, F7, F3, Fz, F4, F8), central (C3, Cz, C4), temporal (T3, T4, T5, T6), parietal (P3, Pz, P4), and occipital (O1, O2). Flat channels were excluded within regions. Exact source windows were downloaded by byte range; 236 range checksums and metadata were retained. Features matched complete-file extraction exactly for three checked recordings. Epochs were never split across patients or treated as independent observations.')

page();h('4 Mathematical formulation')
p('Let X denote basic inputs, Z an advanced panel and Y a binary recorded outcome. Fix fitted predictors p₀(X) and p₁(X,Z) when evaluating a batch. Define expected Brier improvement conditional on the information available before acquisition:')
eq('G(x) = E[(Y − p₀(x))² − (Y − p₁(x,Z))² | X = x].                                      (1)')
p('G is a predictive-loss difference, not a causal treatment effect. Its realized training target requires Y and Z; the deployment score uses X alone. A confidence target is different: if Y = 1, p₀ = 0.4 and p₁ = 0.1, distance from 0.5 rises from 0.1 to 0.4 while squared error rises from 0.36 to 0.81. This counterexample does not prove that an estimated loss target generalizes better.')
sub('4 1 Equal cost allocation')
p('Proposition 1. Suppose each panel has equal cost, exactly k of n participants must be selected, and each participant has a fixed separable conditional benefit Gᵢ. The optimal set consists of the k largest Gᵢ.')
eq('R(S) = Σᵢ E[(Yᵢ − p₀(Xᵢ))² | Xᵢ] − Σᵢ∈S Gᵢ,     |S| = k.                          (2)')
p('Proof. The first sum is independent of S. Replacing a selected lower gain with an unselected higher gain cannot increase risk. If acquisition is optional up to k panels, retain only positive gains. A constant acquisition penalty c replaces Gᵢ by Gᵢ − c. Unequal costs under a total budget generally yield a knapsack problem; a simple benefit-to-cost ranking is not asserted to be optimal.')
sub('4 2 Sensitivity to estimation error')
p('Proposition 2. If |Ĝᵢ − Gᵢ| ≤ ε for all n candidates, S* maximizes true benefit, and Ŝ maximizes estimated benefit over sets of size k, then:')
eq('0 ≤ R(Ŝ) − R(S*) ≤ 2kε.                                                                          (3)')
p('Proof. Add and subtract estimated gains in Σᵢ∈S*Gᵢ − Σᵢ∈ŜGᵢ. The two estimation-error sums are each at most kε; the remaining estimated-gain difference is nonpositive by optimality of Ŝ. The average-loss bound is 2kε/n. We do not establish a uniform ε empirically, so this is an explanation of ranking sensitivity rather than a performance certificate.')
sub('4 3 Brier value of information')
p('Proposition 3. If the predictors are coherent Bayes probabilities η₀ = E[Y|X] and η₁ = E[Y|X,Z], the expected Brier improvement is:')
eq('G Bayes(x) = Var(η₁(X,Z) | X = x) ≥ 0.                                                      (4)')
p('Proof. Squared-loss risk of a conditional mean is conditional variance. Subtract E[Var(Y|X,Z)|X] from Var(Y|X) and apply the law of total variance. Practical separately fitted predictors need not satisfy coherence or calibration, so their expected gain may be negative. Individual realized gains can be negative even under the Bayes assumptions. These propositions are elementary decision-theoretic derivations, not claims of new general theorems.')
sub('4 4 Conditional posterior uncertainty')
p('A Bayesian linear gate fits cross-fitted gains gᵢ = φ(Xᵢ)ᵀβ + eᵢ with Gaussian noise, an isotropic Gaussian coefficient prior and empirical-Bayes precisions. Standardized basic inputs and an explicit constant form φ. For posterior mean m and covariance Σ:')
eq('μ(x) = φ(x)ᵀm,     s(x) = √[φ(x)ᵀΣφ(x)],     aκ(x) = μ(x) − κs(x).                (5)')
p('We compare κ = 0, 0.5, 1 and 2, with κ = 1 versus 0 as the principal extension contrast. Here s measures uncertainty in the conditional mean, excluding observation noise and upstream classifier, calibration and cross-fitting uncertainty. The adjusted score is a heuristic, not a distribution-free confidence bound or conformal risk guarantee [15].')

page();h('5 Model fitting and evaluation')
sub('5 1 Patient partitions and nested estimation')
p('The original stratified partitions were retained for OASIS and CSF. Their earlier test outcomes were known before this extension, so reuse is exploratory. EEG received a new stratified 70/30 partition with seed 20261121, producing 41 development and 18 holdout participants, including 11 AD and 7 FTD holdout cases. Refitting for AD versus FTD evaluates feasibility on a new task; it does not externally validate an MRI classifier. The extension protocol was specified locally before its performance evaluation, after the original results were known. It was not publicly preregistered.')
p('Development used three repeats of four outer folds. Within each outer training set, three-fold cross-fitting generated paired basic and advanced probabilities and gain targets. Each classifier used three-fold sigmoid calibration confined to its training data, with ensemble=False. Imputation, scaling and conditional feature fitting were also training-only. Outer predictions were combined within a repeat and ranked as one evaluation batch. Final models used all development participants; holdout configurations were evaluated once without outcome-based tuning.')
sub('5 2 Classifiers and acquisition rules')
p('The main classifier was logistic regression with C = 1. The nonlinear alternative used quadratic additive splines with three training-quantile knots per continuous input, linear extrapolation and C = 0.5; recorded sex entered linearly. Both used standardization and a 2000-iteration limit. Median imputation preceded continuous transformations; the spline binary input used most-frequent imputation. Two ablations removed sigmoid calibration or MMSE. Four configurations across four cohorts produced sixteen final fitted bundles, including gates and conditional feature models.')
p('Ridge gates with penalty 10 learned either Brier gain g or confidence gain |p₁ − 0.5| − |p₀ − 0.5|. Comparators ranked by basic risk, proximity to 0.5, Bayesian posterior mean, adjusted scores, or random scores averaged over 30 draws. A training-only ridge model estimated standardized advanced features given basic inputs, with Ledoit–Wolf residual covariance. For 32 Gaussian integration draws, the information score was H(mean p₁) − mean H(p₁), where H is Bernoulli entropy. This simplified generative comparator does not reproduce EDDI, GSMRL or Learning-To-Measure [2,3,6]; its draws are not training patients.')
p('A policy replaces p₀ with p₁ for the top floor(qn) scores, using stable participant ordering for ties. Budgets were 0, 0.1, 0.2, 0.3, 0.5, 0.75 and 1. The primary capacity was 0.3; probabilities were thresholded at 0.5 except in cost scenarios. An outcome-informed oracle ranked realized Brier gains only as a retrospective bound. It is unavailable prospectively and is not the Acquisition Conditioned Oracle method [4].')
sub('5 3 Secondary experiments and inference')
p('Learning curves retained 50%, 75% or 100% of outer training participants. Stability used twenty complete pipeline refits on 80% stratified subsamples without replacement, within a development-only training group; a fixed 25% development validation group supplied referral Jaccard overlaps. Missingness at 10% or 30% and Gaussian noise at 0.1 or 0.3 training standard deviations perturbed continuous basic evaluation inputs, with one fixed realization per outer fold and condition. Measured advanced values remained unchanged.')
p('For false-negative weight w ∈ {1,2,5,10}, decisions used threshold 1/(1+w). A separate ridge gate learned cross-fitted weighted-error reduction and acquired when predicted reduction exceeded c ∈ {0,0.01,0.05,0.1,0.2,0.5}. The objective was mean weighted classification error plus c times referral fraction. These hypothetical false-positive-error units are not clinical utilities or currency.')
p('The main metric was Brier score. AUROC, precision-recall area, log loss, classification errors and acquisition counts were retained. Paired 95% intervals used 2000 class-stratified patient bootstraps, conditional on fixed models and realized allocations; no retraining or reranking occurred. Development repeats and stability pairs are dependent and descriptive. Secondary comparisons are exploratory without multiplicity-adjusted superiority claims. Reporting follows relevant TRIPOD+AI principles [16].')

page();h('6 Held out results')
p('The conditional uncertainty penalty did not produce a consistent Brier improvement over the posterior mean. OASIS 2, OASIS 1 and CSF intervals included zero; the EEG predictions were identical for the two policies at 30% capacity. A degenerate zero interval in that setting reflects identical realized predictions, not population equivalence or absence of training uncertainty.')
p('Table 2. Logistic Brier scores at nominal 30% capacity, except basic-only and full acquisition. Intermediate policies acquire 9/30 OASIS 2, 12/40 OASIS 1, 10/36 CSF and 5/18 EEG panels. Lower is better. Earlier cohort holdouts are exploratory.','Caption')
policies=['basic','advanced','uncertainty','bayes_mean','bayes_lcb_1','information']
table(['Cohort','Basic','Full','Uncertainty','Bayes mean','Adjusted','Information'],[[label]+[value(c,pol) for pol in policies] for c,label in COHORTS.items()],[1.25,.75,.75,1,.9,.9,1.2])
p('Table 3. Adjusted minus Bayesian mean Brier contrasts for the main logistic configuration. Intervals condition on fitted models and the observed referral assignment.','Caption')
table(['Cohort','Difference','95% interval'],[[label,f"{float(contrast(c)['difference']):+.5f}",f"[{float(contrast(c)['low']):+.5f}, {float(contrast(c)['high']):+.5f}]"] for c,label in COHORTS.items()],[1.7,1.5,3.55])
figure('paired_contrasts','Figure 1. Paired contrasts across four configurations. Red identifies the main logistic configuration; gray identifies alternatives and ablations. Panel scales differ. EEG zero-width intervals arise from identical realized policy predictions.',6.35)

page();h('7 Capacity and diagnostic errors')
p('More acquisition did not uniformly reduce empirical loss. Uncertainty routing was competitive in OASIS; full acquisition had a lower point Brier score than partial acquisition in CSF. Oracle curves require knowledge of realized gains and are unavailable prospectively. No capacity was selected from holdout results.')
figure('capacity_brier','Figure 2. Logistic Brier scores against realized panel acquisition. The outcome-informed oracle uses evaluation outcomes and is diagnostic only. Curves are point estimates; panel scales differ. OASIS and CSF holdouts were previously exposed.')
p(f'For EEG, basic-only, full acquisition and adjusted acquisition had Brier scores {value("eeg_ad_ftd","basic")}, {value("eeg_ad_ftd","advanced")} and {value("eeg_ad_ftd","bayes_lcb_1")}, respectively. Adjusted and mean acquisition selected the same five participants. Their favorable point Brier score relative to full acquisition did not imply fewer missed AD cases: both missed two of eleven positives, compared with one under full acquisition. Their AUROC was {value("eeg_ad_ftd","bayes_lcb_1","auroc")}, compared with {value("eeg_ad_ftd","advanced","auroc")} under full acquisition. These small-sample differences establish neither superiority nor noninferiority.')
p('In OASIS 1, uncertainty routing improved Brier score relative to basic-only prediction but increased missed positives from three to four. Thus an average probabilistic improvement can coexist with a worse clinically relevant error count. The missed-case curves and calibration plots in Supplement A retain that distinction. Sparse holdout bins prevent a strong calibration conclusion.')
h('7 1 Development evidence')
p('Figures 3–8 examine estimation behavior without selecting models from held-out outcomes. Learning curves generally favored more training data, but their ranges span only three correlated repeats. The spline alternative had higher mean development Brier scores than calibrated logistic regression in all four cohorts under adjusted routing. Removing MMSE also worsened scores in every cohort. This indicates strong dependence on cognitive assessment and raises concern about diagnostic incorporation; it does not establish a causal contribution of MMSE.')
p('The penalty increased mean EEG referral Jaccard overlap from 0.211 to 0.409, versus 0.416 for uncertainty routing. It reduced overlap in OASIS 2 (0.534 to 0.492) and OASIS 1 (0.610 to 0.518); CSF changed little (0.572 to 0.575). These dependent-pair summaries are descriptive.')

page();h('8 Training size and model ablations')
figure('learning_curves','Figure 3. Development learning curves for logistic models at 30% acquisition capacity. Lines are mean Brier scores; shading spans three correlated repeats and is not a confidence interval. Training subsets are stratified and contain distinct participants.',6.25)
figure('ablations','Figure 4. Classifier and ablation comparison under uncertainty-adjusted acquisition. Gray dots denote development repeats; red bars denote their mean. No configuration was selected using holdout results. Removing MMSE worsened average Brier score in every cohort.',6.25)

page();h('9 Referral stability and estimated benefit')
figure('referral_stability','Figure 5. Development-only referral stability from twenty full pipeline refits. Each box contains 190 dependent pairwise Jaccard overlaps; medians and interquartile ranges are descriptive. Whiskers follow the 1.5 IQR rule; outlier points are omitted visually. Higher overlap does not imply lower predictive loss.',6.25)
figure('benefit_reliability','Figure 6. Predicted versus observed Brier gain in four within-repeat development quartiles. Points average three repeats; bars span their range. The dashed line denotes agreement. Nonmonotonic observed gains and negative EEG averages expose limits of benefit estimation.',6.25)

page();h('10 Input perturbations and hypothetical costs')
figure('robustness','Figure 7. Mean development Brier score under controlled perturbations of basic inputs. Missingness particularly degraded OASIS results. These simulated conditions use one fixed realization per fold and level; they do not establish performance under clinical distribution shift.',6.25)
figure('cost_sensitivity','Figure 8. Weighted-error-plus-acquisition-cost objective of the separate cost gate minus basic-only prediction. Negative values favor acquisition. The gate did not consistently improve outcomes; EEG differences were nonnegative throughout. Weights and costs are hypothetical, and large-cost zero differences can result from acquiring no panels.',6.25)

page();h('11 Discussion')
p('The formulation separates the value of a measurement from confidence in a prediction and from uncertainty in an estimated value. Under known separable gains, top-k allocation is straightforward. The practical difficulty is learning those gains from small datasets. Cross-fitted targets avoid direct in-sample prediction reuse, but they remain noisy functions of fitted classifiers, calibration and outcomes. A conditional Bayesian penalty addresses only part of that uncertainty.')
p('The results do not support a general advantage for the penalty. EEG showed a development stability improvement relative to the posterior mean, yet no change in the primary holdout allocation. Both OASIS cohorts showed worse stability. The reliability plots also show that larger predicted gains did not consistently correspond to larger observed gains. Penalizing an uncertain estimate cannot correct every form of model misspecification or systematic bias.')
p('Removing MMSE reduced performance across tasks, indicating substantial dependence on cognitive measurements. Nonlinear modeling alone does not establish independent diagnostic information. A gate can also fail when its target matches a stated cost objective: no EEG cost scenario improved that objective relative to basic-only prediction.')
sub('11 1 Limitations')
p('The cohorts are small convenience samples, with 18–40 holdout participants per task. One changed prediction can materially alter sensitivity. Three holdouts were exposed in earlier work; their reuse cannot supply confirmatory evidence. The EEG holdout is new but comes from one source and tests a different endpoint with refitted models. The OASIS releases may overlap and are not independent external cohorts. No result estimates prospective Alzheimer progression, population screening performance or clinical cost savings.')
p('Recorded diagnoses may incorporate cognitive or biomarker information related to the predictors. Case mix, complete-panel inclusion and retrospective masking can produce incorporation, spectrum and selection biases. MRI inputs comprise two volumetric summaries, not image-based models. EEG uses a fixed short window of provider-denoised signals and simple regional spectra. The conditional Gaussian model is an approximation for correlated bounded powers and non-Gaussian biomarkers. No fairness or transportability claim is supported.')
p('Posterior mean uncertainty excludes upstream uncertainty, and bootstrap intervals omit refitting and reallocation. Fixed-model intervals can collapse when policies choose the same people. Development repeats and stability pairs are correlated, while stress tests use limited perturbation realizations. Multiple exploratory comparisons increase the opportunity for favorable chance findings. Future evaluation requires an independently acquired cohort, a clinically justified referral objective, prospectively fixed analysis and adequate power.')
h('12 Conclusion')
p('Conditional uncertainty adjustment did not reliably improve acquisition performance in this measured-data benchmark. It changed referral stability differently across cohorts, and favorable Brier scores could coexist with additional missed positives. The mathematical formulation, trained models, provenance and complete negative results provide a basis for replication and stronger validation, rather than a clinically validated acquisition policy.')
h('Data and code availability')
p('Source protocols, acquisition code, aggregate results and figures accompany the manuscript. OASIS, the CSF repository and OpenNeuro sources are cited in [8–12,17]. EEG metadata identify CC0; CSF terms identify CC BY-NC-ND 4.0. Source-specific conditions apply. Raw participant data, participant-level predictions and fitted bundles remain outside the shareable package. This secondary analysis involved no new recruitment or intervention; no new ethics approval is asserted.')
h('Acknowledgments and AI assistance')
p('We acknowledge the OASIS, clinical lipidomics and AHEPA EEG data contributors, including the dataset studies [12–14]. AI assistance supported literature synthesis, code, analysis, figures and drafting. The named author is responsible for final verification and venue-required disclosure.')

page();h('References')
for ref in json.loads((ROOT/'literature.json').read_text()):
    pp=p(f"[{ref['id']}] {ref['reference']} {ref['url']}")
    pp.paragraph_format.space_after=Pt(7)
    for run in pp.runs:run.font.size=Pt(9.5)

page();h('Supplement A Missed positives and calibration')
figure('capacity_missed','Figure A1. Missed positives at probability threshold 0.5 across capacity levels. The oracle optimizes realized Brier gain, not missed-case count, and uses outcomes unavailable prospectively. Classification error and probabilistic loss need not improve together.',6.25)
figure('calibration','Figure A2. Descriptive calibration at nominal 30% capacity for adjusted routing, with basic-only and full-acquisition endpoints. Bins have width 0.2; only occupied bins are shown. Small counts and fixed fitted models limit interpretation. No calibration superiority is asserted.',6.25)

out=ROOT/'manuscript';out.mkdir(exist_ok=True)
path=out/'measurement_benefit_manuscript.docx';doc.save(path)
print(path)
