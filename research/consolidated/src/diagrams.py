"""Colour study and acquisition diagrams with black labels; no invented results."""
from pathlib import Path
import sys,textwrap
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT.parent/'.plot_packages'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'pdf.fonttype':42})
def box(ax,x,y,w,h,text):
 ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.008',facecolor=('#E5F0F8' if x<.27 else '#E5F3EC' if x<.7 else '#FFF0DB'),edgecolor='black',linewidth=1,clip_on=False))
 wrapped='\n'.join(textwrap.fill(line,width=int(w*105),break_long_words=False) for line in text.split('\n'))
 ax.text(x+w/2,y+h/2,wrapped,ha='center',va='center',fontsize=9)
def arrow(ax,start,end):ax.annotate('',xy=end,xytext=start,arrowprops={'arrowstyle':'->','color':'black','lw':1.2})
def save(fig,name):
 for ext in ['png','pdf']:fig.savefig(ROOT/'figures'/f'{name}.{ext}',dpi=220,bbox_inches='tight')
 plt.close(fig)
fig,ax=plt.subplots(figsize=(9,4.2));ax.set_position([.02,.04,.96,.92]);ax.set(xlim=(-.02,1.02),ylim=(0,1));ax.axis('off')
rows=[(.71,'Study A\nMeasurement benefit','OASIS 1 / OASIS 2 / CSF\nGreek AD versus FTD','Development + original holdouts\nEarlier clinical holdouts exposed'),(.39,'Study B\nNested model selection','Same development participants\nEarlier holdouts excluded','Representation and routing comparison\nSource-only repeated validation'),(.07,'Study C\nSensitivity and transport','54 Greek AD / healthy participants\n23 Spanish external participants','Frozen EEG-only external test\nSeparate source AD / FTD analysis')]
for y,a,b,c in rows:
 box(ax,.01,y,.21,.22,a);box(ax,.28,y,.32,.22,b);box(ax,.66,y,.33,.22,c);arrow(ax,(.23,y+.11),(.27,y+.11));arrow(ax,(.61,y+.11),(.65,y+.11))
save(fig,'study_map')
fig,ax=plt.subplots(figsize=(9,4.5));ax.set_position([.02,.04,.96,.92]);ax.set(xlim=(-.02,1.02),ylim=(0,1));ax.axis('off')
ax.text(.01,.95,'TRAINING ONLY',weight='bold')
box(ax,.01,.65,.25,.21,'Basic + advanced measurements\nand recorded outcomes');box(ax,.36,.65,.28,.21,'Cross-fitted model probabilities\nRealized Brier-gain targets');box(ax,.74,.65,.25,.21,'Fit benefit gate\nusing basic information')
arrow(ax,(.27,.75),(.35,.75));arrow(ax,(.65,.75),(.73,.75))
ax.text(.01,.51,'EVALUATION OR PROSPECTIVE USE',weight='bold')
box(ax,.01,.23,.23,.19,'Basic measurements\nBasic-model probability');box(ax,.34,.23,.27,.19,'Score measurement benefit\nRank within fixed-capacity batch');box(ax,.73,.32,.26,.16,'Selected participants\nAdvanced prediction');box(ax,.73,.05,.26,.16,'Other participants\nBasic prediction')
arrow(ax,(.25,.32),(.33,.32));arrow(ax,(.62,.34),(.72,.4));arrow(ax,(.62,.29),(.72,.13))
ax.text(.36,.06,'No evaluation labels or advanced inputs enter the referral score.',fontsize=9,ha='center')
save(fig,'acquisition_flow')
