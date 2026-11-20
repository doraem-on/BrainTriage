"""Research figures drawn from recorded evaluation outputs, with honest intervals."""
from pathlib import Path
import sys,os,csv
ROOT=Path(__file__).resolve().parents[2]/'extension_v2'
PAPER=Path(__file__).resolve().parents[1]
FIGURES=PAPER/'figures'
sys.path.insert(0,str(ROOT.parent/'.plot_packages'))
os.environ.setdefault('MPLCONFIGDIR',str(ROOT.parent/'.mplconfig'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from cycler import cycler
plt.rcParams['axes.prop_cycle']=cycler(color=['black'])
from matplotlib.colors import TwoSlopeNorm, LinearSegmentedColormap
from matplotlib.ticker import MaxNLocator
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.titlesize':11,'axes.labelsize':10,
 'axes.spines.top':False,'axes.spines.right':False,'legend.fontsize':9})
NAMES={'oasis2':'OASIS 2','oasis1':'OASIS 1','csf':'CSF cohort','eeg_ad_ftd':'EEG AD versus FTD'}
COLORS={'uncertainty':'#0072B2','confidence':'#E69F00','ridge_gain':'#CC79A7','bayes_mean':'#009E73','bayes_lcb_1':'#D55E00','information':'#7B61A8','oracle':'#777777'}
LABELS={'uncertainty':'Uncertainty','confidence':'Confidence gain','ridge_gain':'Ridge gain','bayes_mean':'Bayesian mean','bayes_lcb_1':'Uncertainty-adjusted benefit','information':'Information gain','oracle':'Outcome-informed oracle'}
LINESTYLE=dict(zip(['uncertainty','confidence','ridge_gain','bayes_mean','bayes_lcb_1','information','oracle'],['-','--','-.',':',(0,(5,1)),(0,(3,1,1,1)),(0,(1,2))]))
MARKER=dict(zip(['uncertainty','confidence','ridge_gain','bayes_mean','bayes_lcb_1','information','oracle'],['o','s','D','^','v','x','+']))
CONFIGS={'logistic':'Logistic','spline_logistic':'Additive spline','logistic_uncalibrated':'No calibration','logistic_no_mmse':'No MMSE'}

def read(name):
 with open(ROOT/'results'/name) as f:return list(csv.DictReader(f))
def select(rows,**kw):return [r for r in rows if all(r[k]==str(v) for k,v in kw.items())]
def save(fig,name):
 (FIGURES).mkdir(exist_ok=True)
 fig.savefig(FIGURES/f'a_{name}.png',dpi=220,bbox_inches='tight');fig.savefig(FIGURES/f'a_{name}.pdf',bbox_inches='tight');plt.close(fig)
def grid():return plt.subplots(2,2,figsize=(9.2,6.3))
def caption_title(ax,c):ax.set_title(NAMES[c]+(' | original EEG holdout' if c=='eeg_ad_ftd' else ' | exposed holdout'))
def legend(fig,ax,ncol=3):
 handles,labels=ax.get_legend_handles_labels();fig.legend(handles,labels,loc='lower center',ncol=ncol,frameon=False,bbox_to_anchor=(.5,-.01))

rows=read('holdout_all_metrics.csv')
for metric,ylabel,name in [('brier','Brier score (lower is better)','capacity_brier'),('false_negatives','Missed positives at 0.5','capacity_missed')]:
 fig,axes=grid()
 for ax,c in zip(axes.flat,NAMES):
  for policy in ['uncertainty','confidence','bayes_mean','bayes_lcb_1','information','oracle']:
   rr=sorted(select(rows,cohort=c,config='logistic',policy=policy),key=lambda r:float(r['budget']))
   ax.plot([100*float(r['referral_fraction']) for r in rr],[float(r[metric]) for r in rr],marker=MARKER[policy],markersize=3,lw=1.4,
    ls=LINESTYLE[policy],color=COLORS[policy],label=LABELS[policy])
  caption_title(ax,c);ax.set_xlabel('Advanced panels acquired (%)');ax.set_ylabel(ylabel);ax.grid(alpha=.15)
  if metric=='false_negatives':
   ax.set_ylim(0,max(float(r[metric]) for r in select(rows,cohort=c,config='logistic'))+.5)
   ax.yaxis.set_major_locator(MaxNLocator(integer=True))
 legend(fig,axes.flat[0]);fig.tight_layout(rect=(0,.09,1,1));save(fig,name)

rows=read('paired_contrasts.csv');fig,axes=grid()
for ax,c in zip(axes.flat,NAMES):
 rr=select(rows,cohort=c,contrast='bayes_lcb_1 minus bayes_mean')
 for i,(key,label) in enumerate(CONFIGS.items()):
  row=next(r for r in rr if r['config']==key);v,lo,hi=[float(row[k]) for k in ['difference','low','high']]
  ax.errorbar(v,3-i,xerr=[[v-lo],[hi-v]],fmt='o',capsize=3,color='#D55E00' if i==0 else '#577590')
 ax.axvline(0,color='black',ls='--',lw=.8);ax.set_yticks(range(4),list(reversed(CONFIGS.values())))
 caption_title(ax,c);ax.set_xlabel('Brier difference\nNegative favors adjustment');ax.grid(axis='x',alpha=.15)
 ax.xaxis.set_major_locator(MaxNLocator(nbins=4))
fig.suptitle('Uncertainty-adjusted score versus posterior mean at 30% capacity\nConditional 95% patient bootstrap intervals',fontsize=11)
fig.tight_layout(rect=(0,0,1,.92));save(fig,'paired_contrasts')

rows=read('learning_all.csv');fig,axes=grid()
for ax,c in zip(axes.flat,NAMES):
 for policy in ['uncertainty','bayes_mean','bayes_lcb_1']:
  rr=select(rows,cohort=c,policy=policy);xs=[.5,.75,1.];ys=[];lo=[];hi=[]
  for x in xs:
   vals=[float(r['brier']) for r in rr if abs(float(r['fraction'])-x)<1e-9];ys.append(np.mean(vals));lo.append(min(vals));hi.append(max(vals))
  ax.plot(np.array(xs)*100,ys,marker=MARKER[policy],linestyle=LINESTYLE[policy],color=COLORS[policy],label=LABELS[policy]);ax.fill_between(np.array(xs)*100,lo,hi,color=COLORS[policy],alpha=.12)
 ax.set_title(NAMES[c]);ax.set_xlabel('Outer training participants retained (%)');ax.set_ylabel('Brier at 30% capacity');ax.grid(alpha=.15)
legend(fig,axes.flat[0]);fig.suptitle('Learning curves | shaded ranges span three correlated development repeats',fontsize=11)
fig.tight_layout(rect=(0,.07,1,.94));save(fig,'learning_curves')

rows=read('develop_all_metrics.csv');fig,axes=grid()
for ax,c in zip(axes.flat,NAMES):
 for i,(config,label) in enumerate(CONFIGS.items()):
  rr=[r for r in select(rows,cohort=c,config=config,policy='bayes_lcb_1') if abs(float(r['budget'])-.3)<1e-9]
  vals=[float(r['brier']) for r in rr]
  ax.scatter(np.repeat(i,len(vals))+np.linspace(-.07,.07,len(vals)),vals,color='#0072B2',s=20)
  ax.scatter(i,np.mean(vals),color='#D55E00',marker='_',s=220,lw=2)
 ax.set_xticks(range(4),['Logistic','Spline','No calibration','No MMSE'],rotation=15,ha='right');ax.set_title(NAMES[c]);ax.set_ylabel('Brier at 30% capacity');ax.grid(axis='y',alpha=.15)
fig.suptitle('Model and ablation comparison | dots are correlated development repeats',fontsize=11)
fig.tight_layout(rect=(0,0,1,.94));save(fig,'ablations')

rows=read('stability_all.csv');fig,axes=grid()
policies=['uncertainty','ridge_gain','bayes_mean','bayes_lcb_1']
for ax,c in zip(axes.flat,NAMES):
 vals=[[float(r['jaccard']) for r in select(rows,cohort=c,policy=p)] for p in policies]
 bp=ax.boxplot(vals,tick_labels=['Uncertainty','Ridge','Bayes mean','Adjusted'],patch_artist=True,showfliers=False)
 for patch,p in zip(bp['boxes'],policies):patch.set_facecolor(COLORS[p]);patch.set_alpha(.3);patch.set_edgecolor('black')
 ax.tick_params(axis='x',rotation=15);ax.set_ylim(-.05,1.05);ax.set_ylabel('Referral Jaccard overlap');ax.set_title(NAMES[c]);ax.grid(axis='y',alpha=.15)
fig.suptitle('Referral stability | 20 complete refits on development-only subsamples\n190 dependent pairs per box; descriptive distributions, not confidence intervals',fontsize=11)
fig.tight_layout(rect=(0,0,1,.91));save(fig,'referral_stability')

rows=read('gain_reliability.csv');fig,axes=grid()
for ax,c in zip(axes.flat,NAMES):
 rr=select(rows,cohort=c);x=[];y=[];lo=[];hi=[]
 for quartile in [1,2,3,4]:
  q=select(rr,quartile=quartile);v=[float(r['observed']) for r in q]
  x.append(np.mean([float(r['predicted']) for r in q]));y.append(np.mean(v));lo.append(min(v));hi.append(max(v))
 ax.errorbar(x,y,yerr=[np.array(y)-lo,np.array(hi)-y],fmt='o-',color='#D55E00',capsize=3)
 for i,(xx,yy) in enumerate(zip(x,y)):ax.annotate(str(i+1),(xx,yy),xytext=(5,5),textcoords='offset points',fontsize=8)
 lim=[min(x+lo+[0]),max(x+hi+[0])];ax.plot(lim,lim,'--',color='black',lw=.8);ax.axhline(0,lw=.6,color='black')
 ax.set_title(NAMES[c]);ax.set_xlabel('Predicted Brier gain');ax.set_ylabel('Observed Brier gain');ax.grid(alpha=.1)
fig.suptitle('Benefit reliability | four within-repeat prediction quartiles\nBars show the range across three correlated development repeats',fontsize=11)
fig.tight_layout(rect=(0,0,1,.91));save(fig,'benefit_reliability')

rows=read('stress_all.csv');fig,axes=grid();conditions=[('clean',0),('missing',.1),('missing',.3),('noise',.1),('noise',.3)]
for ax,c in zip(axes.flat,NAMES):
 for policy in ['uncertainty','bayes_mean','bayes_lcb_1']:
  y=[]
  for kind,level in conditions:
   rr=[r for r in select(rows,cohort=c,policy=policy,perturbation=kind) if abs(float(r['level'])-level)<1e-9]
   y.append(np.mean([float(r['brier']) for r in rr]))
  ax.plot(range(5),y,marker=MARKER[policy],linestyle=LINESTYLE[policy],color=COLORS[policy],label=LABELS[policy])
 ax.set_title(NAMES[c]);ax.set_xticks(range(5),['Clean','10% missing','30% missing','0.1 SD noise','0.3 SD noise'],rotation=25,ha='right');ax.set_ylabel('Mean development Brier');ax.grid(alpha=.15)
legend(fig,axes.flat[0]);fig.suptitle('Controlled perturbations of basic inputs | simulated stress, not new patients',fontsize=11)
fig.tight_layout(rect=(0,.09,1,.94));save(fig,'robustness')

rows=read('cost_all.csv');fig,axes=grid();matrices=[]
for c in NAMES:
 mat=np.zeros((4,6))
 for i,w in enumerate([1,2,5,10]):
  for j,cost in enumerate([0,.01,.05,.1,.2,.5]):
   rr=[r for r in select(rows,cohort=c,config='logistic',fn_weight=w) if abs(float(r['test_cost'])-cost)<1e-10]
   vals={r['policy']:float(r['objective']) for r in rr};mat[i,j]=vals['cost_gate']-vals['basic']
 matrices.append(mat)
scale=max(.01,max(float(np.max(np.abs(x))) for x in matrices))
for ax,c,mat in zip(axes.flat,NAMES,matrices):
 im=ax.imshow(mat,cmap=LinearSegmentedColormap.from_list('cost_difference',['#86B6D9','#FFFFFF','#F2AF83']),vmin=-scale,vmax=scale,aspect='auto')
 for i in range(4):
  for j in range(6):ax.text(j,i,f'{mat[i,j]:+.2f}',ha='center',va='center',fontsize=8,color='black')
 ax.set_xticks(range(6),['0','.01','.05','.1','.2','.5']);ax.set_yticks(range(4),[1,2,5,10]);ax.set_xlabel('Hypothetical cost per advanced panel');ax.set_ylabel('False-negative weight');caption_title(ax,c)
fig.suptitle('Cost-gate objective minus basic-only objective\nNegative favors acquisition; units are hypothetical false-positive error equivalents',fontsize=11)
fig.tight_layout(rect=(0,0,.94,.91));fig.colorbar(im,ax=list(axes.flat),fraction=.025,pad=.02);save(fig,'cost_sensitivity')

rows=read('calibration.csv');fig,axes=grid()
for ax,c in zip(axes.flat,NAMES):
 ax.plot([0,1],[0,1],'--',color='black')
 for policy,color in [('basic','#0072B2'),('advanced','#009E73'),('bayes_lcb_1','#D55E00')]:
  rr=select(rows,cohort=c,policy=policy);ax.plot([float(r['probability']) for r in rr],[float(r['observed']) for r in rr],marker={'basic':'o','advanced':'s','bayes_lcb_1':'^'}[policy],linestyle={'basic':'-','advanced':'--','bayes_lcb_1':':'}[policy],color=color,label={'basic':'Basic only','advanced':'Advanced for all','bayes_lcb_1':'Uncertainty-adjusted benefit'}[policy])
 ax.set_xlim(0,1);ax.set_ylim(0,1);caption_title(ax,c);ax.set_xlabel('Mean probability in occupied bin');ax.set_ylabel('Observed positive fraction')
legend(fig,axes.flat[0]);fig.suptitle('Descriptive calibration | bin width 0.2; sparse bins limit interpretation',fontsize=11)
fig.tight_layout(rect=(0,.06,1,.94));save(fig,'calibration')
print('Saved 10 research figures in PNG and vector PDF formats')
