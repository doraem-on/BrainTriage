"""Fixed exploratory matrix on original development patients, with nested tuning."""
from pathlib import Path
import sys,json,hashlib,time,warnings,collections
import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression,Ridge
from sklearn.svm import SVC
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.calibration import CalibratedClassifierCV
from sklearn.exceptions import ConvergenceWarning
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parent/'extension_v2/src'))
import research as prior
PLAN=json.loads((ROOT/'protocol.json').read_text());SEED=PLAN['seed']

def load_development(cohort):
    full,basic,extra,train,test=prior.load(cohort)
    forbidden=set(full.iloc[test].id.astype(str));d=full.iloc[train].copy()
    if cohort=='eeg_ad_ftd':
        rich=pd.read_csv(ROOT/'data_raw/eeg_development_features.csv',dtype={'id':str})
        assert set(rich.id)==set(d.id) and set(rich.id).isdisjoint(forbidden)
        assert rich.set_index('id').y.equals(d.set_index('id').y.reindex(rich.id))
        d=rich
    d=d.sort_values('id').reset_index(drop=True)
    assert d.id.is_unique and set(d.id).isdisjoint(forbidden)
    return d,basic,extra,forbidden

def candidate_specs(role,mode,has_rich):
    if mode=='legacy_fixed':return [('original','lr',1.)]
    if role=='basic':return [('original','lr',c) for c in [.03,.3,1.,3.]]
    if mode=='nested_rich' and has_rich:
        return [('original','lr',1.)]+[('rich','lr',c) for c in [.03,.3,1.,3.]]+[('rich','svm',c) for c in [.3,3.]]+[('cov','lr',c) for c in [.3,3.]]
    return [('original','lr',c) for c in [.03,.3,1.,3.]]+[('original','svm',c) for c in [.3,3.]]

def estimator(spec,basic,extra,d,role,seed):
    representation,kind,c=spec
    if role=='basic':cols=basic
    elif representation=='rich':cols=basic+[x for x in d if x.startswith(('eeg_','rich_'))]
    elif representation=='cov':cols=basic+[x for x in d if x.startswith('cov_')]
    else:cols=basic+extra
    numerical=lambda:make_pipeline(SimpleImputer(strategy='median',add_indicator=True),StandardScaler())
    if representation=='cov' and role!='basic':
        covcols=[x for x in cols if x.startswith('cov_')]
        covpipe=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),PCA(n_components=5,svd_solver='full'))
        preprocessing=ColumnTransformer([('covariance',covpipe,covcols),('basic',numerical(),basic)])
        pipe=make_pipeline(preprocessing,StandardScaler(),LogisticRegression(C=c,max_iter=3000,random_state=seed))
    else:
        classifier=LogisticRegression(C=c,max_iter=3000,random_state=seed) if kind=='lr' else SVC(C=c,gamma='scale',kernel='rbf')
        pipe=make_pipeline(SimpleImputer(strategy='median',add_indicator=True),StandardScaler(),classifier)
    calibrated=CalibratedClassifierCV(pipe,method='sigmoid',cv=StratifiedKFold(3,shuffle=True,random_state=seed),ensemble=False)
    return calibrated,cols

def tune(d,basic,extra,role,mode,seed):
    specs=candidate_specs(role,mode,any(x.startswith('rich_') for x in d))
    losses=[]
    if len(specs)>1:
        folds=list(StratifiedKFold(3,shuffle=True,random_state=seed).split(d,d.y))
        for spec in specs:
            pred=np.empty(len(d))
            for tr,va in folds:
                model,cols=estimator(spec,basic,extra,d,role,seed)
                model.fit(d.iloc[tr][cols],d.y.iloc[tr]);pred[va]=model.predict_proba(d.iloc[va][cols])[:,1]
            assert np.isfinite(pred).all()
            losses.append(float(np.mean((d.y.to_numpy()-pred)**2)))
        chosen=int(np.argmin(losses))
    else:chosen=0;losses=[None]
    model,cols=estimator(specs[chosen],basic,extra,d,role,seed);model.fit(d[cols],d.y)
    return {'model':model,'columns':cols,'spec':specs[chosen],'candidate_scores':[{'spec':s,'brier':v} for s,v in zip(specs,losses)],'training_ids':d.id.tolist()}

def probability(model,d):
    assert set(d.id).isdisjoint(model['training_ids'])
    p=model['model'].predict_proba(d[model['columns']])[:,1]
    assert np.isfinite(p).all() and np.all((p>=0)&(p<=1))
    return p

def blend_weight(y,pb,pa):
    delta=np.asarray(pa)-np.asarray(pb);den=float(np.sum(delta**2))
    return float(np.clip(np.sum((np.asarray(y)-pb)*delta)/den,0,1)) if den>1e-12 else 0.

def gate_design(preprocessor,d,basic,pb):
    x=preprocessor.transform(d[basic])
    return np.column_stack([x,pb,pb*(1-pb)])

def fit_bundle(d,basic,extra,mode,seed):
    d=d.sort_values('id').reset_index(drop=True)
    basic_model=tune(d,basic,extra,'basic',mode,seed)
    advanced_model=tune(d,basic,extra,'advanced',mode,seed)
    pb=np.empty(len(d));pa=np.empty(len(d));nested=[]
    for fold,(tr,va) in enumerate(StratifiedKFold(3,shuffle=True,random_state=seed).split(d,d.y)):
        b=tune(d.iloc[tr],basic,extra,'basic',mode,seed+fold+1)
        a=tune(d.iloc[tr],basic,extra,'advanced',mode,seed+fold+1)
        pb[va]=probability(b,d.iloc[va]);pa[va]=probability(a,d.iloc[va])
        nested.append({'fold':fold,'training_ids':d.id.iloc[tr].tolist(),'validation_ids':d.id.iloc[va].tolist(),'basic':b['spec'],'advanced':a['spec']})
    prep=make_pipeline(SimpleImputer(strategy='median',add_indicator=True),StandardScaler()).fit(d[basic])
    design=gate_design(prep,d,basic,pb);alpha=blend_weight(d.y.to_numpy(),pb,pa)
    gates={}
    for name,weight in [('raw',1.),('blend',alpha)]:
        adjusted=pb+weight*(pa-pb);gain=(d.y.to_numpy()-pb)**2-(d.y.to_numpy()-adjusted)**2
        confidence=np.abs(adjusted-.5)-np.abs(pb-.5)
        gates[name]={
            'ridge_gain':Ridge(alpha=10).fit(design,gain),
            'nonlinear_gain':ExtraTreesRegressor(n_estimators=80,max_depth=3,min_samples_leaf=6,max_features=1.,random_state=seed,n_jobs=1).fit(design,gain),
            'confidence':Ridge(alpha=10).fit(design,confidence)}
    return {'mode':mode,'basic':basic,'extra':extra,'training_ids':d.id.tolist(),'seed':seed,'basic_model':basic_model,'advanced_model':advanced_model,'preprocessor':prep,'alpha':alpha,'gates':gates,'nested_partitions':nested,'oof_basic':pb,'oof_advanced':pa,'oof_y':d.y.to_numpy()}

def predict(bundle,d,blending):
    assert set(d.id).isdisjoint(bundle['training_ids'])
    pb=probability(bundle['basic_model'],d);pa=probability(bundle['advanced_model'],d)
    weight=bundle['alpha'] if blending=='blend' else 1.
    out=d[['id','y']].copy().reset_index(drop=True);out['basic']=pb;out['advanced']=pb+weight*(pa-pb)
    x=gate_design(bundle['preprocessor'],d,bundle['basic'],pb)
    for name,gate in bundle['gates'][blending].items():out[name]=gate.predict(x)
    out['uncertainty']=-np.abs(pb-.5)
    assert np.isfinite(out.drop(columns='id')).all().all()
    return out

def evaluate(d,context):
    rows=[]
    for budget in PLAN['budgets']:
        for policy in PLAN['policies']:
            scores=[]
            for draw in range(PLAN['random_draws'] if policy=='random' else 1):
                if policy=='basic':ref=np.zeros(len(d),bool)
                elif policy=='full':ref=np.ones(len(d),bool)
                else:
                    if policy=='oracle':score=(d.y-d.basic)**2-(d.y-d.advanced)**2
                    elif policy=='random':score=np.random.default_rng(SEED+draw).uniform(size=len(d))
                    else:score=d[policy]
                    ref=prior.original.refer_mask(score,budget)
                prob=np.where(ref,d.advanced,d.basic);scores.append(prior.original.metrics(d.y,prob,ref))
            rows.append({**context,'policy':policy,'budget':budget,**{key:float(np.mean([v[key] for v in scores])) for key in scores[0]}})
    return rows

def main():
    out=ROOT/'results';out.mkdir(exist_ok=True);(ROOT/'models').mkdir(exist_ok=True)
    sentinel=out/'experiment_started.json'
    if sentinel.exists():raise RuntimeError('Fixed matrix already started. Inspect outputs; do not rerun to optimize reported scores.')
    digest=hashlib.sha256((ROOT/'protocol.json').read_bytes()).hexdigest()
    assert digest==(ROOT/'protocol.sha256').read_text().split()[0]
    sentinel.write_text(json.dumps({'started_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'protocol_sha256':digest,'experiment_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'scope':'Original development participants only; exploratory'},indent=2))
    rows=[];selection=[];partitions=[];audit=[]
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter('always',RuntimeWarning)
        warnings.simplefilter('error',ConvergenceWarning)
        for cohort in PLAN['cohorts']:
            d,basic,extra,forbidden=load_development(cohort)
            modes=['legacy_fixed','nested_original']+(['nested_rich'] if cohort=='eeg_ad_ftd' else [])
            audit.append({'cohort':cohort,'development_n':len(d),'positives':int(d.y.sum()),'excluded_exposed_holdout_n':len(forbidden),'holdout_used':False})
            for repeat in range(PLAN['outer_repeats']):
                collected={}
                folds=StratifiedKFold(PLAN['outer_folds'],shuffle=True,random_state=SEED+repeat)
                for fold,(tr,va) in enumerate(folds.split(d,d.y)):
                    training=d.iloc[tr];validation=d.iloc[va];seed=SEED+10*repeat+fold
                    partitions.append({'cohort':cohort,'repeat':repeat,'fold':fold,'training_ids':training.id.tolist(),'validation_ids':validation.id.tolist()})
                    for mode in modes:
                        bundle=fit_bundle(training,basic,extra,mode,seed)
                        selection.append({'cohort':cohort,'repeat':repeat,'fold':fold,'mode':mode,'alpha':bundle['alpha'],'basic_spec':str(bundle['basic_model']['spec']),'advanced_spec':str(bundle['advanced_model']['spec'])})
                        for blending in (['raw'] if mode=='legacy_fixed' else ['raw','blend']):
                            variant=mode if mode=='legacy_fixed' else mode+'_'+blending
                            pred=predict(bundle,validation,blending);pred['fold']=fold
                            collected.setdefault(variant,[]).append(pred)
                        print(f'{cohort} repeat={repeat+1} fold={fold+1} {mode}: alpha={bundle["alpha"]:.3f}',flush=True)
                for variant,frames in collected.items():
                    pred=pd.concat(frames).sort_values('id').reset_index(drop=True)
                    assert pred.id.is_unique and set(pred.id)==set(d.id) and set(pred.id).isdisjoint(forbidden)
                    pred.to_csv(out/f'{cohort}_{variant}_repeat{repeat}_predictions.csv',index=False)
                    rows.extend(evaluate(pred,{'cohort':cohort,'repeat':repeat,'variant':variant,'phase':'exploratory_development'}))
                pd.DataFrame(rows).to_csv(out/'outer_metrics.csv',index=False)
                pd.DataFrame(selection).to_csv(out/'selected_models.csv',index=False)
            for mode in modes:
                final=fit_bundle(d,basic,extra,mode,SEED)
                assert set(final['training_ids']).isdisjoint(forbidden)
                joblib.dump(final,ROOT/'models'/f'{cohort}_{mode}.joblib')
                print(f'Saved development-fitted bundle {cohort} {mode}',flush=True)
        counts=collections.Counter(str(w.message) for w in captured)
    (out/'runtime_warnings.json').write_text(json.dumps(dict(counts),indent=2))
    (out/'partitions_patient.json').write_text(json.dumps(partitions,indent=2))
    (out/'data_audit.json').write_text(json.dumps(audit,indent=2))
    assert len(rows)==2352 and len(selection)==108
    (out/'completed.json').write_text(json.dumps({'aggregate_rows':len(rows),'outer_pipeline_fits':len(selection),'final_bundles':9,'heldout_evaluations':0,'protocol_sha256':digest,'completed_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())},indent=2))
    print('Completed fixed development experiment matrix; no holdout evaluation',flush=True)

if __name__=='__main__':main()
