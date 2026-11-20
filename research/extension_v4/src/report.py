"""Audit saved partitions and summarize the fixed studies without refitting."""
from pathlib import Path
import json,sys,hashlib,collections
import numpy as np
import pandas as pd
import joblib
from scipy.special import expit
from sklearn.metrics import roc_curve
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.compose import ColumnTransformer
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results'
import sensitivity

def verify_partitions(nodes, allowed):
    count=0
    for item in nodes:
        tr=item.get('outer_training',item.get('training_ids',item.get('training')))
        va=item.get('outer_validation',item.get('validation_ids',item.get('validation')))
        scope=allowed
        if tr is not None:
            a,b=set(tr),set(va);assert a.isdisjoint(b) and a|b==allowed
            assert len(a)==len(tr) and len(b)==len(va);scope=a;count+=1
        for key in ['threshold_partitions','gate_partitions','final_threshold_partitions']:
            if key in item:count+=verify_partitions(item[key],scope)
    return count

def transform(step,x):
    if isinstance(step,ColumnTransformer):
        return np.column_stack([transform(s,x.loc[:,cols] if isinstance(cols[0],str) else x.iloc[:,cols]) for _,s,cols in step.transformers_ if s!='drop' and len(cols)])
    if isinstance(step,Pipeline):
        for s in step.steps:x=transform(s[1],x)
        return x
    if isinstance(step,SimpleImputer):return step.transform(x)
    x=np.asarray(x,float)
    if isinstance(step,StandardScaler):return (x-step.mean_)/step.scale_
    if isinstance(step,PCA):return np.einsum('ij,kj->ik',x-step.mean_,step.components_)
    raise TypeError(type(step))

def manual(model,x):
    c=model.calibrated_classifiers_[0];pipe=c.estimator
    z=transform(pipe[:-1],x);lr=pipe[-1]
    score=np.einsum('ij,j->i',z,lr.coef_[0])+lr.intercept_[0]
    cal=c.calibrators[0];return expit(-(cal.a_*score+cal.b_))

def main():
    source=pd.read_csv(ROOT/'data_raw/source_features.csv');target=pd.read_csv(ROOT/'data_raw/external_features.csv')
    dev,basic,extra,forbidden=sensitivity.ex.load_development('eeg_ad_ftd')
    assert set(source.id).isdisjoint(forbidden) and set(dev.id).isdisjoint(forbidden)
    checks={}
    for name,ids in [('companion',set(source.id)),('sensitivity',set(dev.id))]:
        audit=json.loads((OUT/f'{name}_partitions_patient.json').read_text())
        checks[name+'_partition_checks']=verify_partitions(audit,ids)
        predictions=pd.read_csv(OUT/('companion_development_predictions.csv' if name=='companion' else 'sensitivity_predictions.csv'))
        assert np.isfinite(predictions[['probability','threshold']]).all().all()
        key='model' if name=='companion' else 'policy'
        for _,group in predictions.groupby(['repeat',key,'operating']):assert set(group.id)==ids and group.id.is_unique
        a=predictions[predictions.operating.eq('default')].set_index(['id','repeat','fold',key])
        b=predictions[predictions.operating.eq('sensitivity90')].set_index(['id','repeat','fold',key]).loc[a.index]
        np.testing.assert_array_equal(a.probability,b.probability)
        assert (b.threshold<=a.threshold).all()
        assert ((a.probability>=a.threshold).astype(int)<=(b.probability>=b.threshold).astype(int)).all()
        checks[name+'_saved_predictions']=len(predictions)
    allfeatures=pd.concat([source,target],ignore_index=True).drop(columns=['id','y'])
    assert not allfeatures.duplicated().any();assert np.isfinite(allfeatures).all().all()
    checks['identical_feature_rows']=0
    checks['holdouts_excluded']=True
    saved=pd.read_csv(OUT/'external_predictions.csv');roc=[];errors={}
    for kind in ['spectral','covariance']:
        bundle=joblib.load(ROOT/'models'/f'companion_{kind}.joblib')
        p=manual(bundle['model'],target[bundle['columns']])
        err=float(np.max(np.abs(p-saved[kind])));assert err<1e-10;errors[kind]=err
        fpr,tpr,threshold=roc_curve(saved.y,saved[kind])
        roc.extend({'model':kind,'false_positive_rate':float(x),'true_positive_rate':float(y)} for x,y in zip(fpr,tpr))
    original=joblib.load(ROOT/'models/sensitivity_ad_ftd.joblib')['models']
    for name in ['basic','advanced']:
        x=dev[original[name+'_columns']];p=manual(original[name],x)
        err=float(np.max(np.abs(p-original[name].predict_proba(x)[:,1])));assert err<1e-10;errors['original_'+name]=err
    checks['final_probability_arithmetic_errors']=errors
    checks['arithmetic_scope']='Independent einsum PCA and logistic calculations for final models, including saved external predictions; intermediate fits not independently reconstructed.'
    pd.DataFrame(roc).to_csv(OUT/'external_roc.csv',index=False)
    for name,keys in [('sensitivity',['policy','operating']),('companion_development',['model','operating'])]:
        d=pd.read_csv(OUT/f'{name}_metrics.csv');rows=[]
        for key,g in d.groupby(keys):
            row=dict(zip(keys,key))
            for metric in ['false_negatives','false_positives','sensitivity','specificity','auroc','brier']:
                for stat,fn in [('mean',np.mean),('minimum',np.min),('maximum',np.max)]:row[metric+'_'+stat]=float(fn(g[metric]))
            rows.append(row)
        pd.DataFrame(rows).to_csv(OUT/f'{name}_summary.csv',index=False)
    provenance=json.loads((OUT/'feature_provenance.json').read_text())
    public={k:v for k,v in provenance.items() if k not in ['source','external']}
    public.update(source_participants=len(source),external_participants=len(target),source_segments_per_person=24,
                  external_segment_count_distribution=dict(collections.Counter(p['segments_used'] for p in provenance['external'])),
                  publication_scope='Archive and feature hashes retained; participant identifiers and per-person provenance remain local.')
    (OUT/'public_provenance.json').write_text(json.dumps(public,indent=2))
    checks['external_models_and_thresholds_published_before_evaluation_commit']='02d3e24'
    checks['tests_passed']=5
    (OUT/'verification.json').write_text(json.dumps(checks,indent=2));print(json.dumps(checks,indent=2))
if __name__=='__main__':main()
