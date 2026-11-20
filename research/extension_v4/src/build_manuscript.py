from pathlib import Path
import csv,json
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH
ROOT=Path(__file__).resolve().parents[1]
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


def read(name):
    with open(ROOT/'results'/name) as f:return list(csv.DictReader(f))
external=read('external_metrics.csv');source=read('sensitivity_summary.csv')
doc.core_properties.title='Sensitivity and cross cohort transport of EEG classifiers for Alzheimer assessment'
p(doc.core_properties.title,'Title')
p('Lalit Kishore R')
p('Department of Computer Science and Engineering, Thapar University\nCorrespondence: lr_be24@thapar.edu')
h('Abstract')
p('Background: A lower decision threshold may reduce missed Alzheimer’s disease (AD) cases while increasing false positives. Whether this operating point transfers between EEG cohorts is separate from whether an EEG representation improves discrimination. We examined both questions in a fixed extension of BrainTriage.')
p('Methods: Two EEG-only classifiers were trained on 54 Greek participants, comprising 25 AD cases and 29 healthy controls. Shared-channel spectral and log-covariance features were extracted from measured EEG. Models, calibration and source-derived thresholds were frozen before evaluation on 23 independent Spanish participants, comprising 12 AD cases and 11 controls. A separate nested analysis assessed threshold changes in the original 41-person AD-versus-frontotemporal dementia (FTD) development sample. Earlier holdouts were excluded throughout.')
p('Results: External AUROC was 0.864 for both representations. At threshold 0.5, covariance classification missed 0 of 12 AD cases but produced 7 of 11 false positives; spectral classification missed 2 cases and produced 1 false positive. Covariance sensitivity was 100%, with a Wilson 95% interval of 75.8–100%; specificity was 36.4% (15.2–64.6%). Lower source-derived thresholds recovered no additional external AD cases. The spectral threshold increased false positives from 1 to 3. Covariance Brier loss was 0.1772 versus 0.1300 for spectral features. In source-only AD/FTD analysis, uncertainty routing reduced mean missed cases from 3.67 to 3.33 at the cost of increasing mean false positives from 7 to 8; ridge routing remained at 3 missed cases.')
p('Conclusions: Independent evaluation supports a measurable sensitivity–specificity tradeoff, without establishing covariance superiority or a transferable 90% sensitivity guarantee. This companion AD-versus-control study does not externally validate the original AD/FTD triage model. A larger compatible cohort is needed before making clinical or comparative-superiority claims.')
p('Keywords: Alzheimer disease; EEG; external validation; decision threshold; covariance; missed diagnosis')
h('1 Introduction')
p('BrainTriage studies whether additional measurements should be acquired for selected patients. Earlier development experiments favored covariance features over a fixed EEG comparator on mean probabilistic loss, but missed AD cases did not consistently decrease. That observation motivates two separate experiments: transporting a compact EEG representation to a genuinely independent population, and assessing a training-selected sensitivity threshold in the original differential-diagnosis task. All findings remain exploratory because prior development results informed the design.')
page();h('2 Related work and cohort selection')
p('The AHEPA dataset [1] supplies measured EEG from AD, FTD and healthy participants. Smith and colleagues [2] studied functional connectivity in a separate Valladolid cohort and released the recordings through OSF [3]. LEAD [4] provides an explicit APAVA diagnosis mapping in its preprocessing code; we use that mapping, not its foundation model or reported performance. OAS covariance shrinkage [5] supplies a regularized second-order representation. These established methods motivate the feature comparison, rather than a claim of a new covariance estimator.')
p('Adaptive measurement acquisition [6] motivates the original basic/advanced triage structure. Nested validation [7] motivates choosing thresholds exclusively within training data. The experimental question is whether source-derived operating points preserve missed-case performance across cohorts, while keeping the representation comparison and acquisition policy distinct. Neither within-cohort accuracy nor an additional recording from the same person answers that question.')
p('Table 1. Separate analysis populations and endpoints. All counts refer to people.','Caption')
table(['Population','AD / comparator','Purpose'],[
['Greek companion source','25 / 29 healthy','Train two EEG-only classifiers'],
['Spanish APAVA external','12 / 11 healthy','One frozen external evaluation'],
['Greek original development','25 / 16 FTD','Nested threshold intervention']], [2.35,1.65,2.77])
p('The companion source retains the original 25 development AD participants and adds all 29 healthy controls from ds004504. The 11 AD participants from the earlier test split remain excluded; all earlier AD/FTD holdouts are also excluded from the original-task analysis. The Spanish cohort was acquired at a different institution and contains 23 participant files. Its archive SHA256, diagnosis-mapping blob and feature hashes are recorded with the code. No target measurements were used to fit normalization, PCA, calibration, classifiers or thresholds.')
p('Dataset eligibility was checked before examining performance. OpenNeuro ds006036 was excluded as independent evidence because its provider states that the participants also appear in ds004504 [8]. BrainLat [9] offers a compatible AD/bvFTD population, but anonymous downloads returned HTTP 403 and authorized access was unavailable. Figshare ADSZ was not used because its recording-to-person mapping did not support a sufficiently clear participant-level evaluation. These exclusions prevent counting new recordings or ambiguous files as new patients.')
p('APAVA diagnosis indices were taken from the explicit published LEAD preprocessing mapping [4], with 12 AD and 11 healthy participants. Original clinical records were unavailable for independent confirmation. This provenance limitation is retained; the mapping was fixed before model fitting and was not altered after seeing predictions.')
h('3 Methods')
p('Both companion cohorts use the same 16 observed electrodes: C3, C4, F3, F4, F7, F8, Fp1, Fp2, O1, O2, P3, P4, T3, T4, T5 and T6. Missing midline channels are not interpolated. The source uses its first 120 seconds, split into 24 five-second segments. APAVA uses up to its first 24 physician-selected five-second trials. Fifteen external participants contribute 24 trials; eight contribute fewer, including one with a single trial. Thus recording duration and artifact selection differ between sites.')
page();sub('Model and threshold specification')
p('Each segment is re-referenced to the shared-channel common average, resampled to 128 Hz with a polyphase filter and filtered at 0.5–30 Hz using a fourth-order zero-phase Butterworth filter. Welch spectra use two-second Hann windows with 50% overlap. Twenty spectral features are log relative powers across five regions and four bands: delta 0.5–4, theta 4–8, alpha 8–13 and beta 13–30 Hz. Features are averaged across available segments so that every participant contributes one row.')
p('For each band, OAS estimates a 16-by-16 covariance matrix. Trace normalization removes global scale; a matrix logarithm maps the positive definite matrix to symmetric coordinates. Eigenvalues are floored at 10⁻¹⁰. Off-diagonal coordinates receive a square-root-of-two weight, yielding 136 coordinates per band and 544 in total. Common-average referencing can create a singular raw covariance; shrinkage and the eigenvalue floor make the logarithm defined. This representation is a regularized feature map, not an inferred causal brain network.')
eq('C̃ = C_OAS / tr(C_OAS),     z = vec_sym(log(C̃))')
p('The spectral classifier uses median imputation, standard scaling and logistic regression with C = 1. The covariance classifier uses median imputation, scaling, five training-fitted principal components, a second scaling step and logistic regression with C = 0.3. Both use three-fold sigmoid calibration, ensemble=False, and a 3,000-iteration limit. No target adaptation, hyperparameter search, synthetic examples or clinical metadata are used in the companion models.')
p('For positive-class out-of-fold probabilities pᵢ from a training set, we select the largest feasible threshold at or below 0.5. Candidate thresholds are 0, 0.5 and observed positive-class probabilities no greater than 0.5. The exploratory 90% target is a design choice, not a clinically validated requirement.')
eq('t* = max {t ∈ T : t ≤ 0.5 and Σᵢ yᵢ 1[pᵢ ≥ t] / Σᵢ yᵢ ≥ 0.90}')
p('The constraint t* ≤ 0.5 guarantees that lowering the threshold cannot increase false negatives on the same probabilities; it can increase false positives. It leaves AUROC and Brier loss unchanged. Source evaluation uses three repeats of four outer folds, with three-fold threshold cross-fitting inside each outer training set. Final thresholds use five-fold source cross-fitting, followed by refitting on all 54 source participants. Frozen thresholds are 0.3372 for spectral and 0.2200 for covariance models; both attain 92% sensitivity on the source predictions used to choose them. That fitting sensitivity is not an independent performance estimate.')
p('The original AD/FTD analysis uses fixed basic logistic regression on age, sex and MMSE and an advanced classifier with those variables plus 760 covariance coordinates reduced to five principal components. Four policies are compared: basic, full acquisition, uncertainty routing and ridge benefit routing. The ridge gate predicts the cross-fitted reduction in Brier loss from basic inputs, the basic probability and its Bernoulli variance, with penalty 10. Threshold cross-fitting repeats the complete classifier-and-gate fitting process within outer training. Referral batches are individual validation folds with floor(0.3n) acquisitions, totaling 12 of 41 participants per repeat for either routing policy. This batching differs from the earlier pooled-repeat experiment, so comparisons are made within this study.')
page();h('4 Independent external results')
p('Table 2. One external prediction per participant. FN denotes missed AD cases; FP denotes healthy controls classified as AD. Source t denotes the frozen sensitivity threshold.','Caption')
table(['Model and threshold','FN / 12','FP / 11','Sensitivity','Specificity','Brier'],[[r['model'].capitalize()+(' 0.5' if r['operating']=='default' else ' source t'),r['false_negatives'],r['false_positives'],f"{float(r['sensitivity']):.3f}",f"{float(r['specificity']):.3f}",f"{float(r['brier']):.4f}"] for r in external],[2.1,.7,.7,.95,.95,1.07])
p('The covariance model detected all 12 AD cases at both thresholds, but seven controls were classified as AD. The spectral model detected ten AD cases and correctly classified ten controls at 0.5. Its lower threshold added two false positives without recovering either missed AD case. The primary intervention, lowering the covariance threshold, therefore made no external classification change. Zero observed misses should not be interpreted as zero future risk.')
figure('external_intervals','Figure 1. External sensitivity and specificity with Wilson 95% intervals. Circles denote threshold 0.5; squares denote source-derived thresholds. Intervals reflect 12 AD cases and 11 controls, not large-sample certainty.',6.5)
p('Both models had AUROC 0.8636. Covariance minus spectral Brier loss was +0.0472, with a paired stratified participant-bootstrap 95% interval of −0.0479 to +0.1403. The AUROC difference was numerically zero, with interval −0.2045 to +0.1818. These 2,000-draw intervals are conditional on the two fitted models and omit source-training variability. They do not establish equivalence or superiority.')
page();h('External discrimination and error counts')
figure('external_roc','Figure 2. External ROC curves from 23 participants. Squares mark the source-derived operating points. These curves describe the completed test; no point on them was used to retune a threshold.',3.8)
figure('external_confusion','Figure 3. External confusion counts for both fixed classifiers and thresholds. Each panel contains the same 12 AD participants and 11 controls. Raw counts make the sensitivity–specificity tradeoff explicit.',5.2)
page();h('5 Source development and missed cases')
p('Companion source validation showed the expected threshold tradeoff. Mean covariance misses decreased from 6.33 to 3.33 among 25 AD participants, while false positives increased from 4 to 16 among 29 controls. Spectral misses decreased from 7.33 to 2.67, while false positives increased from 2 to 14. Mean sensitivity at source-derived thresholds was 86.7% for covariance and 89.3% for spectral features, below the fitting target. These three correlated repeat means are descriptive and have no independent-repeat confidence interval.')
p('Table 3. Original AD/FTD task, mean counts over three nested outer repeats. Each repeat has 25 AD and 16 FTD participants. Parentheses show default threshold → source-derived threshold.','Caption')
rows=[]
for policy,label in [('basic','Basic'),('full','Full EEG'),('uncertainty','Uncertainty'),('ridge_gain','Ridge gain')]:
 a=next(r for r in source if r['policy']==policy and r['operating']=='default');b=next(r for r in source if r['policy']==policy and r['operating']=='sensitivity90')
 rows.append([label,f"{float(a['false_negatives_mean']):.2f} → {float(b['false_negatives_mean']):.2f}",f"{float(a['false_positives_mean']):.2f} → {float(b['false_positives_mean']):.2f}",f"{float(a['brier_mean']):.4f}"])
table(['Policy','Missed AD','False positive FTD','Brier'],rows,[1.55,1.65,2.0,1.27])
figure('source_missed_cases','Figure 4. Individual repeat counts and horizontal mean markers for the original AD/FTD development sample. Repeats reuse participants. This is source-only evidence and does not validate the original triage model in Spain.',6.5)
p('Ridge routing retained three missed AD cases in every repeat, while mean false positives rose from 6.67 to 7.00 after threshold adjustment. Uncertainty routing recovered one case in one repeat, producing the mean reduction of 0.33, but mean false positives rose by one. Full acquisition similarly recovered one case in one repeat. The basic policy did not change its classifications. These limited changes do not support a robust improvement in missed-case performance.')
p('At threshold 0.5, ridge routing had mean Brier loss 0.1675 versus 0.1713 for uncertainty routing using the same classifiers and acquisition count. That descriptive difference is distinct from threshold benefit. Source labels, earlier development reuse, the small sample and clinical inputs limit any superiority claim. In particular, MMSE may overlap with information used in clinical diagnosis.')
page();h('6 Discussion and limitations')
p('The external experiment changes the interpretation of the earlier covariance result. Covariance features achieved high observed sensitivity, but their external specificity and Brier loss were worse than the compact spectral baseline. Equal AUROC alongside different threshold behavior separates ranking from probability calibration and operating point choice. The data do not identify whether site, preprocessing, disease severity or sample composition caused these differences. A causal explanation of transport failure would require more cohorts and measured covariates.')
p('This study contributes a reproducible source-to-external experiment with harmonized observed channels, an explicit freeze before target predictions and complete reporting of both benefit and harm from threshold changes. The model components are established; no state-of-the-art claim is made. The lack of a beneficial external threshold effect is a substantive result. Optimizing another threshold on these 23 participants would convert them into development data and would require a new untouched cohort for validation.')
p('The endpoint limitation is fundamental. AD versus healthy control classification and AD versus FTD differential diagnosis have different comparator populations; neither endpoint is longitudinal disease progression. The companion model has no clinical inputs or acquisition gate. Its external result therefore cannot establish the validity of the unchanged original triage model. BrainLat remains a candidate for that separate test once authorized download access and compatible clinical measurements are available.')
p('The external sample contains only 12 AD cases. Even with no observed misses, its sensitivity interval extends down to 75.8%. One participant contributes only five seconds of selected EEG, and eight contribute fewer than 24 trials. Source recordings are contiguous and preprocessed by a different provider; target trials were selected for quality. The analysis cannot separate duration, artifact-selection and population effects. Original APAVA clinical labels were not independently checked beyond the published mapping. No demographic fairness, prevalence adjustment, prospective utility or economic benefit was established.')
h('7 Reproducibility and research integrity')
p('The protocol was committed before performance evaluation; source-trained model hashes and thresholds were pushed in commit 02d3e24 before external predictions. The external analysis was performed once. All four prespecified model/threshold results are retained. Five scientific tests passed, including channel-order and scale invariance, participant exclusion, predictor isolation and threshold monotonicity. The audit checked 106 companion and 204 original-task partition records, and 1,632 saved source prediction rows. No identical feature rows occurred across the combined 77-person companion dataset; this is an additional check, not independent proof of cohort identity.')
p('The numerical runtime emitted matrix-multiplication warnings during extraction, training and evaluation. It also reported an unrecognized iprint solver option during companion training. Warning counts are preserved. Recorded features and probabilities were finite; convergence warnings were treated as errors. Independent einsum calculations for PCA and logistic prediction reproduced the four final classifiers, including saved external predictions, within 3.33 × 10⁻¹⁶. Intermediate fits were not independently reconstructed, so the warning record remains a reproducibility limitation rather than being dismissed.')
p('Public code, aggregate metrics, plots and provenance hashes accompany this manuscript. Raw signals, participant-level predictions, identifiers and fitted bundles remain local. The APAVA OSF metadata did not specify a license; the release is analyzed with attribution and its raw files are not redistributed. This is secondary research on public recordings, without new recruitment or an asserted new ethics approval. AI assistance supported implementation, analysis and drafting; the named author remains responsible for verification and venue-specific disclosure.')
page();h('8 Conclusion')
p('The independent Spanish cohort supports a clear tradeoff: covariance classification missed fewer observed AD cases but generated more false positives than spectral classification, with equal AUROC and worse Brier loss. Source-selected lower thresholds did not improve external detection. The original AD/FTD analysis showed only small, inconsistent reductions in missed cases. The evidence strengthens reproducibility and clarifies limitations; it does not establish a superior or clinically deployable system. The next confirmatory study requires a larger independent cohort matching the original differential-diagnosis endpoint and a prospectively justified operating objective.')
h('References')
refs=[
('Miltiadous A, et al. A Dataset of Scalp EEG Recordings of Alzheimer’s Disease, Frontotemporal Dementia and Healthy Subjects from Routine EEG. Data. 2023;8(6):95.','https://doi.org/10.3390/data8060095'),
('Smith K, Abásolo D, Escudero J. Accounting for the complex hierarchical topology of EEG phase-based functional connectivity in network binarisation. PLoS ONE. 2017;12(10):e0186164.','https://doi.org/10.1371/journal.pone.0186164'),
('Smith K. Public analysis data accompanying the network binarisation study. OSF project JBYSN; AD_Data.tar.gz. Accessed 20 November 2026.','https://osf.io/jbysn/'),
('DL4mHealth. LEAD APAVA preprocessing notebook. Diagnosis mapping in data_preprocessing/APAVA/APAVA_preprocessing.ipynb, Git blob b6b9c130b9e519366c2844a8c203b80c9d5d8536. Accessed 20 November 2026.','https://github.com/DL4mHealth/LEAD/blob/main/data_preprocessing/APAVA/APAVA_preprocessing.ipynb'),
('Chen Y, Wiesel A, Eldar YC, Hero AO. Shrinkage Algorithms for MMSE Covariance Estimation. IEEE Transactions on Signal Processing. 2010.','https://arxiv.org/abs/0907.4698'),
('Hou R, Tang S, Jin W. An Adaptive Machine Learning Triage Framework for Predicting Alzheimer’s Disease Progression. ML4H Findings. 2025.','https://arxiv.org/abs/2511.06681'),
('Varma S, Simon R. Bias in error estimation when using cross-validation for model selection. BMC Bioinformatics. 2006;7:91.','https://doi.org/10.1186/1471-2105-7-91'),
('OpenNeuro ds006036 providers. README documenting participant overlap with ds004504. Accessed 20 November 2026.','https://github.com/OpenNeuroDatasets/ds006036/blob/main/README'),
('Prado P, et al. The BrainLat project, a multimodal neuroimaging dataset of neurodegeneration from underrepresented backgrounds. Scientific Data. 2023;10:889.','https://doi.org/10.1038/s41597-023-02806-8')]
for i,(ref,url) in enumerate(refs,1):
 pp=p(f'[{i}] {ref} {url}');pp.paragraph_format.space_after=Pt(6)
 for run in pp.runs:run.font.size=Pt(9)
(ROOT/'literature.json').write_text(json.dumps([{'id':i,'reference':ref,'url':url} for i,(ref,url) in enumerate(refs,1)],indent=2))
(ROOT/'manuscript').mkdir(exist_ok=True)
path=ROOT/'manuscript/external_eeg_validation.docx';doc.save(path);print(path)
