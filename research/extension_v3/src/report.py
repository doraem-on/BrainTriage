"""Summarize the fixed matrix and audit saved models without evaluating holdouts."""
from pathlib import Path
import json, hashlib, warnings
import numpy as np
import pandas as pd
import joblib
from scipy.special import expit
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
import experiment as ex
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'results'

def main():
    rows=pd.read_csv(OUT/'outer_metrics.csv')
    assert len(rows)==2352 and np.isfinite(rows.select_dtypes('number')).all().all()
    metrics=['brier','auroc','sensitivity','specificity','false_negatives','referrals']
    aggregate=rows.groupby(['cohort','variant','policy','budget'])[metrics].agg(['mean','min','max'])
    aggregate.columns=['_'.join(x) for x in aggregate.columns]
    aggregate.reset_index().to_csv(OUT/'aggregate_metrics.csv',index=False)
    comparisons=[];table=[]
    def sample(c,v,p):
        return rows[(rows.cohort==c)&(rows.variant==v)&(rows.policy==p)&rows.budget.eq(.3)].sort_values('repeat')
    for c in ex.PLAN['cohorts']:
        v='nested_rich_blend' if c=='eeg_ad_ftd' else 'nested_original_blend'
        for label,variant,policy in [('Fixed uncertainty','legacy_fixed','uncertainty'),('Tuned basic',v,'basic'),('Tuned full',v,'full'),('Tuned uncertainty',v,'uncertainty'),('Tuned nonlinear gain',v,'nonlinear_gain')]:
            s=sample(c,variant,policy)
            table.append({'cohort':c,'method':label,'variant':variant,**{m:float(s[m].mean()) for m in metrics},'brier_min':float(s.brier.min()),'brier_max':float(s.brier.max())})
        for label,rv,rp in [('primary_matched_uncertainty',v,'uncertainty'),('secondary_fixed_uncertainty','legacy_fixed','uncertainty')]:
            delta=sample(c,v,'nonlinear_gain').brier.to_numpy()-sample(c,rv,rp).brier.to_numpy()
            comparisons.append({'cohort':c,'comparison':label,'candidate':v,'delta_brier_mean':float(delta.mean()),'delta_brier_min':float(delta.min()),'delta_brier_max':float(delta.max()),'repeat_deltas':delta.tolist(),'improved_repeats':int((delta<0).sum()),'interpretation':'Negative favors nonlinear gain; three correlated repeats, no confidence interval or significance claim.'})
    pd.DataFrame(table).to_csv(OUT/'primary_table.csv',index=False)
    (OUT/'comparisons.json').write_text(json.dumps(comparisons,indent=2))
    checks=[];partitions=json.loads((OUT/'partitions_patient.json').read_text())
    for c in ex.PLAN['cohorts']:
        d,b,e,forbidden=ex.load_development(c);ids=set(d.id)
        for repeat in range(3):
            folds=[p for p in partitions if p['cohort']==c and p['repeat']==repeat]
            validation=[]
            for p in folds:
                tr=set(p['training_ids']);va=set(p['validation_ids'])
                assert tr.isdisjoint(va) and tr|va==ids and (tr|va).isdisjoint(forbidden)
                validation+=p['validation_ids']
            assert len(validation)==len(ids) and set(validation)==ids
        for file in OUT.glob(c+'_*_predictions.csv'):
            pred=pd.read_csv(file,dtype={'id':str});assert set(pred.id)==ids and pred.id.is_unique
            assert np.isfinite(pred.drop(columns='id')).all().all()
        for file in (ROOT/'models').glob(c+'_*.joblib'):
            bundle=joblib.load(file);assert set(bundle['training_ids'])==ids
            alpha=ex.blend_weight(bundle['oof_y'],bundle['oof_basic'],bundle['oof_advanced'])
            assert abs(alpha-bundle['alpha'])<1e-12
            pb=bundle['oof_basic'];pa=bundle['oof_advanced'];y=bundle['oof_y']
            assert np.mean((y-pb-alpha*(pa-pb))**2)<=min(np.mean((y-pb)**2),np.mean((y-pa)**2))+1e-12
            for role in ['basic_model','advanced_model']:
                model=bundle[role];cal=model['model'].calibrated_classifiers_[0]
                pipe=cal.estimator;x=np.asarray(pipe[:-1].transform(d[model['columns']]))
                clf=pipe[-1]
                if isinstance(clf,LogisticRegression):decision=np.einsum('ij,j->i',x,clf.coef_[0])+clf.intercept_[0]
                elif isinstance(clf,SVC):
                    # Direct differences avoid BLAS matrix multiplication and cancellation.
                    distances=np.sum((x[:,None,:]-clf.support_vectors_[None,:,:])**2,axis=2)
                    kernel=np.exp(-clf._gamma*distances)
                    decision=np.einsum('ij,j->i',kernel,clf.dual_coef_[0])+clf.intercept_[0]
                else:raise TypeError(type(clf))
                sigmoid=cal.calibrators[0];manual=expit(-(sigmoid.a_*decision+sigmoid.b_))
                actual=model['model'].predict_proba(d[model['columns']])[:,1]
                error=float(np.max(np.abs(actual-manual)));assert error<1e-10
                checks.append({'bundle':file.name,'role':role,'classifier':type(clf).__name__,'maximum_probability_error':error,'n_arithmetic_check_only':len(d)})
    feature=json.loads((OUT/'feature_provenance.json').read_text())
    assert hashlib.sha256((ROOT/'data_raw/eeg_development_features.csv').read_bytes()).hexdigest()==feature['feature_sha256']
    assert hashlib.sha256((ROOT/'src/extract_features.py').read_bytes()).hexdigest()==feature['extractor_sha256']
    started=json.loads((OUT/'experiment_started.json').read_text())
    assert hashlib.sha256((ROOT/'src/experiment.py').read_bytes()).hexdigest()==started['experiment_sha256']
    audit={'final_models_checked':len(checks)//2,'probability_checks':checks,'outer_partition_audit':'passed: all 48 partitions disjoint, development-only, full validation coverage per repeat','prediction_files_checked':len(list(OUT.glob('*_predictions.csv'))),'feature_and_experiment_hashes':'matched','holdout_evaluations':0,'limitations':'Independent arithmetic check covers final calibrated classifier calculations, not every intermediate estimator or BLAS operation. Training-runtime warnings retained separately; all saved predictions finite.'}
    (OUT/'verification.json').write_text(json.dumps(audit,indent=2))
    print(pd.DataFrame(table)[['cohort','method','brier','auroc','false_negatives']].round(5).to_string(index=False))
    print(json.dumps(comparisons,indent=2))
    print('Verified',len(checks),'classifier calculations; maximum error',max(x['maximum_probability_error'] for x in checks))
if __name__=='__main__':
    with warnings.catch_warnings():
        warnings.simplefilter('ignore',RuntimeWarning);main()
