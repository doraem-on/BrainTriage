"""Measured-data extension. No tuning on any held-out outcome metrics."""
from pathlib import Path
import sys, os, json, hashlib, argparse, time, warnings
import numpy as np
import pandas as pd
import joblib
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, SplineTransformer
from sklearn.pipeline import make_pipeline
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression, Ridge, BayesianRidge
from sklearn.covariance import LedoitWolf
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import StratifiedKFold, train_test_split
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parent/'src'))
import study as original
PLAN=json.loads((ROOT/'protocol.json').read_text());SEED=PLAN['seed']
warnings.filterwarnings('ignore',message='Unknown solver options: iprint')

def load(name):
    if name=='eeg_ad_ftd':
        d=pd.read_csv(ROOT/'data_raw/eeg_features.csv').sort_values('id').reset_index(drop=True)
        basic=['age','male','mmse'];extra=[c for c in d if c.startswith('eeg_')]
        tr,te=train_test_split(np.arange(len(d)),test_size=PLAN['new_holdout_fraction'],stratify=d.y,random_state=SEED)
        tr,te=np.sort(tr),np.sort(te)
    else:
        d,basic,extra,_=original.load_cohort(name);tr,te=original.split_cohort(d)
    assert d.id.is_unique and set(d.iloc[tr].id).isdisjoint(d.iloc[te].id)
    assert not d[extra].isna().any().any()
    return d,basic,extra,tr,te

def preprocess():return make_pipeline(SimpleImputer(strategy='median',add_indicator=True),StandardScaler())

def classifier(columns,config,seed):
    if config=='spline_logistic':
        continuous=[c for c in columns if c!='male']
        smooth=make_pipeline(SimpleImputer(strategy='median'),SplineTransformer(n_knots=3,degree=2,include_bias=False,extrapolation='linear'))
        transform=ColumnTransformer([('smooth',smooth,continuous),('binary',SimpleImputer(strategy='most_frequent'),['male'])])
        pipe=make_pipeline(transform,StandardScaler(),LogisticRegression(C=.5,max_iter=2000,random_state=seed))
    else:
        pipe=make_pipeline(SimpleImputer(strategy='median',add_indicator=True),StandardScaler(),LogisticRegression(C=1,max_iter=2000,random_state=seed))
    if config=='logistic_uncalibrated':return pipe
    return CalibratedClassifierCV(pipe,method='sigmoid',cv=StratifiedKFold(PLAN['calibration_folds'],shuffle=True,random_state=seed),ensemble=False)

def weighted_loss(y,p,w):
    decision=np.asarray(p)>=1/(1+w);y=np.asarray(y)
    return w*((y==1)&~decision)+((y==0)&decision)

def entropy(p):
    p=np.clip(p,1e-12,1-1e-12)
    return -p*np.log(p)-(1-p)*np.log1p(-p)

def fit(d,basic,extra,config='logistic',seed=SEED):
    basic=[c for c in basic if not(config=='logistic_no_mmse' and c=='mmse')]
    d=d.sort_values('id');y=d.y.to_numpy();oof_b=np.zeros(len(d));oof_a=np.zeros(len(d))
    cv=StratifiedKFold(PLAN['gate_folds'],shuffle=True,random_state=seed)
    for tr,va in cv.split(d,y):
        for cols,output in [(basic,oof_b),(basic+extra,oof_a)]:
            m=classifier(cols,config,seed).fit(d.iloc[tr][cols],y[tr])
            output[va]=m.predict_proba(d.iloc[va][cols])[:,1]
    prep=preprocess().fit(d[basic]);x=prep.transform(d[basic]);xb=np.column_stack([np.ones(len(x)),x])
    gain=(y-oof_b)**2-(y-oof_a)**2
    confidence=np.abs(oof_a-.5)-np.abs(oof_b-.5)
    bayes=BayesianRidge(fit_intercept=False,max_iter=500).fit(xb,gain)
    ridge=Ridge(alpha=10).fit(x,gain);conf=Ridge(alpha=10).fit(x,confidence)
    costs={w:Ridge(alpha=10).fit(x,weighted_loss(y,oof_b,w)-weighted_loss(y,oof_a,w)) for w in PLAN['false_negative_weights']}
    extra_scale=StandardScaler().fit(d[extra]);z=extra_scale.transform(d[extra])
    conditional=Ridge(alpha=10).fit(x,z)
    residual=z-conditional.predict(x);cov=LedoitWolf().fit(residual).covariance_+np.eye(len(extra))*1e-8
    mb=classifier(basic,config,seed).fit(d[basic],y)
    ma=classifier(basic+extra,config,seed).fit(d[basic+extra],y)
    return {'basic':basic,'extra':extra,'config':config,'training_ids':d.id.tolist(),'seed':seed,
        'preprocessor':prep,'bayes':bayes,'ridge':ridge,'confidence':conf,'cost_gates':costs,
        'extra_scale':extra_scale,'conditional':conditional,'covariance':cov,'basic_model':mb,'advanced_model':ma,
        'oof_basic':oof_b,'oof_advanced':oof_a,'oof_y':y,'basic_sd':d[basic].std().fillna(0).to_dict()}

def information(bundle,d):
    basic,extra=bundle['basic'],bundle['extra'];x=bundle['preprocessor'].transform(d[basic])
    mu=bundle['conditional'].predict(x)
    # Common random numbers keep rankings deterministic and independent of outcomes.
    eps=np.random.default_rng(SEED).multivariate_normal(np.zeros(len(extra)),bundle['covariance'],size=32)
    z=mu[:,None,:]+eps[None,:,:]
    drawn=bundle['extra_scale'].inverse_transform(z.reshape(-1,len(extra)))
    frame=d[basic].iloc[np.repeat(np.arange(len(d)),32)].reset_index(drop=True)
    frame[extra]=drawn
    prob=bundle['advanced_model'].predict_proba(frame[basic+extra])[:,1].reshape(len(d),32)
    info=entropy(prob.mean(axis=1))-entropy(prob).mean(axis=1)
    assert np.all(info>=-1e-10)
    return np.maximum(info,0)

def predict(bundle,d,with_information=True):
    assert set(d.id).isdisjoint(bundle['training_ids'])
    basic,extra=bundle['basic'],bundle['extra'];x=bundle['preprocessor'].transform(d[basic]);xb=np.column_stack([np.ones(len(x)),x])
    out=d[['id','y','age','male']].copy().reset_index(drop=True)
    out['basic']=bundle['basic_model'].predict_proba(d[basic])[:,1]
    out['advanced']=bundle['advanced_model'].predict_proba(d[basic+extra])[:,1]
    out['risk']=out.basic;out['uncertainty']=-np.abs(out.basic-.5)
    out['ridge_gain']=bundle['ridge'].predict(x);out['confidence']=bundle['confidence'].predict(x)
    out['bayes_mean']=bundle['bayes'].predict(xb)
    # Variance of the conditional posterior mean, not predictive observation variance.
    out['gain_sd']=np.sqrt(np.maximum(np.einsum('ij,jk,ik->i',xb,bundle['bayes'].sigma_,xb,optimize=False),0))
    for k in [.5,1,2]:out[f'bayes_lcb_{k:g}']=out.bayes_mean-k*out.gain_sd
    out['information']=information(bundle,d) if with_information else 0.
    for w,gate in bundle['cost_gates'].items():out[f'cost_gain_{w}']=gate.predict(x)
    assert np.isfinite(out.drop(columns=['id','age'])).all().all()
    return out

def policy_predictions(d,policy,budget):
    if policy=='basic':return d.basic.to_numpy(),np.zeros(len(d),bool)
    if policy=='advanced':return d.advanced.to_numpy(),np.ones(len(d),bool)
    if policy=='oracle':scores=(d.y-d.basic)**2-(d.y-d.advanced)**2
    else:scores=d[policy]
    ref=original.refer_mask(scores,budget)
    return np.where(ref,d.advanced,d.basic),ref

def metrics(d,p,ref):
    m=original.metrics(d.y,p,ref);y=d.y.to_numpy();b=d.basic.to_numpy()
    m['corrected_errors']=int(((b>=.5)!=y)[(p>=.5)==y].sum())
    m['new_errors']=int(((b>=.5)==y)[(p>=.5)!=y].sum())
    return m

def evaluate(d,context,budgets=None):
    rows=[]
    for q in (PLAN['budgets'] if budgets is None else budgets):
        for policy in PLAN['policies']+['oracle']:
            values=[]
            for rep in range(PLAN['random_draws'] if policy=='random' else 1):
                if policy=='random':
                    ref=original.refer_mask(np.random.default_rng(SEED+rep).uniform(size=len(d)),q)
                    p=np.where(ref,d.advanced,d.basic)
                else:p,ref=policy_predictions(d,policy,q)
                values.append(metrics(d,p,ref))
            rows.append({**context,'policy':policy,'budget':q,**{k:float(np.mean([v[k] for v in values])) for k in values[0]}})
    return rows

def cost_scenarios(d,context):
    rows=[];y=d.y.to_numpy()
    for w in PLAN['false_negative_weights']:
        for cost in PLAN['test_costs']:
            for policy in ['basic','advanced','uncertainty','bayes_mean','bayes_lcb_1','cost_gate']:
                if policy=='cost_gate':
                    ref=d[f'cost_gain_{w}'].to_numpy()>cost;p=np.where(ref,d.advanced,d.basic)
                else:p,ref=policy_predictions(d,policy,.3)
                loss=weighted_loss(y,p,w)
                rows.append({**context,'policy':policy,'fn_weight':w,'test_cost':cost,'referrals':int(ref.sum()),
                    'referral_fraction':float(ref.mean()),'weighted_error':float(loss.mean()),
                    'objective':float(loss.mean()+cost*ref.mean()),'n':len(d)})
    return rows

def perturb(d,bundle,kind,level,seed):
    d=d.copy();rng=np.random.default_rng(seed)
    cols=[c for c in bundle['basic'] if c!='male']
    for col in cols:
        if kind=='missing':d.loc[rng.uniform(size=len(d))<level,col]=np.nan
        else:d[col]=d[col]+rng.normal(size=len(d))*level*bundle['basic_sd'][col]
    return d

def develop(name,config):
    d,basic,extra,tr,te=load(name);dev=d.iloc[tr].reset_index(drop=True)
    predictions=[];rows=[];stress_rows=[];learning_rows=[]
    for repeat in range(PLAN['development_repeats']):
        cv=StratifiedKFold(PLAN['development_folds'],shuffle=True,random_state=SEED+repeat)
        full=[];learning={f:[] for f in [.5,.75]};stress={}
        for fold,(train,validation) in enumerate(cv.split(dev,dev.y)):
            seed=SEED+repeat*10+fold;train_d=dev.iloc[train];eval_d=dev.iloc[validation]
            bundle=fit(train_d,basic,extra,config,seed);pred=predict(bundle,eval_d);pred['fold']=fold;full.append(pred)
            if config=='logistic':
                for fraction in [.5,.75]:
                    subset,_=train_test_split(np.arange(len(train_d)),train_size=fraction,stratify=train_d.y,random_state=seed)
                    small=fit(train_d.iloc[subset],basic,extra,config,seed)
                    learning[fraction].append(predict(small,eval_d))
                for kind,levels in [('missing',[.1,.3]),('noise',[.1,.3])]:
                    for level in levels:
                        changed=perturb(eval_d,bundle,kind,level,seed)
                        stress.setdefault((kind,level),[]).append(predict(bundle,changed))
            print(f'develop {name} {config} repeat={repeat+1} fold={fold+1}',flush=True)
        pr=pd.concat(full).sort_values('id').reset_index(drop=True)
        pr['repeat']=repeat;pr['cohort']=name;pr['config']=config;predictions.append(pr)
        context={'cohort':name,'config':config,'repeat':repeat,'phase':'development'}
        rows.extend(evaluate(pr,context))
        if config=='logistic':
            learning[1.0]=[pr]
            for fraction,frames in learning.items():
                q=pd.concat(frames).sort_values('id').reset_index(drop=True)
                learning_rows.extend(evaluate(q,{**context,'fraction':fraction},budgets=[.3]))
            stress[('clean',0)]=[pr]
            for (kind,level),frames in stress.items():
                q=pd.concat(frames).sort_values('id').reset_index(drop=True)
                stress_rows.extend(evaluate(q,{**context,'perturbation':kind,'level':level},budgets=[.3]))
    out=ROOT/'results'
    pd.concat(predictions).to_csv(out/f'develop_{name}_{config}_predictions.csv',index=False)
    pd.DataFrame(rows).to_csv(out/f'develop_{name}_{config}_metrics.csv',index=False)
    if learning_rows:pd.DataFrame(learning_rows).to_csv(out/f'learning_{name}.csv',index=False)
    if stress_rows:pd.DataFrame(stress_rows).to_csv(out/f'stress_{name}.csv',index=False)

def holdout(name,config):
    out=ROOT/'results';sentinel=out/f'holdout_opened_{name}_{config}.json'
    if sentinel.exists():raise RuntimeError('This holdout configuration has already been evaluated. Do not retune on it.')
    d,basic,extra,tr,te=load(name);bundle=fit(d.iloc[tr],basic,extra,config)
    joblib.dump(bundle,ROOT/'models'/f'{name}_{config}.joblib')
    pred=predict(bundle,d.iloc[te]).sort_values('id').reset_index(drop=True)
    context={'cohort':name,'config':config,'phase':'new_task_holdout' if name=='eeg_ad_ftd' else 'exposed_holdout_exploratory','repeat':0}
    for key,value in context.items():pred[key]=value
    pred.to_csv(out/f'holdout_{name}_{config}_predictions.csv',index=False)
    pd.DataFrame(evaluate(pred,context)).to_csv(out/f'holdout_{name}_{config}_metrics.csv',index=False)
    pd.DataFrame(cost_scenarios(pred,context)).to_csv(out/f'cost_{name}_{config}.csv',index=False)
    sentinel.write_text(json.dumps({'timestamp_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
        'protocol_sha256':hashlib.sha256((ROOT/'protocol.json').read_bytes()).hexdigest(),
        'training_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),**context},indent=2))
    print(f'Final saved {name} {config}: development={len(tr)}, holdout={len(te)}',flush=True)

def stability(name):
    d,basic,extra,tr,_=load(name);dev=d.iloc[tr].reset_index(drop=True)
    fit_ids,ev_ids=train_test_split(np.arange(len(dev)),test_size=.25,stratify=dev.y,random_state=SEED)
    train=dev.iloc[fit_ids];validation=dev.iloc[ev_ids].sort_values('id')
    masks={p:[] for p in ['uncertainty','ridge_gain','bayes_mean','bayes_lcb_1']}
    for run in range(PLAN['stability_refits']):
        indices,_=train_test_split(np.arange(len(train)),train_size=.8,stratify=train.y,random_state=SEED+run)
        bundle=fit(train.iloc[indices],basic,extra,'logistic',SEED+run)
        pred=predict(bundle,validation,with_information=False)
        for policy in masks:masks[policy].append(original.refer_mask(pred[policy],.3))
        print(f'stability {name} refit={run+1}',flush=True)
    pairs=[];inclusion=[]
    for policy,values in masks.items():
        arr=np.array(values)
        for i in range(len(arr)):
            for j in range(i):
                union=(arr[i]|arr[j]).sum();score=float((arr[i]&arr[j]).sum()/union) if union else 1.
                pairs.append({'cohort':name,'policy':policy,'run_a':i,'run_b':j,'jaccard':score})
        for pid,prob in zip(validation.id,arr.mean(axis=0)):inclusion.append({'cohort':name,'policy':policy,'id':pid,'referral_frequency':prob})
    pd.DataFrame(pairs).to_csv(ROOT/'results'/f'stability_{name}.csv',index=False)
    pd.DataFrame(inclusion).to_csv(ROOT/'results'/f'inclusion_{name}_patient.csv',index=False)

def audit():
    rows=[];manifest=[]
    for name in PLAN['cohorts']:
        d,b,a,tr,te=load(name)
        rows.append({'cohort':name,'n':len(d),'positive_n':int(d.y.sum()),'development_n':len(tr),'holdout_n':len(te),
            'holdout_positive_n':int(d.iloc[te].y.sum()),'basic':b,'advanced':a})
        for partition,indices in [('development',tr),('holdout',te)]:
            manifest.extend({'cohort':name,'id':pid,'partition':partition} for pid in d.iloc[indices].id)
    (ROOT/'results/data_audit.json').write_text(json.dumps(rows,indent=2))
    pd.DataFrame(manifest).to_csv(ROOT/'results/split_manifest_patient.csv',index=False)
    print(json.dumps(rows,indent=2))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=['audit','develop','holdout','stability'],required=True)
    parser.add_argument('--cohort',choices=PLAN['cohorts']);parser.add_argument('--config',choices=PLAN['configurations'])
    args=parser.parse_args()
    for folder in ['results','models','figures']:(ROOT/folder).mkdir(exist_ok=True,parents=True)
    assert hashlib.sha256((ROOT/'protocol.json').read_bytes()).hexdigest()==(ROOT/'protocol.sha256').read_text().split()[0]
    if args.mode=='audit':audit();return
    for name in ([args.cohort] if args.cohort else PLAN['cohorts']):
        if args.mode=='stability':stability(name);continue
        for config in ([args.config] if args.config else PLAN['configurations']):
            if args.mode=='develop':develop(name,config)
            else:holdout(name,config)

if __name__=='__main__':main()
