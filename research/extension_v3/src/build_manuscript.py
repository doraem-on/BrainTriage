"""Build the research update from recorded aggregate results."""
from pathlib import Path
import csv,json
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH
ROOT=Path(__file__).resolve().parents[1]
with open(ROOT/'results/primary_table.csv') as f: results=list(csv.DictReader(f))
def val(c,m,k='brier'):
    return float(next(r for r in results if r['cohort']==c and r['method']==m)[k])
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

doc.core_properties.title='Nested selection and covariance features for budgeted dementia assessment'
p('Nested selection and covariance features for budgeted dementia assessment','Title')
p('Lalit Kishore R')
p('Department of Computer Science and Engineering, Thapar University\nCorrespondence: lr_be24@thapar.edu')
h('Abstract')
p('Background: Improving prediction after an additional measurement does not necessarily improve the decision to acquire it. We examined regularization, richer EEG representations and training-fitted probability blending in a fixed extension of a dementia triage study.')
p('Methods: Original development participants from OASIS 2 (120), OASIS 1 (158), a CSF cohort (142) and an EEG AD-versus-FTD cohort (41) underwent three repeats of four-fold patient-level outer validation. Model selection was nested inside both outer training and gate-target cross-fitting. EEG candidates added spectral ratios, Hjorth summaries and band-specific log-covariance features with training-only principal components. A constrained scalar blend minimized cross-fitted Brier loss. The primary comparison ranked predicted Brier benefit versus basic-model uncertainty using identical classifiers and nominal 30% acquisition capacity. Earlier holdouts were excluded.')
p('Results: The fixed matrix completed 108 outer pipeline fits and nine final development-fitted bundles. For EEG, the rich blended nonlinear-benefit policy had mean Brier score 0.1662, versus 0.1789 for fixed uncertainty routing and 0.1742 for matched tuned uncertainty routing. The matched difference was −0.0080, with repeat differences from −0.0248 to +0.0007; only one of three repeats favored the benefit policy. The same rich classifiers with a ridge benefit gate scored 0.1656. No consistent gain occurred in the clinical cohorts. Covariance candidates were selected in all twelve rich EEG outer fits.')
p('Conclusions: Covariance features produced an exploratory improvement over the fixed EEG baseline, but the nonlinear referral rule did not consistently outperform matched or simpler alternatives. These findings support a focused external test of the representation, not a claim of general or clinical superiority. The previously studied development samples and small EEG cohort limit inference.')
p('Keywords: dementia; EEG covariance; active feature acquisition; nested validation; probability blending; Brier score')
h('1 Introduction and scope')
p('A resource-constrained assessment system needs both an informative advanced model and a useful acquisition rule. A model can be accurate when every patient receives an EEG or biomarker panel while providing little guidance about which patients need that measurement. Conversely, a referral rule can appear successful because its classifiers improved, even when the ranking itself did not. We therefore separate representation, probability estimation and referral selection in capacity-matched comparisons.')
p('This extension follows an earlier BrainTriage study whose uncertainty-adjusted benefit gate did not reliably improve held-out performance. That result motivates the present finite experiment, but it also makes the analysis exploratory. All earlier test participants are excluded here. The contribution is a reproducible assessment of when richer measurements help and whether a learned ranking adds value beyond uncertainty; the component algorithms are established methods.')
page();h('2 Related work and measured datasets')
p('Hou, Tang and Jin [1] study adaptive basic/advanced prediction and gating for ADNI progression. Their endpoint differs from our concurrent impairment and differential-diagnosis tasks, so their scores are not direct benchmarks. Connectivity-based dementia classification [2] motivates covariance features. Spectral and complexity research [3,4] motivates compact EEG summaries, while the AHEPA review [5] emphasizes patient-level evaluation. We adapt these ideas rather than reproduce their complete pipelines. Nested selection follows the bias-control principle of Varma and Simon [6]; restricted convex blending belongs to established ensemble methodology [7].')
p('The unresolved question examined here is whether improved advanced features translate into better acquisition at a fixed capacity when the routing baselines share the same classifiers. This is a specific experimental gap, not a claim that no previous work has studied acquisition or covariance features.')
p('Table 1. Original development samples only. Cohorts are analyzed separately; no cross-cohort fusion or independent external-validation claim is made.','Caption')
table(['Dataset','n / positive','Basic measurements','Added measurements / outcome'],[
['OASIS 2','120 / 52','Age, sex, education, SES, MMSE','eTIV, nWBV / CDR > 0'],
['OASIS 1','158 / 80','Age, sex, SES, MMSE','eTIV, nWBV / CDR > 0'],
['CSF','142 / 73','Age, sex, MMSE','Amyloid, total tau, phosphorylated tau / AD vs MCI'],
['EEG','41 / 25','Age, sex, MMSE','Measured EEG / AD vs FTD']], [1.0,.8,1.95,3.02])
p('OASIS uses one observation per participant: the earliest visit in OASIS 2 and adults aged at least 60 in OASIS 1 [8,9]. CDR > 0 denotes concurrent cognitive impairment, not confirmed Alzheimer pathology or future progression. The releases may overlap and are not pooled [13]. The complete-panel CSF analysis uses measured within-person biomarkers [10,11]. Its downloaded source table contains 212 records versus 213 in the publication; retained bytes were verified against a public mirror rather than directly against the original repository. Selection for complete biomarkers may bias the cohort.')
p('EEG source recordings come from OpenNeuro ds004504 [12]. The earlier 59-person AD/FTD subset had 36 AD and 23 FTD cases; only its 41 development participants enter this extension. We use the same first 120 seconds of provider-denoised, 19-channel, 500-Hz signals. Source URLs and exact window hashes are retained. Dataset metadata identify version 1.0.9, while retrieved S3 objects were pinned by byte hashes rather than assumed immutable. No new restricted ADNI data were obtained.')
h('3 Model and representation design')
p('Every classifier uses training-only median imputation and scaling, with sigmoid calibration in three stratified folds (ensemble=False). Basic selection compares logistic regression C ∈ {0.03, 0.3, 1, 3}; original advanced selection adds RBF SVC C ∈ {0.3, 3}, with gamma=scale. The fixed baseline uses calibrated logistic C=1. Candidate selection minimizes three-fold out-of-fold Brier loss, with the fixed candidate order breaking ties. It is repeated inside each gate-training fold.')
p('Rich EEG selection compares nine candidates: the original spectral logistic C=1; four logistic and two RBF models on 45 spectral/complexity features; and two logistic models on covariance principal components (C=0.3 or 3). Basic clinical inputs remain in every advanced model. These are alternative representations, not a single 805-feature classifier.')
page();h('3.1 Covariance features and probability blending')
p('The spectral representation contains twenty regional log-relative powers and twenty-five regional summaries: theta/alpha and slow/fast log ratios, normalized spectral entropy, and Hjorth mobility and complexity. For each of four bands (0.5–4, 4–8, 8–13 and 13–30 Hz), a fourth-order zero-phase Butterworth filter precedes Oracle Approximating Shrinkage covariance estimation. Trace normalization removes overall scale; a matrix logarithm and upper-triangle vectorization yield 190 features per band. Off-diagonal elements receive a square-root-of-two weight, preserving the Frobenius inner product for symmetric matrices. The 760 covariance features are standardized and reduced to five principal components fitted only on training participants. This describes second-order signal coupling, not causal connectivity.')
p('Let p_b and p_a be paired basic and advanced probabilities generated by nested cross-fitting on an outer training set. Define d_i = p_a,i − p_b,i and q_i(α) = p_b,i + αd_i. The empirical blend objective is:')
eq('L(α) = n⁻¹ Σᵢ (yᵢ − p_b,i)² − 2α n⁻¹ Σᵢ (yᵢ − p_b,i)dᵢ + α² n⁻¹ Σᵢ dᵢ².')
eq('α* = clip[ Σᵢ (yᵢ − p_b,i)dᵢ / Σᵢ dᵢ², 0, 1 ].')
p('For a positive denominator this follows by differentiation of a convex quadratic and projection onto [0,1]. A denominator at most 10⁻¹² sets α=0. In the nondegenerate case, both endpoints are feasible, so fitted loss on these particular cross-fitted pairs cannot exceed either endpoint. This is an empirical optimization property, not a guarantee for refitted models or new patients. The blend coefficient uses all cross-fitted training pairs; it is not itself cross-fitted per training observation. Outer validation evaluates the resulting complete procedure.')
h('3.2 Referral, validation and reporting')
p('Gain targets are g_i = (y_i − p_b,i)² − (y_i − q_i)². A ridge regressor (penalty 10) and an Extra Trees regressor (80 trees, depth 3, minimum leaf size 6) predict gain from basic variables, p_b and p_b(1−p_b). The gates never receive validation labels or advanced measurements. A ridge confidence-gain comparator targets |q_i−0.5|−|p_b,i−0.5|. All gate hyperparameters are fixed.')
p('Within each repeat, outer validation predictions are combined and ranked as one evaluation batch. Each partial-acquisition rule selects floor(budget × n) participants; nominal 30% means 36/120, 47/158, 42/142 and 12/41 acquisitions. Uncertainty ranks proximity of p_b to 0.5. Random results average thirty fixed draws; the outcome-informed oracle is retrospective only. Basic-only and full-acquisition endpoints use zero and all panels. Eight policies and seven capacities are retained for every variant.')
p('Three repeats of four outer folds contain selection, calibration, cross-fitted gain targets and blending; the overall seed is 20261122. The primary contrast is blended nonlinear gain minus matched uncertainty at nominal 30%, using rich EEG selection and original-feature selection elsewhere. Fixed-baseline and representation/blend comparisons are secondary. Means and repeat ranges are descriptive: the repeats share people and training data. No independent-repeat confidence interval, p-value or prospective-superiority claim is made. The protocol was committed before v3 performance evaluation, after earlier findings informed its design.')
page();h('4 Results')
p('Table 2. Mean Brier scores across three correlated outer repeats; lower is better. Tuned policies share the same classifiers. Basic and full endpoints are not subject to 30% capacity.','Caption')
cohorts={'oasis2':'OASIS 2','oasis1':'OASIS 1','csf':'CSF','eeg_ad_ftd':'EEG'}
methods=['Fixed uncertainty','Tuned basic','Tuned full','Tuned uncertainty','Tuned nonlinear gain']
table(['Cohort','Fixed\nuncertainty','Tuned\nbasic','Tuned\nfull','Tuned\nuncertainty','Tuned\nnonlinear'],[[label]+[f'{val(c,m):.4f}' for m in methods] for c,label in cohorts.items()],[.85,1.18,1.05,1.05,1.25,1.39])
p('The EEG nonlinear-benefit policy reduced mean Brier loss by 0.0128 (7.1%) relative to fixed uncertainty routing and by 0.0080 (4.6%) relative to matched tuned uncertainty. It beat the fixed baseline in all three repeats, but beat the matched comparator in only one. Matched repeat differences were +0.00070, +0.00003 and −0.02476: the mean advantage was driven by the third repeat. Rich blended ridge routing scored 0.1656, slightly below nonlinear routing at 0.1662; full acquisition scored 0.1648 while using all panels.')
p('EEG mean AUROC was 0.8192 for rich blended nonlinear routing versus 0.7875 for fixed uncertainty and 0.7967 for matched uncertainty. At threshold 0.5, mean false negatives were 3.33, 2.33 and 3.33, respectively, among 25 positive participants per repeat. Better mean Brier and AUROC therefore did not imply fewer missed AD cases than the fixed baseline.')
figure('primary_comparison','Figure 1. Each point is one outer repeat; diamonds mark means and line segments span observed ranges. These ranges are not confidence intervals. The panels have different horizontal scales.',6.2)
p('The clinical cohorts did not show a consistent gain. Nonlinear minus matched uncertainty mean Brier differences were −0.0010 in OASIS 2, +0.0016 in OASIS 1 and +0.0024 in CSF. Against fixed uncertainty, the differences were +0.0045, +0.0033 and +0.0071. Thus the revised pipeline did not improve the strongest fixed comparator in these cohorts.')
page();h('4.1 Capacity and representation analysis')
figure('capacity_curves','Figure 2. Mean Brier score across three correlated repeats against nominal acquisition capacity. Nonlinear, ridge, uncertainty, random and oracle curves share tuned blended classifiers; fixed uncertainty uses the original fixed classifiers. The oracle requires outcomes and is unavailable for deployment. Capacity was not selected from these curves.',6.3)
figure('eeg_ablation','Figure 3. EEG representation and blending ablations. Dots are repeat estimates; diamonds are means. Covariance/PCA candidates were selected in all twelve rich outer fits (C=0.3 in eight; C=3 in four). Selection frequency alone does not establish stable principal components or biological validity.',6.3)
p('Under full acquisition, original-feature tuning scored 0.2510 without blending and 0.1757 with blending; rich tuning scored 0.1655 and 0.1648, respectively. The rich representation supplied the clearest predictive change. At 30% nonlinear acquisition, rich raw and blended scores were 0.1659 and 0.1662: adding blending did not improve this policy. These ablations argue against attributing all observed improvement to the scalar blend or nonlinear gate.')
page();h('5 Discussion')
p('The results suggest a focused direction for further research: test the covariance representation with a simpler, well-controlled acquisition rule on a new cohort. The rich EEG model improved over fixed uncertainty routing in every repeat, whereas the nonlinear gate did not consistently improve matched routing and did not beat the ridge gate on mean Brier score. This distinction matters because it identifies the component most worth validating without promoting a selected favorable configuration as an established winner.')
p('More model selection is not automatically better. In the clinical cohorts, additional tuning and blending failed to consistently surpass the fixed logistic uncertainty comparator. The small EEG sample supports only limited training sets inside nested folds; even shrinkage covariance and five principal components can be unstable. Performance also depends on MMSE, which may be closely related to clinical diagnostic assignment. The earlier study included a no-MMSE analysis; the present fixed matrix does not establish that rich EEG performance persists without cognitive inputs.')
figure('blend_weights','Figure 4. Training-fitted blend coefficients from twelve outer fits per configuration. Jitter separates points. Values near zero suppress advanced prediction; near one retain it. These correlated estimates describe fitting variability and are not posterior samples.',6.2)
p('The current evidence has additional limits. All development participants had been studied previously, and earlier results influenced the extension. Nested resampling controls selection within this matrix but does not erase that dataset-level adaptation. OASIS outcomes, CSF AD/MCI labels and EEG AD/FTD labels are different tasks. Complete-panel selection, site effects, diagnostic incorporation, uncertain source-table correspondence and short signal windows limit generalization. No economic value or clinical safety threshold was validated. No confidence interval or significance claim is attached to the three repeat means.')
h('5.1 Confirmatory study required')
p('A subsequent study should obtain a genuinely independent cohort with the same diagnostic endpoint and paired cognitive/EEG measurements, then lock preprocessing, classifier, gate, capacity and decision threshold before inspecting its outcomes. The primary endpoint should separate probabilistic accuracy from a prespecified missed-case constraint; adequate sample size should be determined for that paired comparison. External site testing and a prespecified no-MMSE ablation would address transportability and diagnostic incorporation. ADNI progression would require its own endpoint, access approval and protocol rather than being appended as a numerically comparable test.')
page();h('6 Reproducibility and conclusion')
p('The fixed run generated 2,352 aggregate metric rows, 108 outer pipeline fits and nine final development-fitted bundles. Five scientific tests cover blend optimization, covariance geometry, participant exclusion, nested gate separation, predictor invariance and exact capacity. All 48 outer partitions and 42 participant-prediction files were checked for development-only membership and finite predictions. Independent scalar/einsum calculations reproduced all eighteen final calibrated classifiers to a maximum absolute probability difference of 2.11 × 10⁻¹⁵. This verifies final classifier arithmetic, not every intermediate numerical operation.')
p('The numerical runtime emitted 1,963 warnings each for divide-by-zero, overflow and invalid matrix multiplication. Warning counts are retained rather than hidden; all recorded predictions were finite and final arithmetic checks passed. Convergence warnings were configured as errors and none terminated the run. Feature and training-code hashes matched the recorded manifests. Raw records, participant predictions and fitted bundles containing training identifiers remain local; code, aggregate results, source provenance and figures accompany the manuscript.')
p('Data use follows source-specific terms: OpenNeuro metadata identify CC0, the CSF repository identifies CC BY-NC-ND 4.0, and OASIS terms apply separately. No new recruitment, intervention or new ethics approval is asserted. AI assistance supported implementation, analysis and drafting; the author is responsible for verification and venue-specific disclosure.')
p('Covariance features yielded an exploratory EEG improvement over a fixed comparator, while acquisition-policy gains remained unstable and clinical-cohort gains were absent. The supported next step is independent validation of the representation and simpler routing baselines. The present results do not establish state-of-the-art performance or a clinically deployable triage system.')
h('References')
refs=json.loads((ROOT/'literature.json').read_text())
old=json.loads((ROOT.parent/'extension_v2/literature.json').read_text())
refs += [{**r,'id':13 if r['id']==17 else r['id']} for r in old if r['id'] in [8,9,10,11,12,17]]
for ref in refs:
    pp=p(f"[{ref['id']}] {ref['reference']} {ref['url']}")
    pp.paragraph_format.space_after=Pt(4)
    for run in pp.runs:run.font.size=Pt(8.5)
(ROOT/'manuscript').mkdir(exist_ok=True)
path=ROOT/'manuscript/nested_model_research_update.docx';doc.save(path);print(path)
