"""Operating-point selection and participant-level metrics."""
import numpy as np
from sklearn.metrics import roc_auc_score,brier_score_loss,average_precision_score

def sensitivity_threshold(y,p,target=.9):
    y=np.asarray(y);p=np.asarray(p,float)
    assert set(np.unique(y))=={0,1} and np.isfinite(p).all() and np.all((p>=0)&(p<=1))
    candidates=np.unique(np.r_[0.,.5,p[(y==1)&(p<=.5)]])
    return float(max(t for t in candidates if np.mean(p[y==1]>=t)>=target-1e-12))

def wilson(k,n):
    z=1.959963984540054;phat=k/n;den=1+z*z/n
    mid=(phat+z*z/(2*n))/den;half=z*np.sqrt(phat*(1-phat)/n+z*z/(4*n*n))/den
    return float(mid-half),float(mid+half)

def metrics(y,p,threshold):
    y=np.asarray(y);p=np.asarray(p,float);positive=p>=threshold
    tp=int(np.sum(positive&(y==1)));fn=int(np.sum(~positive&(y==1)));tn=int(np.sum(~positive&(y==0)));fp=int(np.sum(positive&(y==0)))
    sl,sh=wilson(tp,tp+fn);cl,ch=wilson(tn,tn+fp)
    return {'n':len(y),'ad_n':int(y.sum()),'threshold':float(threshold),'true_positives':tp,'false_negatives':fn,'true_negatives':tn,'false_positives':fp,'sensitivity':tp/(tp+fn),'specificity':tn/(tn+fp),'sensitivity_low':sl,'sensitivity_high':sh,'specificity_low':cl,'specificity_high':ch,'auroc':float(roc_auc_score(y,p)),'brier':float(brier_score_loss(y,p)),'average_precision':float(average_precision_score(y,p))}
