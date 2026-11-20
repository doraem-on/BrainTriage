"""Summaries and conditional uncertainty from saved extension predictions."""
import json
import numpy as np
import pandas as pd
from research import ROOT, PLAN, SEED, policy_predictions, metrics

def bootstrap_weights(y):
    rng=np.random.default_rng(SEED);weights=np.zeros((PLAN['bootstrap_replicates'],len(y)),int)
    for label in [0,1]:
        idx=np.flatnonzero(y==label)
        for k,draw in enumerate(rng.choice(idx,size=(len(weights),len(idx)),replace=True)):
            weights[k]+=np.bincount(draw,minlength=len(y))
    return weights

def interval(values):return np.quantile(values,[.025,.975]).tolist()

def main():
    out=ROOT/'results'
    for phase in ['develop','holdout']:
        files=[out/f'{phase}_{c}_{m}_metrics.csv' for c in PLAN['cohorts'] for m in PLAN['configurations']]
        frames=[pd.read_csv(f) for f in files];pd.concat(frames,ignore_index=True).to_csv(out/f'{phase}_all_metrics.csv',index=False)
    for name in ['learning','stress','stability']:
        pd.concat([pd.read_csv(out/f'{name}_{c}.csv') for c in PLAN['cohorts']],ignore_index=True).to_csv(out/f'{name}_all.csv',index=False)
    pd.concat([pd.read_csv(out/f'cost_{c}_{m}.csv') for c in PLAN['cohorts'] for m in PLAN['configurations']],ignore_index=True).to_csv(out/'cost_all.csv',index=False)
    summary=[];contrasts=[];calibration=[];gain_bins=[];coef=[]
    for cohort in PLAN['cohorts']:
        for config in PLAN['configurations']:
            d=pd.read_csv(out/f'holdout_{cohort}_{config}_predictions.csv');y=d.y.to_numpy();w=bootstrap_weights(y)
            preds={}
            for policy in ['basic','advanced']+[p for p in PLAN['policies'] if p!='random']:
                p,ref=policy_predictions(d,policy,.3);preds[policy]=p;m=metrics(d,p,ref)
                low,high=interval(np.einsum('bi,i->b',w,(y-p)**2,optimize=False)/len(y))
                pos=y==1;neg=y==0
                pair=(p[pos,None]>p[None,neg]).astype(float)+.5*(p[pos,None]==p[None,neg])
                auclo,auchi=interval(np.einsum('bi,ij,bj->b',w[:,pos],pair,w[:,neg],optimize=False)/(pos.sum()*neg.sum()))
                summary.append({'cohort':cohort,'config':config,'policy':policy,**m,'brier_low':low,'brier_high':high,'auc_low':auclo,'auc_high':auchi})
                if config=='logistic' and policy in ['basic','advanced','bayes_mean','bayes_lcb_1']:
                    bin_index=np.minimum((p*5).astype(int),4)
                    for i,lo in enumerate([0,.2,.4,.6,.8]):
                        mask=bin_index==i
                        if mask.any():calibration.append({'cohort':cohort,'policy':policy,'bin_low':lo,'n':int(mask.sum()),'probability':float(p[mask].mean()),'observed':float(y[mask].mean())})
            for comparator in ['bayes_mean','ridge_gain','uncertainty','information','basic','advanced']:
                loss=(y-preds['bayes_lcb_1'])**2-(y-preds[comparator])**2
                low,high=interval(np.einsum('bi,i->b',w,loss,optimize=False)/len(y))
                contrasts.append({'cohort':cohort,'config':config,'contrast':'bayes_lcb_1 minus '+comparator,
                    'difference':float(loss.mean()),'low':low,'high':high,'status':'new_task_holdout' if cohort=='eeg_ad_ftd' else 'exposed_holdout_exploratory'})
            # Benefit reliability uses only cross-fitted development predictions.
            if config=='logistic':
                dev=pd.read_csv(out/f'develop_{cohort}_{config}_predictions.csv')
                for repeat,g in dev.groupby('repeat'):
                    g=g.sort_values('bayes_mean');gain=(g.y-g.basic)**2-(g.y-g.advanced)**2
                    for i,ix in enumerate(np.array_split(np.arange(len(g)),4)):
                        gain_bins.append({'cohort':cohort,'repeat':repeat,'quartile':i+1,'n':len(ix),
                            'predicted':float(g.bayes_mean.iloc[ix].mean()),'observed':float(gain.iloc[ix].mean())})
    for name,rows in [('holdout_summary',summary),('paired_contrasts',contrasts),('calibration',calibration),('gain_reliability',gain_bins)]:
        pd.DataFrame(rows).to_csv(out/f'{name}.csv',index=False)
    dev=pd.read_csv(out/'develop_all_metrics.csv')
    dev.groupby(['cohort','config','policy','budget'])[['brier','auroc','false_negatives','new_errors','referrals']].agg(['mean','std']).to_csv(out/'development_summary.csv')
    checks={'development_metric_rows':len(dev),'holdout_metric_rows':len(pd.read_csv(out/'holdout_all_metrics.csv')),
        'saved_final_bundles':len(list((ROOT/'models').glob('*.joblib')))}
    assert checks['development_metric_rows']==3696 and checks['holdout_metric_rows']==1232 and checks['saved_final_bundles']==16
    (out/'analysis_integrity.json').write_text(json.dumps(checks,indent=2))
    print(pd.DataFrame(summary).query("config=='logistic'")[['cohort','policy','brier','auroc','false_negatives','referrals']].round(4).to_string(index=False))
    print(pd.DataFrame(contrasts).query("config=='logistic' and contrast=='bayes_lcb_1 minus bayes_mean'").round(5).to_string(index=False))

if __name__=='__main__':main()
