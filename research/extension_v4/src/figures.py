"""Publication figures from recorded aggregate outputs; no model fitting."""
from pathlib import Path
import sys,csv
ROOT=Path(__file__).resolve().parents[1]
if (ROOT.parent/'.plot_packages').exists():sys.path.insert(0,str(ROOT.parent/'.plot_packages'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
OUT=ROOT/'figures';OUT.mkdir(exist_ok=True)
def read(name):
    with open(ROOT/'results'/name) as f:return list(csv.DictReader(f))
def save(fig,name):
    fig.savefig(OUT/f'{name}.png',dpi=220,bbox_inches='tight');fig.savefig(OUT/f'{name}.pdf',bbox_inches='tight');plt.close(fig)
d=read('external_metrics.csv');colors={'spectral':'#2166ac','covariance':'#b35806'}
fig,axes=plt.subplots(2,2,figsize=(8,6),layout='constrained')
for ax,r in zip(axes.flat,d):
    matrix=np.array([[int(r['true_negatives']),int(r['false_positives'])],[int(r['false_negatives']),int(r['true_positives'])]])
    ax.imshow(matrix,cmap='Blues',vmin=0,vmax=12)
    for (i,j),v in np.ndenumerate(matrix):ax.text(j,i,str(v),ha='center',va='center',color='white' if v>7 else 'black',fontsize=16)
    ax.set_xticks([0,1],['Predicted HC','Predicted AD']);ax.set_yticks([0,1],['Actual HC','Actual AD'])
    ax.set_title(f"{r['model'].capitalize()} | t = {float(r['threshold']):.3f}")
save(fig,'external_confusion')
fig,axes=plt.subplots(1,2,figsize=(8,3.5),layout='constrained')
for ax,metric in zip(axes,['sensitivity','specificity']):
    for i,r in enumerate(d):
        v=float(r[metric]);lo=float(r[metric+'_low']);hi=float(r[metric+'_high'])
        ax.errorbar(v,3-i,xerr=[[v-lo],[hi-v]],fmt='o' if r['operating']=='default' else 's',color=colors[r['model']],capsize=3)
    ax.set_yticks(range(4),['Covariance source t','Covariance t = 0.5','Spectral source t','Spectral t = 0.5']);ax.set_xlim(0,1.04);ax.set_xticks([0,.25,.5,.75,1]);ax.set_xlabel(metric.capitalize());ax.grid(axis='x',alpha=.2)
axes[1].set_yticklabels([])
save(fig,'external_intervals')
fig,ax=plt.subplots(figsize=(5.4,4.4),layout='constrained')
roc=read('external_roc.csv')
for model in ['spectral','covariance']:
    rows=[r for r in roc if r['model']==model];ax.step([float(r['false_positive_rate']) for r in rows],[float(r['true_positive_rate']) for r in rows],where='post',color=colors[model],label=f'{model.capitalize()} AUROC 0.864')
    r=next(r for r in d if r['model']==model and r['operating']=='sensitivity90');ax.scatter(1-float(r['specificity']),float(r['sensitivity']),color=colors[model],marker='s',s=65)
ax.plot([0,1],[0,1],ls='--',color='gray',lw=1);ax.set(xlim=(-.02,1.02),ylim=(-.02,1.04),xlabel='False positive rate',ylabel='Sensitivity');ax.legend(loc='lower right',fontsize=9)
save(fig,'external_roc')
rows=read('sensitivity_metrics.csv');policies=['basic','full','uncertainty','ridge_gain']
fig,axes=plt.subplots(1,2,figsize=(8,3.8),layout='constrained')
for ax,metric,title in zip(axes,['false_negatives','false_positives'],['Missed AD cases out of 25','False positives out of 16 FTD']):
    for i,policy in enumerate(policies):
        for j,op in enumerate(['default','sensitivity90']):
            vals=[float(r[metric]) for r in rows if r['policy']==policy and r['operating']==op]
            x=i+(j-.5)*.25;ax.scatter(x+np.array([-.025,0,.025]),vals,color=['#2166ac','#b35806'][j],s=22,alpha=.75,label=['Threshold 0.5','Source threshold'][j] if i==0 else None)
            ax.scatter(x,np.mean(vals),marker='_',s=260,color=['#2166ac','#b35806'][j])
    ax.set_xticks(range(4),['Basic','Full EEG','Uncertainty','Ridge gain'],rotation=15);ax.set_title(title);ax.set_ylim(0,10);ax.set_yticks(range(0,11,2));ax.grid(axis='y',alpha=.2)
axes[0].legend(fontsize=8,loc='upper left')
save(fig,'source_missed_cases')
print('Wrote four figures in PNG and vector PDF')
