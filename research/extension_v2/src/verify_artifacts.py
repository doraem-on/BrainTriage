"""Read-only numerical and source-integrity audit of completed experiments."""
import hashlib,json
from pathlib import Path
import numpy as np
import pandas as pd
import joblib
from scipy.special import expit
import research as r
from acquire_eeg import features
from eeg_ranges import read_window

ROOT=r.ROOT
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

lock=json.loads((ROOT/'results/final_evaluation_lock.json').read_text())
assert sha(ROOT/'protocol.json')==lock['protocol_sha256']
assert sha(ROOT/'src/research.py')==lock['research_sha256']
report={'protocol_unchanged':True,'training_code_unchanged':True,'bundles':[]}
for cohort in r.PLAN['cohorts']:
    d,b,a,tr,te=r.load(cohort);evaluation=d.iloc[te]
    for config in r.PLAN['configurations']:
        path=ROOT/'models'/f'{cohort}_{config}.joblib';bundle=joblib.load(path)
        pred=r.predict(bundle,evaluation).sort_values('id').reset_index(drop=True)
        recorded=pd.read_csv(ROOT/'results'/f'holdout_{cohort}_{config}_predictions.csv',dtype={'id':str})
        assert pred.id.tolist()==recorded.id.tolist()
        cols=list(pred.select_dtypes('number').columns)
        np.testing.assert_allclose(pred[cols],recorded[cols],atol=1e-12,rtol=1e-12)
        errors=[]
        for name,cols in [('basic',bundle['basic']),('advanced',bundle['basic']+bundle['extra'])]:
            model=bundle[name+'_model']
            calibrated=hasattr(model,'calibrated_classifiers_')
            pipe=model.calibrated_classifiers_[0].estimator if calibrated else model
            x=pipe[:-1].transform(evaluation[cols]);clf=pipe[-1]
            # Independent of the BLAS matrix multiplication used in predict_proba.
            decision=np.einsum('ij,j->i',x,clf.coef_[0],optimize=False)+clf.intercept_[0]
            if calibrated:
                calibration=model.calibrated_classifiers_[0].calibrators[0]
                manual=expit(-(calibration.a_*decision+calibration.b_))
            else:manual=expit(decision)
            actual=model.predict_proba(evaluation[cols])[:,1]
            np.testing.assert_allclose(manual,actual,atol=1e-12,rtol=1e-12)
            errors.append(float(np.max(np.abs(manual-actual))))
        x=bundle['preprocessor'].transform(evaluation[bundle['basic']]);phi=np.column_stack([np.ones(len(x)),x])
        mean=np.einsum('ij,j->i',phi,bundle['bayes'].coef_,optimize=False)
        np.testing.assert_allclose(mean,bundle['bayes'].predict(phi),atol=1e-12,rtol=1e-12)
        report['bundles'].append({'cohort':cohort,'configuration':config,'sha256':sha(path),'holdout_predictions_reproduced':True,'maximum_manual_probability_error':max(errors)})

source=json.loads((ROOT/'results/eeg_provenance.json').read_text())
assert len(source['recordings'])==59
assert sha(ROOT/'data_raw/eeg_features.csv')==source['feature_file_sha256']
count=0
for item in source['source_metadata']:
    assert sha(ROOT/'data_raw'/item['path'])==item['sha256']
for record in source['recordings']:
    for byte_range in record['range_reads']:
        candidates=list((ROOT/'data_raw/ranges'/record['id']).glob(f"{byte_range['start']}_*.bin"))
        assert any(sha(path)==byte_range['sha256'] for path in candidates)
        count+=1
report['eeg_source_ranges_verified']=count
report['eeg_participants']=59
report['range_reader_sha256']=sha(ROOT/'src/eeg_ranges.py')
report['full_file_comparisons']=[]
for pid in ['sub-001','sub-003','sub-004']:
    eeg,_=read_window(pid);partial,_=features(eeg)
    complete,_=features(ROOT/'data_raw/derivatives'/pid/'eeg'/f'{pid}_task-eyesclosed_eeg.set')
    np.testing.assert_array_equal(list(partial.values()),list(complete.values()))
    report['full_file_comparisons'].append({'participant':pid,'twenty_features_exactly_equal':True})
pred=pd.read_csv(ROOT/'results/holdout_eeg_ad_ftd_logistic_predictions.csv')
p,ref=r.policy_predictions(pred,'bayes_mean',.3);q,ref2=r.policy_predictions(pred,'bayes_lcb_1',.3)
assert np.array_equal(ref,ref2) and np.array_equal(p,q)
report['eeg_primary_contrast']='Identical selected participants and predictions; zero conditional interval does not imply population equivalence.'
(ROOT/'results/numerical_verification.json').write_text(json.dumps(report,indent=2))
print(json.dumps({'verified_bundles':len(report['bundles']),'eeg_source_ranges':count,'full_file_feature_matches':3,'maximum_probability_error':max(x['maximum_manual_probability_error'] for x in report['bundles'])},indent=2))
