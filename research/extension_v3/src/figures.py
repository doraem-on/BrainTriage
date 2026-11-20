"""Publication plots from aggregate data; ranges are descriptive, not confidence intervals."""
from pathlib import Path
import csv,sys
ROOT=Path(__file__).resolve().parents[1]
# Optional local plotting packages; ordinary installations use their environment.
local=ROOT.parent/'.plot_packages'
if local.exists():sys.path.insert(0,str(local))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
OUT=ROOT/'figures';OUT.mkdir(exist_ok=True)
with open(ROOT/'results/outer_metrics.csv') as f:rows=list(csv.DictReader(f))
with open(ROOT/'results/selected_models.csv') as f:selected=list(csv.DictReader(f))
C={'oasis2':'OASIS 2','oasis1':'OASIS 1','csf':'CSF','eeg_ad_ftd':'EEG AD vs FTD'}
plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':200,'pdf.fonttype':42})
def vals(c,v,p,q=.3):return np.array([float(r['brier']) for r in rows if r['cohort']==c and r['variant']==v and r['policy']==p and float(r['budget'])==q])
def chosen(c):return 'nested_rich_blend' if c=='eeg_ad_ftd' else 'nested_original_blend'
def save(fig,name):
    fig.savefig(OUT/(name+'.png'),bbox_inches='tight');fig.savefig(OUT/(name+'.pdf'),bbox_inches='tight');plt.close(fig)
fig,axes=plt.subplots(2,2,figsize=(8,5.7),layout='constrained')
labels=['Fixed uncertainty','Tuned basic','Tuned full','Tuned uncertainty','Tuned nonlinear gain']
for ax,c in zip(axes.flat,C):
    for j,(v,p) in enumerate([('legacy_fixed','uncertainty'),(chosen(c),'basic'),(chosen(c),'full'),(chosen(c),'uncertainty'),(chosen(c),'nonlinear_gain')]):
        a=vals(c,v,p);color='#ae422b' if j==4 else '#345e7e'
        ax.plot([a.min(),a.max()],[j,j],color=color,lw=1.3);ax.scatter(a,[j]*3,color=color,s=14,alpha=.5);ax.scatter(a.mean(),j,color=color,marker='D',s=30)
    ax.set(yticks=range(5),yticklabels=labels,title=C[c],xlabel='Brier score (lower is better)');ax.invert_yaxis();ax.grid(axis='x',alpha=.2);ax.xaxis.set_major_locator(MaxNLocator(4))
save(fig,'primary_comparison')
fig,axes=plt.subplots(2,2,figsize=(8,5.6),layout='constrained')
styles=[('uncertainty','Tuned uncertainty','#345e7e'),('nonlinear_gain','Tuned nonlinear gain','#ae422b'),('ridge_gain','Tuned ridge gain','#6a5b8e'),('random','Random mean','#777777'),('oracle','Retrospective oracle','#408f70')]
qs=[0,.1,.2,.3,.5,.75,1]
for ax,c in zip(axes.flat,C):
    for p,label,color in styles:ax.plot(qs,[vals(c,chosen(c),p,q).mean() for q in qs],label=label,color=color,marker='o',ms=3)
    ax.plot(qs,[vals(c,'legacy_fixed','uncertainty',q).mean() for q in qs],label='Fixed uncertainty',color='black',ls='--')
    ax.set(title=C[c],xlabel='Nominal acquisition fraction',ylabel='Mean Brier score');ax.axvline(.3,color='gray',alpha=.3);ax.grid(alpha=.15)
handles,labels=axes[0,0].get_legend_handles_labels();fig.legend(handles,labels,loc='outside lower center',ncol=3,fontsize=8)
save(fig,'capacity_curves')
fig,axes=plt.subplots(1,2,figsize=(8,3.7),layout='constrained')
variants=['legacy_fixed','nested_original_raw','nested_original_blend','nested_rich_raw','nested_rich_blend'];labels=['Fixed original','Tuned original','Tuned original + blend','Tuned rich','Tuned rich + blend']
for ax,policy,title in zip(axes,['full','nonlinear_gain'],['Full acquisition','Nonlinear gain, 30% capacity']):
    for j,v in enumerate(variants):
        a=vals('eeg_ad_ftd',v,policy);ax.plot([a.min(),a.max()],[j,j],color='#345e7e');ax.scatter(a,[j]*3,s=20,color='#345e7e',alpha=.6);ax.scatter(a.mean(),j,marker='D',s=30,color='#ae422b')
    ax.set(yticks=range(5),yticklabels=labels,title=title,xlabel='Brier score');ax.invert_yaxis();ax.grid(axis='x',alpha=.2)
save(fig,'eeg_ablation')
fig,ax=plt.subplots(figsize=(7.5,3.4),layout='constrained')
for j,(c,mode,label) in enumerate([(c,'nested_original',C[c]) for c in C]+[('eeg_ad_ftd','nested_rich','EEG rich')]):
    a=[float(r['alpha']) for r in selected if r['cohort']==c and r['mode']==mode]
    ax.scatter(a,np.full(len(a),j)+np.linspace(-.12,.12,len(a)),alpha=.7,s=24,color='#345e7e')
ax.set(yticks=range(5),yticklabels=list(C.values())+['EEG rich'],xlabel='Training-fitted blend weight α (0 = basic; 1 = advanced)',xlim=(-.04,1.04));ax.invert_yaxis();ax.grid(axis='x',alpha=.2)
save(fig,'blend_weights')
print('Wrote four figures in PNG and vector PDF formats.')
