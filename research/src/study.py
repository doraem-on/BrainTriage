"""Reproducible, patient-level retrospective feature-acquisition benchmark.

This is research software, not a diagnostic or referral service.
All model fitting, calibration and gate targets are confined to training data.
"""
from pathlib import Path
import argparse, hashlib, json, os, platform, time, warnings
import joblib
import numpy as np
import pandas as pd
import sklearn
warnings.filterwarnings('ignore', message='Unknown solver options: iprint')
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.metrics import (roc_auc_score, average_precision_score, brier_score_loss,
    log_loss, balanced_accuracy_score, f1_score, confusion_matrix)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get('BRAINTRIAGE_SOURCE', str(ROOT/'data_raw')))
PLAN = json.loads((ROOT/'protocol.json').read_text())
SEED = PLAN['seed']
BUDGETS = PLAN['budgets']

def load_cohort(name):
    if name == 'oasis2':
        path = SOURCE/'data/oasis_longitudinal.csv'
        raw = pd.read_csv(path)
        d = raw.sort_values(['Subject ID','Visit','MR Delay']).drop_duplicates('Subject ID').copy()
        d = d.rename(columns={'Subject ID':'id', 'Age':'age', 'MMSE':'mmse', 'EDUC':'education', 'SES':'ses'})
        basic = ['age','male','education','ses','mmse']
        extra = ['eTIV','nWBV']
        d['male'] = (d['M/F'] == 'M').astype(int)
        d = d.dropna(subset=['CDR']+extra)
        d['y'] = (d['CDR'] > 0).astype(int)
    elif name == 'oasis1':
        path = SOURCE/'data/oasis_cross-sectional.csv'
        raw = pd.read_csv(path)
        d = raw.copy()
        d['id'] = d.ID.str.replace(r'_MR\d+$','',regex=True)
        d = d.sort_values('ID').drop_duplicates('id')
        d = d.rename(columns={'Age':'age','MMSE':'mmse','SES':'ses'})
        # Educ is an ordinal category, not years; omit it from this benchmark.
        basic = ['age','male','ses','mmse']
        extra = ['eTIV','nWBV']
        d['male'] = (d['M/F'] == 'M').astype(int)
        d = d[(d.age >= 60) & d.CDR.notna()].dropna(subset=extra).copy()
        d['y'] = (d['CDR'] > 0).astype(int)
    elif name == 'csf':
        path = SOURCE/'data_external/csf_biomarkers.csv'
        raw = pd.read_csv(path)
        d = raw[raw.Diagnostic.isin(["Mild Cognitive Impairment", "Alzheimer's Disease"])].copy()
        d = d.rename(columns={'Sample':'id','Age':'age','MMSE':'mmse',
            'CSF Amyloid (pg/mL)':'amyloid','CSF Total tau (pg/mL)':'ttau',
            'CSF Phosphorylated tau (pg/mL)':'ptau'})
        basic = ['age','male','mmse']
        extra = ['amyloid','ttau','ptau']
        d['male'] = (d.Sex == 'Male').astype(int)
        d = d.dropna(subset=extra)
        d['y'] = (d.Diagnostic == "Alzheimer's Disease").astype(int)
    else:
        raise ValueError(name)
    d['id'] = d.id.astype(str)
    assert d.id.is_unique, 'Repeated participant in baseline cohort'
    d = d.sort_values('id').reset_index(drop=True)
    audit = {'cohort':name,'raw_rows':len(raw),'analysis_n':len(d),'positive_n':int(d.y.sum()),
        'negative_n':int((1-d.y).sum()),'basic_features':basic,'advanced_features':extra,
        'missing_basic':d[basic].isna().sum().to_dict(),'source_path':str(path),
        'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'age_min':float(d.age.min()),'age_max':float(d.age.max()),'male_n':int(d.male.sum())}
    return d, basic, extra, audit

def split_cohort(d):
    train, test = train_test_split(np.arange(len(d)),test_size=PLAN['locked_test_fraction'],
        random_state=SEED,stratify=d.y)
    assert set(d.iloc[train].id).isdisjoint(d.iloc[test].id)
    return np.sort(train), np.sort(test)

def make_model(family, seed):
    if family == 'logistic':
        estimator = LogisticRegression(C=1.0,max_iter=2000,random_state=seed)
    elif family == 'random_forest':
        estimator = RandomForestClassifier(n_estimators=150,max_depth=4,min_samples_leaf=5,
            max_features='sqrt',n_jobs=1,random_state=seed)
    elif family == 'hist_gradient':
        estimator = HistGradientBoostingClassifier(max_iter=100,max_leaf_nodes=7,
            min_samples_leaf=10,l2_regularization=1,learning_rate=0.05,random_state=seed)
    else:
        raise ValueError(family)
    pipe = make_pipeline(SimpleImputer(strategy='median',add_indicator=True),StandardScaler(),estimator)
    return CalibratedClassifierCV(pipe,method='sigmoid',
        cv=StratifiedKFold(PLAN['calibration_folds'],shuffle=True,random_state=seed),ensemble=False)

def gate_pipeline(regression=False):
    est = Ridge(alpha=10) if regression else LogisticRegression(C=1,max_iter=2000,random_state=SEED)
    return make_pipeline(SimpleImputer(strategy='median',add_indicator=True),StandardScaler(),est)

def fit_bundle(d, basic, extra, family, seed):
    y = d.y.to_numpy()
    oof_b, oof_a = np.zeros(len(d)), np.zeros(len(d))
    folds = StratifiedKFold(PLAN['gate_crossfit_folds'],shuffle=True,random_state=seed)
    for tr, va in folds.split(d,y):
        assert set(d.iloc[tr].id).isdisjoint(d.iloc[va].id)
        for cols, dest in [(basic,oof_b),(basic+extra,oof_a)]:
            m = make_model(family,seed).fit(d.iloc[tr][cols],y[tr])
            dest[va] = m.predict_proba(d.iloc[va][cols])[:,1]
    certainty_gain = (np.abs(oof_a-.5)-np.abs(oof_b-.5) > .2).astype(int)
    brier_gain = (y-oof_b)**2-(y-oof_a)**2
    gate_c = gate_pipeline().fit(d[basic],certainty_gain) if len(np.unique(certainty_gain))==2 else float(certainty_gain[0])
    gate_g = gate_pipeline(True).fit(d[basic],brier_gain)
    gate_cc = gate_pipeline(True).fit(d[basic],np.abs(oof_a-.5)-np.abs(oof_b-.5))
    mb = make_model(family,seed).fit(d[basic],y)
    ma = make_model(family,seed).fit(d[basic+extra],y)
    return {'basic_model':mb,'advanced_model':ma,'certainty_gate':gate_c,'brier_gate':gate_g,'continuous_certainty_gate':gate_cc,
        'basic_features':basic,'advanced_features':extra,'family':family,
        'training_ids':d.id.tolist(),'certainty_target_positive_n':int(certainty_gain.sum()),
        'oof_basic':oof_b,'oof_advanced':oof_a,'oof_y':y}

def predict_bundle(bundle,d):
    assert set(bundle['training_ids']).isdisjoint(d.id), 'Evaluation participant was used for fitting'
    basic,extra = bundle['basic_features'],bundle['advanced_features']
    out=d[['id','y','age','male']].copy()
    out['basic']=bundle['basic_model'].predict_proba(d[basic])[:,1]
    out['advanced']=bundle['advanced_model'].predict_proba(d[basic+extra])[:,1]
    gate=bundle['certainty_gate']
    out['certainty_gain']=gate if isinstance(gate,float) else gate.predict_proba(d[basic])[:,1]
    out['brier_gain']=bundle['brier_gate'].predict(d[basic])
    out['certainty_continuous']=bundle['continuous_certainty_gate'].predict(d[basic])
    out['risk']=out.basic
    out['uncertainty']=-np.abs(out.basic-.5)
    return out

def refer_mask(scores,budget):
    n=len(scores); k=int(np.floor(n*budget+1e-10))
    # Input sorted by ID; stable ties resolved by ID, never by target.
    mask=np.zeros(n,dtype=bool)
    mask[np.argsort(-np.asarray(scores),kind='stable')[:k]]=True
    return mask

def metrics(y,p,ref=None):
    y=np.asarray(y); p=np.asarray(p); pred=(p>=.5).astype(int)
    tn,fp,fn,tp=confusion_matrix(y,pred,labels=[0,1]).ravel()
    return {'n':len(y),'auroc':float(roc_auc_score(y,p)) if len(np.unique(y))==2 else np.nan,
        'average_precision':float(average_precision_score(y,p)),
        'brier':float(brier_score_loss(y,p)), 'log_loss':float(log_loss(y,np.clip(p,1e-7,1-1e-7),labels=[0,1])),
        'balanced_accuracy':float(balanced_accuracy_score(y,pred)),
        'macro_f1':float(f1_score(y,pred,average='macro',zero_division=0)),
        'sensitivity':float(tp/(tp+fn)) if tp+fn else np.nan,
        'specificity':float(tn/(tn+fp)) if tn+fp else np.nan,
        'false_negatives':int(fn),'false_positives':int(fp),
        'referrals':int(np.sum(ref)) if ref is not None else 0,
        'referral_fraction':float(np.mean(ref)) if ref is not None else 0.}

def evaluate_policies(pred,context):
    rows=[]; y=pred.y.to_numpy(); b=pred.basic.to_numpy(); a=pred.advanced.to_numpy()
    for budget in BUDGETS:
        for policy in PLAN['primary_policies']:
            runs=range(PLAN['random_policy_replicates']) if policy=='random' else range(1)
            vals=[]
            for r in runs:
                scores=np.random.default_rng(SEED+r).uniform(size=len(pred)) if policy=='random' else pred[policy]
                ref=refer_mask(scores,budget); p=np.where(ref,a,b)
                m=metrics(y,p,ref)
                m['new_errors']=int(np.sum(ref & ((b>=.5)==y) & ((a>=.5)!=y)))
                m['corrected_errors']=int(np.sum(ref & ((b>=.5)!=y) & ((a>=.5)==y)))
                vals.append(m)
            avg={k:float(np.mean([v[k] for v in vals])) for k in vals[0]}
            rows.append({**context,'policy':policy,'budget':budget,**avg})
    return rows

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--mode',choices=['audit','develop','test'],required=True)
    parser.add_argument('--cohort',choices=PLAN['cohorts']); parser.add_argument('--family',choices=['logistic','random_forest','hist_gradient'])
    args=parser.parse_args()
    for folder in ['results','models']: (ROOT/folder).mkdir(exist_ok=True)
    audits=[]; manifest=[]
    for name in ([args.cohort] if args.cohort else PLAN['cohorts']):
        d,basic,extra,audit=load_cohort(name); tr,te=split_cohort(d); audits.append(audit)
        for idx in tr: manifest.append({'cohort':name,'id':d.iloc[idx].id,'partition':'development'})
        for idx in te: manifest.append({'cohort':name,'id':d.iloc[idx].id,'partition':'locked_test'})
        if args.mode=='audit': continue
        for family in ([args.family] if args.family else ['logistic','random_forest','hist_gradient']):
            start=time.time(); all_pred=[]; rows=[]; fitted_audit=[]
            dev=d.iloc[tr].reset_index(drop=True)
            if args.mode=='develop':
                for repeat in range(PLAN['development_repeats']):
                    cv=StratifiedKFold(PLAN['development_outer_folds'],shuffle=True,random_state=SEED+repeat)
                    repeat_pred=[]
                    for fold,(fit,ev) in enumerate(cv.split(dev,dev.y)):
                        bundle=fit_bundle(dev.iloc[fit],basic,extra,family,SEED+repeat*10+fold)
                        pr=predict_bundle(bundle,dev.iloc[ev]); pr['fold']=fold; repeat_pred.append(pr)
                        fitted_audit.append({'repeat':repeat,'fold':fold,'certainty_positive_n':bundle['certainty_target_positive_n']})
                    # Ranking at one shared batch budget after all participants have out-of-fold predictions.
                    pr=pd.concat(repeat_pred).sort_values('id').reset_index(drop=True)
                    pr['repeat']=repeat; pr['cohort']=name; pr['family']=family; all_pred.append(pr)
                    rows.extend(evaluate_policies(pr,{'cohort':name,'family':family,'repeat':repeat,'phase':'development'}))
            else:
                sentinel=ROOT/'results'/f'test_opened_{name}_{family}.json'
                if sentinel.exists(): raise RuntimeError('Locked test already evaluated. Preserve the existing run; do not retune on test.')
                bundle=fit_bundle(dev,basic,extra,family,SEED)
                joblib.dump(bundle,ROOT/'models'/f'{name}_{family}.joblib')
                pr=predict_bundle(bundle,d.iloc[te]).sort_values('id').reset_index(drop=True)
                pr['repeat']=0; pr['cohort']=name; pr['family']=family; all_pred.append(pr)
                rows.extend(evaluate_policies(pr,{'cohort':name,'family':family,'repeat':0,'phase':'test'}))
                sentinel.write_text(json.dumps({'opened_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
                    'protocol_sha256':hashlib.sha256((ROOT/'protocol.json').read_bytes()).hexdigest(),
                    'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    'certainty_positive_n':bundle['certainty_target_positive_n']},indent=2))
            pd.concat(all_pred).to_csv(ROOT/'results'/f'{args.mode}_{name}_{family}_predictions.csv',index=False)
            pd.DataFrame(rows).to_csv(ROOT/'results'/f'{args.mode}_{name}_{family}_metrics.csv',index=False)
            (ROOT/'results'/f'{args.mode}_{name}_{family}_fit_audit.json').write_text(json.dumps(fitted_audit,indent=2))
            print(f'{args.mode} {name} {family}: n={len(d)}, dev={len(tr)}, test={len(te)}, {time.time()-start:.1f}s',flush=True)
    if args.mode=='audit':
        (ROOT/'results/data_audit.json').write_text(json.dumps(audits,indent=2))
        pd.DataFrame(manifest).to_csv(ROOT/'results/split_manifest.csv',index=False)
        (ROOT/'results/environment.json').write_text(json.dumps({'python':platform.python_version(),
            'sklearn':sklearn.__version__,'pandas':pd.__version__,'numpy':np.__version__,'joblib':joblib.__version__},indent=2))
        print(json.dumps(audits,indent=2))

if __name__=='__main__': main()
