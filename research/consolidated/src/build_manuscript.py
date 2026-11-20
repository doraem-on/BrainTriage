"""Assemble one comprehensive paper from the audited study narratives and tables.
No model is refitted and no evaluation is repeated. Source narratives stay versioned.
"""
from pathlib import Path
import re,json,csv,shutil
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT.parent
sources={s:(BASE/folder/'src/build_manuscript.py').read_text() for s,folder in [('a','extension_v2'),('b','extension_v3'),('c','extension_v4')]}
folders={'a':BASE/'extension_v2','b':BASE/'extension_v3','c':BASE/'extension_v4'}
# Reuse the inspected typography and table implementation, not older title pages.
helper=sources['c'][:sources['c'].index('\ndef read(name):')]
helper=helper.replace('ROOT=Path(__file__).resolve().parents[1]','ROOT=Path(__file__).resolve().parents[1]')
exec(compile(helper,'shared_document_layout','exec'))
base_p=p;base_eq=eq;base_figure=figure
stage='c';figure_number=0;equation_number=0;table_number=0
references=[];maps={}
def canonical(url):
 return re.sub(r'arxiv.org/html/(\d+\.\d+)(v\d+)?',r'arxiv.org/abs/\1',url).rstrip('/')
for st in ['c','a','b']:
 maps[st]={}
 for ref in json.loads((folders[st]/'literature.json').read_text()):
  found=next((i for i,r in enumerate(references,1) if canonical(r['url'])==canonical(ref['url'])),None)
  if found is None:references.append(ref);found=len(references)
  maps[st][ref['id']]=found

def citations(text):
 def change(match):
  numbers=[]
  for part in match.group(1).split(','):
   ends=re.split('[–-]',part.strip())
   numbers.extend(range(int(ends[0]),int(ends[-1])+1))
  if 0 in numbers:return match.group(0)
  return '['+', '.join(str(maps[stage].get(n,n)) for n in numbers)+']'
 return re.sub(r'\[(\d+(?:[–,-]\s*\d+)*)\]',change,text)

def p(text,style=None):
 global table_number
 text=citations(text)
 if style=='Caption' and re.match(r'Table \w+\.',text):
  table_number+=1;text=re.sub(r'^Table \w+\.',f'Table {table_number}.',text)
 text=text.replace('Figures 3–8 examine','The following development analyses examine').replace('in Supplement A','in Figures 11 and 12')
 text=text.replace('Red identifies the main logistic configuration; gray identifies alternatives and ablations.','Rows identify the logistic configuration, alternatives and ablations.').replace('Gray dots denote development repeats; red bars denote their mean.','Dots denote development repeats; horizontal bars denote their mean.')
 return base_p(text,style)

def h(text):return doc.add_heading(re.sub(r'^\d+(?:[ .]\d+)*\s+','',text),1)
def sub(text):return doc.add_heading(re.sub(r'^\d+(?:[ .]\d+)*\s+','',text),2)
def eq(text):
 global equation_number
 equation_number+=1;text=re.sub(r'\s*\(\d+\)\s*$','',text).rstrip()
 return base_eq(text+'     ('+str(equation_number)+')')
def figure(name,caption,width=6.6):
 global figure_number
 figure_number+=1;caption=re.sub(r'^Figure\s+\w+\.',f'Figure {figure_number}.',caption)
 return base_figure((stage+'_'+name) if stage in ['a','b','c'] else name,caption,width)
def read(name):
 with open(folders[stage]/'results'/name) as f:return list(csv.DictReader(f))
def run(code):exec(compile(code,'assembled_study_'+stage,'exec'),globals())
# Study C figures are rebuilt from aggregates by figures_stage_c.py.
summary=[];contrasts=[]
# Shared title, abstract and scope replace the three separate update titles.
doc.core_properties.title='Measurement benefit and independent EEG validation in dementia assessment'
p(doc.core_properties.title,'Title');p('Lalit Kishore R');p('Department of Computer Science and Engineering, Thapar University\nCorrespondence: lr_be24@thapar.edu')
h('Abstract')
p('Background: Acquiring an additional measurement can improve a probability estimate without reducing missed diagnoses. A referral policy must therefore be evaluated separately from its underlying classifiers and decision threshold. We examine measurement benefit, uncertainty in referral rankings, model selection and independent EEG transport in a sequence of retrospective studies.')
p('Methods: The initial benchmark analyzed OASIS 2, OASIS 1, a measured cerebrospinal-fluid cohort and Greek EEG recordings as separate tasks. Equal-cost allocation, estimation-error bounds and a Brier value-of-information identity motivated comparisons of confidence, benefit and uncertainty-adjusted referral scores. Subsequent analyses nested classifier selection, covariance features and probability blending within development data. Finally, two EEG-only AD-versus-healthy-control classifiers were trained on 54 Greek participants, frozen and evaluated on 23 independent Spanish participants. A separate nested threshold analysis retained the original 41-person AD/FTD development sample.')
p('Results: Conditional uncertainty adjustment did not consistently improve acquisition performance. In the initial EEG holdout, adjusted and posterior-mean routing selected the same five of eighteen participants and missed two AD cases, versus one under full acquisition. Later rich-feature nonlinear routing reduced mean development Brier loss from 0.1789 for fixed uncertainty to 0.1662, but outperformed matched uncertainty in only one of three repeats. On the independent Spanish cohort, both companion classifiers had AUROC 0.864. Covariance classification missed 0 of 12 AD cases but generated 7 of 11 false positives, versus 2 misses and 1 false positive for spectral classification. Lower source-selected thresholds recovered no additional external AD cases.')
p('Conclusions: The evidence separates improvements in representation from benefits of acquisition and threshold adjustment. No policy consistently dominated matched alternatives, and zero external misses came with poor specificity and substantial sampling uncertainty. The independent AD-versus-control result applies to the EEG-only companion models; the original AD/FTD triage model still lacks compatible external validation.')
p('Keywords: dementia; measurement acquisition; EEG covariance; Brier score; nested validation; external validation')
h('Introduction')
p('The practical question is whether an additional measurement helps a particular assessment enough to justify acquiring it. This requires more than a strong full-information classifier. A referral score must estimate the value of information available only after acquisition, and its ranking can be unstable when training samples are small. We study that problem using recorded within-person measurements, then examine whether the EEG representation and a sensitivity-oriented operating point transfer to a new cohort.')
page();h('Study structure and acquisition system');stage='front'
base_p('Three linked studies address different questions. Study A tests measurement-benefit rules, Study B evaluates richer representations and nested model selection, and Study C tests sensitivity thresholds and independent EEG transport. Their participants, comparators and validation designs are retained separately. Combining them into one account does not turn reused development samples into new independent evidence.')
figure('study_map','Figure 0. Study sequence and evidence boundaries. The Spanish cohort supplies independent AD-versus-control evidence only. The original clinical holdouts had already been examined before Study A.',6.6)
figure('acquisition_flow','Figure 0. Training and evaluation information flow for the original acquisition system. Realized gains need outcomes and advanced measurements during training; referral at evaluation uses only information available before acquisition.',6.6)
base_p('A single participant may contribute to several development analyses, but contributes only one outcome within each analysis. No pooled sample size, meta-analysis or version-to-version significance test is reported. All figures are regenerated from saved aggregate results; no experiment was rerun to prepare this combined manuscript.')
# Study A: preserve the complete earlier methods and results, including screenshot curves.
stage='a';summary=read('holdout_summary.csv');contrasts=read('paired_contrasts.csv')
COHORTS={'oasis2':'OASIS 2','oasis1':'OASIS 1','csf':'CSF','eeg_ad_ftd':'EEG AD vs FTD'}
def result(c,policy):return next(r for r in summary if r['cohort']==c and r['config']=='logistic' and r['policy']==policy)
def value(c,policy,k='brier',digits=4):return f"{float(result(c,policy)[k]):.{digits}f}"
def contrast(c):return next(r for r in contrasts if r['cohort']==c and r['config']=='logistic' and r['contrast']=='bayes_lcb_1 minus bayes_mean')
a=sources['a'][sources['a'].index("page();h('2 Related"):sources['a'].index("page();h('11 Discussion')")]
a=a.replace("h('2 Related work and research question')","h('Study A Measurement benefit and referral uncertainty');sub('Related work and research question')")
run(a)
# Preserve the two supplementary diagnostic plots alongside Study A.
a=sources['a'][sources['a'].index("page();h('Supplement A"):sources['a'].index("out=ROOT/'manuscript'")]
a=a.replace('Supplement A Missed positives and calibration','Study A Missed positives and calibration');run(a)
# Study B: model selection, exact blend derivation, comparative results and ablations.
stage='b';brows=read('primary_table.csv')
def val(c,m,k='brier'):return float(next(r for r in brows if r['cohort']==c and r['method']==m)[k])
page();h('Study B Nested model selection and richer EEG features')
p('This study uses only the earlier development participants: OASIS 2 n=120, OASIS 1 n=158, CSF n=142 and EEG AD/FTD n=41. Earlier holdouts are excluded. Prior findings informed the finite candidate matrix, making this an exploratory development study. Its objective is to determine whether a richer advanced representation helps and whether a learned referral ranking adds value when comparators share classifiers.')
p('Connectivity-based classification [2] and compact spectral and complexity descriptors [3] motivate complementary EEG representations. Participant-level benchmarking and the AHEPA review [4, 5] inform the validation design; all segments from a participant stay together. These studies use different pipelines or endpoints, so their reported accuracies are not direct baselines. Cross-validated model combination is established methodology [7]. Our restricted two-predictor blend does not reproduce the general Super Learner procedure or inherit its guarantees automatically.')
b=sources['b'][sources['b'].index("h('3 Model and representation design')"):sources['b'].index("page();h('5 Discussion')")]
b=b.replace("page();h('3.1 Covariance features and probability blending')","h('Covariance features')").replace("p('Let p_b and p_a", "page();h('Probability blending');p('Let p_b and p_a")
run(b)
page();h('Study B Blending and interpretation')
figure('blend_weights','Figure 0. Training-fitted blend coefficients from twelve outer fits per configuration. Jitter separates points. These correlated coefficients describe the fitting procedure and do not form a posterior distribution.',6.4)
p('The rich EEG feature set provided the clearest mean predictive improvement, while the learned routing rule was less consistent. Covariance/PCA candidates were chosen in all twelve rich outer fits, with C=0.3 in eight and C=3 in four. This frequency does not establish that covariance features will dominate at another site. Rich blended ridge routing scored 0.1656 on mean Brier loss, slightly below the nonlinear gate at 0.1662. The independent transport experiment in Study C tests a simplified representation without claiming to validate this complete clinical-input triage pipeline.')
p('All three clinical cohorts failed to improve consistently over the fixed uncertainty comparator. The results caution against attributing favorable EEG means to model complexity in general. Study B ranks combined outer validation predictions within a repeat; the source sensitivity analysis in Study C uses separate validation-fold batches. The numerical difference between those studies cannot be interpreted as a controlled improvement caused by a software version change.')
# Study C: full new methods, results, figures, uncertainty and integrity record.
stage='c';external=read('external_metrics.csv');source=read('sensitivity_summary.csv')
c=sources['c'][sources['c'].index("page();h('2 Related work"):sources['c'].index("page();h('8 Conclusion')")]
c=c.replace("h('2 Related work and cohort selection')","h('Study C Sensitivity thresholds and independent EEG transport');sub('Related work and cohort selection')")
run(c)
page();h('Integrated discussion')
p('Across the three studies, predictive accuracy, referral stability and missed-case performance did not move together. Study A showed that subtracting conditional posterior uncertainty could stabilize one EEG referral ranking without changing its holdout allocation. Study B improved mean EEG probability loss relative to a fixed baseline, but the matched routing comparison remained unstable. Study C found equal external AUROC for spectral and covariance models while their false-positive counts differed sharply. The corresponding figures show why one headline metric cannot summarize the system.')
p('The mathematical results describe what optimal allocation would require if conditional gains were known. They do not establish that the fitted gates estimate those gains accurately. The posterior penalty omits upstream classifier uncertainty; the blending guarantee applies to the training pairs used to fit its coefficient. Both distinctions remain relevant after adding external data. Neither a theoretical identity nor an internally favorable average removes the need for a compatible external test of the complete acquisition system.')
p('Several restrictions apply to the evidence as a whole. OASIS releases may overlap and were never pooled. The clinical holdouts were exposed before the extended benchmark. Recorded outcomes may incorporate cognitive or biomarker information related to the inputs. The CSF mirror could not be matched directly to original repository bytes. The Greek AD/FTD and Spanish AD/control endpoints are different, and APAVA clinical labels were obtained from an explicit published preprocessing mapping rather than independently reviewed clinical records. Repeated development analyses also create dataset-level adaptation beyond what within-run nesting can remove.')
p('Hypothetical acquisition costs, controlled missingness and Gaussian perturbations help explain algorithm behavior but are not observed clinical economics or external cohorts. The original EEG holdout and the Spanish cohort are small; conditional intervals omit model-refitting variability. No prospective safety, clinical deployment, fairness, causal biomarker contribution or state-of-the-art superiority is established. These limits accompany the favorable and unfavorable results throughout the paper.')
h('Conclusion')
p('Measurement-benefit estimation provides a clear framework for allocating additional measurements, but the fitted rules did not consistently improve on simpler matched policies. Rich covariance features improved some source-development averages, while external testing exposed a substantial sensitivity–specificity tradeoff. The next confirmatory study must match the original AD/FTD endpoint, retain paired clinical and EEG measurements, and fix a clinically justified acquisition and missed-case objective before evaluation. Until then, the supported contribution is a reproducible comparison of allocation, representation and threshold behavior using measured data.')
h('Data availability and acknowledgments')
p('We acknowledge the OASIS, clinical lipidomics, AHEPA EEG and Valladolid/APAVA contributors. Source-specific terms apply: OASIS conditions, the CSF repository’s CC BY-NC-ND 4.0 notice, and the OpenNeuro metadata’s CC0 declaration are retained in the versioned records. APAVA metadata did not specify a license; its raw signals are not redistributed. Public code, aggregate outputs and manuscripts are available in the BrainTriage research branch. Raw participant rows, private partitions and fitted bundles remain local. This secondary analysis involved no new recruitment; no new ethics approval, funding declaration or institutional endorsement is asserted.')
p('AI assistance supported literature synthesis, implementation, analysis, figures and drafting. The named author remains responsible for verification, authorship declarations and the disclosure required by the selected venue.')
# Unified reference list; original study citations are remapped by source URL.
page();h('References')
for i,ref in enumerate(references,1):
 if i==15:page();h('References continued')
 pp=base_p(f"[{i}] {ref['reference']} {ref['url']}");pp.paragraph_format.space_after=Pt(6)
 for run_ in pp.runs:run_.font.size=Pt(9)
# Detailed new appendices retain exact metric and implementation records.
stage='c'
start=sources['c'].index("page();h('Appendix A")
end=sources['c'].index("(ROOT/'manuscript').mkdir",start)
run(sources['c'][start:end])
# A study-aware glossary disambiguates reused symbols without changing equations.
notation=json.loads((ROOT/'notation.json').read_text())
for group in notation:
 page();h(group['heading']);base_p(group['introduction'])
 if group.get('subheading'):sub(group['subheading'])
 table(['Symbol or abbreviation','Meaning and scope'],group['rows'],[1.55,5.15])
# Ensure every explicit Word color is black and shading is white.
for tree in [doc.element,doc.styles.element,section.footer._element]:
 for element in tree.iter():
  if element.tag==qn('w:color'):element.attrib.clear();element.set(qn('w:val'),'000000')
  if element.tag==qn('w:shd'):element.attrib.clear();element.set(qn('w:val'),'clear');element.set(qn('w:fill'),'FFFFFF')
  for key in list(element.attrib):
   if key.rsplit('}',1)[-1] in ['themeColor','themeTint','themeShade','themeFill','themeFillTint','themeFillShade']:del element.attrib[key]
  if qn('w:color') in element.attrib:element.set(qn('w:color'),'000000')
path=ROOT/'manuscript/braintriage_complete_research_paper.docx';doc.save(path)
(ROOT/'literature.json').write_text(json.dumps([dict(r,id=i) for i,r in enumerate(references,1)],indent=2))
(ROOT/'content_manifest.json').write_text(json.dumps({'figures':figure_number,'equations':equation_number,'tables':len(doc.tables),'references':len(references),'notation_entries':sum(len(group['rows']) for group in notation),'new_model_fits':0,'new_external_evaluations':0,'source_studies':['extension_v2','extension_v3','extension_v4']},indent=2))
print(path);print('Figures',figure_number,'equations',equation_number,'tables',len(doc.tables),'references',len(references))
