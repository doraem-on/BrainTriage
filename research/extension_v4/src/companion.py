"""Train on Greece; freeze artifacts; evaluate Spain exactly once without adaptation."""
from pathlib import Path
import json,sys,hashlib,time,warnings,collections,argparse
import numpy as np
import pandas as pd
import joblib
from scipy.special import expit
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import StratifiedKFold
from sklearn.exceptions import ConvergenceWarning
from common import sensitivity_threshold,metrics
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results';SEED=20261124
MODELS=['spectral','covariance']
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def classifier(kind,seed):
    steps=[SimpleImputer(strategy='median'),StandardScaler()]
    if kind=='covariance':steps += [PCA(n_components=5,svd_solver='full'),StandardScaler()]
    steps += [LogisticRegression(C=.3 if kind=='covariance' else 1.,max_iter=3000,random_state=seed)]
    return CalibratedClassifierCV(make_pipeline(*steps),method='sigmoid',cv=StratifiedKFold(3,shuffle=True,random_state=seed),ensemble=False)
def columns(d,kind):return [c for c in d if c.startswith('cov_' if kind=='covariance' else 'spectral_')]
def fit(d,kind,seed):
    cols=columns(d,kind);model=classifier(kind,seed).fit(d[cols],d.y)
    return {'model':model,'columns':cols,'training_ids':d.id.tolist(),'kind':kind}
def predict(bundle,d):
    assert set(bundle['training_ids']).isdisjoint(d.id),'Training/evaluation participant overlap'
    p=bundle['model'].predict_proba(d[bundle['columns']])[:,1]
    assert np.isfinite(p).all() and np.all((p>=0)&(p<=1));return p
def crossfit(d,kind,seed,folds=3):
    p=np.empty(len(d));manifest=[]
    for fold,(tr,va) in enumerate(StratifiedKFold(folds,shuffle=True,random_state=seed).split(d,d.y)):
        bundle=fit(d.iloc[tr],kind,seed+fold);p[va]=predict(bundle,d.iloc[va])
        manifest.append({'training':d.id.iloc[tr].tolist(),'validation':d.id.iloc[va].tolist()})
    return p,manifest

def train():
    sentinel=OUT/'companion_training_started.json'
    assert not sentinel.exists(),'Fixed study already started; inspect results, do not retune.'
    assert sha(ROOT/'protocol.json')==(ROOT/'protocol.sha256').read_text().split()[0]
    d=pd.read_csv(ROOT/'data_raw/source_features.csv').sort_values('id').reset_index(drop=True)
    assert len(d)==54 and d.y.sum()==25 and d.id.is_unique and all(d.id.str.startswith('sub-'))
    sentinel.write_text(json.dumps({'started_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'source_sha256':sha(ROOT/'data_raw/source_features.csv'),'code_sha256':sha(__file__),'protocol_sha256':sha(ROOT/'protocol.json')},indent=2))
    rows=[];audits=[];all_pred=[]
    for repeat in range(3):
        for fold,(tr,va) in enumerate(StratifiedKFold(4,shuffle=True,random_state=SEED+repeat).split(d,d.y)):
            training=d.iloc[tr].reset_index(drop=True);validation=d.iloc[va]
            for kind in MODELS:
                oof,partitions=crossfit(training,kind,SEED+repeat*10+fold)
                threshold=sensitivity_threshold(training.y,oof)
                bundle=fit(training,kind,SEED+repeat*10+fold);p=predict(bundle,validation)
                for operating,t in [('default',.5),('sensitivity90',threshold)]:
                    all_pred.extend({'id':pid,'y':int(y),'probability':float(prob),'threshold':t,'repeat':repeat,'fold':fold,'model':kind,'operating':operating} for pid,y,prob in zip(validation.id,validation.y,p))
                audits.append({'repeat':repeat,'fold':fold,'model':kind,'outer_training':training.id.tolist(),'outer_validation':validation.id.tolist(),'threshold_partitions':partitions})
            print('Companion source outer repeat/fold',repeat+1,fold+1,flush=True)
    pred=pd.DataFrame(all_pred);pred.to_csv(OUT/'companion_development_predictions.csv',index=False)
    for (repeat,kind,operating),g in pred.groupby(['repeat','model','operating']):
        m=metrics(g.y,g.probability,.5)
        decisions=g.probability.to_numpy()>=g.threshold.to_numpy();y=g.y.to_numpy()
        tp=int(np.sum(decisions&(y==1)));tn=int(np.sum(~decisions&(y==0)))
        m.update(true_positives=tp,false_negatives=int(y.sum())-tp,true_negatives=tn,false_positives=int((y==0).sum())-tn,sensitivity=tp/sum(y==1),specificity=tn/sum(y==0),threshold=float(g.threshold.mean()))
        for k in ['sensitivity_low','sensitivity_high','specificity_low','specificity_high']:m.pop(k)
        rows.append({'repeat':int(repeat),'model':kind,'operating':operating,'threshold_description':'Mean of training-only fold thresholds; predictions use their own fold threshold',**m})
    pd.DataFrame(rows).to_csv(OUT/'companion_development_metrics.csv',index=False)
    frozen={'scope':'EEG-only AD versus HC companion, not original v3 AD/FTD triage','models':{},'protocol_sha256':sha(ROOT/'protocol.json'),'source_feature_sha256':sha(ROOT/'data_raw/source_features.csv'),'code_sha256':sha(__file__),'common_code_sha256':sha(ROOT/'src/common.py'),'feature_code_sha256':sha(ROOT/'src/features.py'),'label_mapping_source_blob':'b6b9c130b9e519366c2844a8c203b80c9d5d8536'}
    (ROOT/'models').mkdir(exist_ok=True)
    for kind in MODELS:
        oof,parts=crossfit(d,kind,SEED,5);threshold=sensitivity_threshold(d.y,oof);bundle=fit(d,kind,SEED)
        bundle['threshold']=threshold;path=ROOT/'models'/f'companion_{kind}.joblib';joblib.dump(bundle,path)
        cal=bundle['model'].calibrated_classifiers_[0];pipe=cal.estimator;x=pipe[:-1].transform(d[bundle['columns']]);lr=pipe[-1]
        decision=np.einsum('ij,j->i',x,lr.coef_[0])+lr.intercept_[0];a=cal.calibrators[0];manual=expit(-(a.a_*decision+a.b_))
        err=float(np.max(np.abs(manual-bundle['model'].predict_proba(d[bundle['columns']])[:,1])));assert err<1e-10
        frozen['models'][kind]={'file':path.name,'sha256':sha(path),'threshold':threshold,'source_threshold_fit_sensitivity':float(np.mean(oof[d.y.eq(1)]>=threshold)),'maximum_final_probability_arithmetic_error':err,'source_n':len(d)}
        audits.append({'final_model':kind,'threshold_partitions':parts})
    (OUT/'companion_partitions_patient.json').write_text(json.dumps(audits,indent=2))
    frozen['frozen_utc']=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime());(OUT/'external_freeze.json').write_text(json.dumps(frozen,indent=2))
    print('Frozen source-trained models and thresholds; external predictions not computed',flush=True)

def evaluate():
    lock=OUT/'external_evaluation_started.json';assert not lock.exists(),'External outcomes already opened; do not rerun to optimize results.'
    frozen=json.loads((OUT/'external_freeze.json').read_text())
    assert frozen['code_sha256']==sha(__file__) and frozen['common_code_sha256']==sha(ROOT/'src/common.py') and frozen['feature_code_sha256']==sha(ROOT/'src/features.py')
    assert frozen['protocol_sha256']==sha(ROOT/'protocol.json') and frozen['source_feature_sha256']==sha(ROOT/'data_raw/source_features.csv')
    for kind,m in frozen['models'].items():assert sha(ROOT/'models'/m['file'])==m['sha256']
    lock.write_text(json.dumps({'started_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'freeze_sha256':sha(OUT/'external_freeze.json'),'external_feature_sha256':sha(ROOT/'data_raw/external_features.csv')},indent=2))
    d=pd.read_csv(ROOT/'data_raw/external_features.csv');assert len(d)==23 and d.y.sum()==12 and d.id.is_unique and all(d.id.str.startswith('APAVA-'))
    rows=[];probs={};predictions=d[['id','y']].copy()
    for kind,m in frozen['models'].items():
        bundle=joblib.load(ROOT/'models'/m['file']);p=predict(bundle,d);probs[kind]=p;predictions[kind]=p
        for operating,t in [('default',.5),('sensitivity90',m['threshold'])]:rows.append({'cohort':'APAVA_external','model':kind,'operating':operating,**metrics(d.y,p,t)})
    pd.DataFrame(rows).to_csv(OUT/'external_metrics.csv',index=False);predictions.to_csv(OUT/'external_predictions.csv',index=False)
    rng=np.random.default_rng(SEED);y=d.y.to_numpy();pos=np.where(y==1)[0];neg=np.where(y==0)[0];draws=[]
    from sklearn.metrics import roc_auc_score
    for _ in range(2000):
        ix=np.r_[rng.choice(pos,len(pos),replace=True),rng.choice(neg,len(neg),replace=True)]
        draws.append([float(np.mean((y[ix]-probs['covariance'][ix])**2-(y[ix]-probs['spectral'][ix])**2)),float(roc_auc_score(y[ix],probs['covariance'][ix])-roc_auc_score(y[ix],probs['spectral'][ix]))])
    result={}
    for j,name in enumerate(['delta_brier','delta_auroc']):
        point=float(np.mean((y-probs['covariance'])**2-(y-probs['spectral'])**2)) if j==0 else float(roc_auc_score(y,probs['covariance'])-roc_auc_score(y,probs['spectral']))
        result[name]={'covariance_minus_spectral':point,'low':float(np.quantile(np.array(draws)[:,j],.025)),'high':float(np.quantile(np.array(draws)[:,j],.975))}
    result['scope']='Paired stratified participant bootstrap; conditional on frozen models; does not include source-training uncertainty.'
    (OUT/'external_contrasts.json').write_text(json.dumps(result,indent=2));print(pd.DataFrame(rows).to_string(index=False))
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['train','evaluate']);args=parser.parse_args()
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter('always',RuntimeWarning);warnings.simplefilter('error',ConvergenceWarning)
        train() if args.action=='train' else evaluate()
    (OUT/f'companion_{args.action}_warnings.json').write_text(json.dumps(dict(collections.Counter(str(x.message) for x in w)),indent=2))
