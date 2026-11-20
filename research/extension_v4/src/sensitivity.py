"""Nested source-only threshold intervention on the original AD/FTD task."""
from pathlib import Path
import json,sys,hashlib,time,warnings,collections
import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.exceptions import ConvergenceWarning
from common import sensitivity_threshold,metrics
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results';SEED=20261124
sys.path.insert(0,str(ROOT.parent/'extension_v3/src'))
import experiment as ex
POLICIES=['basic','full','uncertainty','ridge_gain']

def pair(d,basic,extra,seed):
    b,bc=ex.estimator(('original','lr',1.),basic,extra,d,'basic',seed)
    a,ac=ex.estimator(('cov','lr',.3),basic,extra,d,'advanced',seed)
    b.fit(d[bc],d.y);a.fit(d[ac],d.y)
    return {'basic':b,'advanced':a,'basic_columns':bc,'advanced_columns':ac,'training_ids':d.id.tolist()}
def pair_predict(fit,d):
    assert set(fit['training_ids']).isdisjoint(d.id)
    return fit['basic'].predict_proba(d[fit['basic_columns']])[:,1],fit['advanced'].predict_proba(d[fit['advanced_columns']])[:,1]
def fit(d,basic,extra,seed):
    d=d.reset_index(drop=True);pb=np.empty(len(d));pa=np.empty(len(d));parts=[]
    for fold,(tr,va) in enumerate(StratifiedKFold(3,shuffle=True,random_state=seed).split(d,d.y)):
        models=pair(d.iloc[tr],basic,extra,seed+fold);pb[va],pa[va]=pair_predict(models,d.iloc[va])
        parts.append({'training_ids':d.id.iloc[tr].tolist(),'validation_ids':d.id.iloc[va].tolist()})
    prep=make_pipeline(SimpleImputer(strategy='median',add_indicator=True),StandardScaler()).fit(d[basic])
    design=np.column_stack([prep.transform(d[basic]),pb,pb*(1-pb)])
    gain=(d.y.to_numpy()-pb)**2-(d.y.to_numpy()-pa)**2
    return {'models':pair(d,basic,extra,seed),'gate':Ridge(alpha=10).fit(design,gain),'prep':prep,'basic_columns':basic,'gate_partitions':parts}
def predict(bundle,d):
    pb,pa=pair_predict(bundle['models'],d);design=np.column_stack([bundle['prep'].transform(d[bundle['basic_columns']]),pb,pb*(1-pb)])
    scores={'uncertainty':-np.abs(pb-.5),'ridge_gain':bundle['gate'].predict(design)}
    predictions={};referrals={}
    for p in POLICIES:
        mask=np.zeros(len(d),bool) if p=='basic' else np.ones(len(d),bool) if p=='full' else ex.prior.original.refer_mask(scores[p],.3)
        predictions[p]=np.where(mask,pa,pb);referrals[p]=mask
        assert np.isfinite(predictions[p]).all()
    return predictions,referrals

def crossfit(d,basic,extra,seed):
    d=d.reset_index(drop=True);prob={p:np.empty(len(d)) for p in POLICIES};parts=[]
    for fold,(tr,va) in enumerate(StratifiedKFold(3,shuffle=True,random_state=seed).split(d,d.y)):
        bundle=fit(d.iloc[tr],basic,extra,seed+fold);pred,_=predict(bundle,d.iloc[va])
        for p in POLICIES:prob[p][va]=pred[p]
        parts.append({'training_ids':d.id.iloc[tr].tolist(),'validation_ids':d.id.iloc[va].tolist(),'gate_partitions':bundle['gate_partitions']})
    return prob,parts

def main():
    sentinel=OUT/'sensitivity_started.json';assert not sentinel.exists(),'Source-only fixed analysis already started'
    sentinel.write_text(json.dumps({'started_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'protocol_sha256':hashlib.sha256((ROOT/'protocol.json').read_bytes()).hexdigest()},indent=2))
    d,basic,extra,forbidden=ex.load_development('eeg_ad_ftd');predictions=[];audits=[]
    assert len(d)==41 and d.y.sum()==25 and set(d.id).isdisjoint(forbidden)
    for repeat in range(3):
        for fold,(tr,va) in enumerate(StratifiedKFold(4,shuffle=True,random_state=SEED+repeat).split(d,d.y)):
            train=d.iloc[tr].reset_index(drop=True);test=d.iloc[va];seed=SEED+repeat*10+fold
            oof,parts=crossfit(train,basic,extra,seed);bundle=fit(train,basic,extra,seed);probs,refs=predict(bundle,test)
            audits.append({'repeat':repeat,'fold':fold,'outer_training':train.id.tolist(),'outer_validation':test.id.tolist(),'threshold_partitions':parts,'gate_partitions':bundle['gate_partitions']})
            for policy in POLICIES:
                threshold=sensitivity_threshold(train.y,oof[policy])
                for operating,t in [('default',.5),('sensitivity90',threshold)]:
                    predictions.extend({'id':pid,'y':int(y),'probability':float(p),'threshold':float(t),'referral':bool(r),'repeat':repeat,'fold':fold,'policy':policy,'operating':operating} for pid,y,p,r in zip(test.id,test.y,probs[policy],refs[policy]))
            print('AD/FTD source repeat/fold',repeat+1,fold+1,flush=True)
    pred=pd.DataFrame(predictions);pred.to_csv(OUT/'sensitivity_predictions.csv',index=False);rows=[]
    for (repeat,policy,operating),g in pred.groupby(['repeat','policy','operating']):
        assert set(g.id)==set(d.id) and g.id.is_unique
        y=g.y.to_numpy();decision=g.probability.to_numpy()>=g.threshold.to_numpy();m=metrics(y,g.probability,.5)
        tp=int(np.sum(decision&(y==1)));tn=int(np.sum(~decision&(y==0)))
        m.update(true_positives=tp,false_negatives=int(y.sum())-tp,true_negatives=tn,false_positives=int((y==0).sum())-tn,sensitivity=tp/sum(y==1),specificity=tn/sum(y==0),threshold=float(g.threshold.mean()),referrals=int(g.referral.sum()))
        for k in ['sensitivity_low','sensitivity_high','specificity_low','specificity_high']:m.pop(k)
        rows.append({'repeat':int(repeat),'policy':policy,'operating':operating,**m})
    pd.DataFrame(rows).to_csv(OUT/'sensitivity_metrics.csv',index=False)
    oof,parts=crossfit(d,basic,extra,SEED);bundle=fit(d,basic,extra,SEED)
    thresholds={p:sensitivity_threshold(d.y,oof[p]) for p in POLICIES}
    bundle['thresholds']=thresholds;(ROOT/'models').mkdir(exist_ok=True);joblib.dump(bundle,ROOT/'models/sensitivity_ad_ftd.joblib')
    audits.append({'final_threshold_partitions':parts});(OUT/'sensitivity_partitions_patient.json').write_text(json.dumps(audits,indent=2))
    (OUT/'sensitivity_frozen.json').write_text(json.dumps({'thresholds':thresholds,'model_sha256':hashlib.sha256((ROOT/'models/sensitivity_ad_ftd.joblib').read_bytes()).hexdigest(),'scope':'Original41source-development participants only; no independent validation'},indent=2))
    print('Completed original-task nested sensitivity study',flush=True)
if __name__=='__main__':
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter('always',RuntimeWarning);warnings.simplefilter('error',ConvergenceWarning);main()
    (OUT/'sensitivity_warnings.json').write_text(json.dumps(dict(collections.Counter(str(x.message) for x in w)),indent=2))
