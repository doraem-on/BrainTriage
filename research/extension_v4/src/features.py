"""Fixed shared-channel feature adapter; no fitted target transformations."""
from pathlib import Path
import sys,io,json,tarfile,hashlib,math,warnings,collections
import numpy as np
import pandas as pd
from scipy.io import loadmat
from scipy.signal import resample_poly,butter,sosfiltfilt,welch
from sklearn.covariance import OAS
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parent/'extension_v3/src'))
from extract_features import matrix_log_vector
import experiment
from eeg_ranges import read_window
PLAN=json.loads((ROOT/'protocol.json').read_text())
CHANNELS=PLAN['external_companion']['channels']
BANDS={'delta':(.5,4),'theta':(4,8),'alpha':(8,13),'beta':(13,30)}
REGIONS={'frontal':['F3','F4','F7','F8','Fp1','Fp2'],'central':['C3','C4'],'temporal':['T3','T4','T5','T6'],'parietal':['P3','P4'],'occipital':['O1','O2']}
AD_POSITIVE={1,3,6,8,9,11,12,13,15,17,19,21}
def segment_features(raw,labels,fs):
    assert len(labels)==len(set(labels)) and all(c in labels for c in CHANNELS)
    x=np.asarray(raw,float)[[labels.index(c) for c in CHANNELS],:]
    assert x.shape==(16,int(5*fs)) and np.isfinite(x).all()
    x=x-x.mean(axis=0,keepdims=True)
    divisor=math.gcd(int(fs),128);x=resample_poly(x,128//divisor,int(fs)//divisor,axis=1)
    x=sosfiltfilt(butter(4,[.5,30],fs=128,btype='bandpass',output='sos'),x,axis=1)
    assert x.shape==(16,640)
    f,p=welch(x,fs=128,nperseg=256,noverlap=128,window='hann',detrend='constant',axis=1)
    total=p[:,(f>=.5)&(f<30)].sum(axis=1);assert np.all(total>0)
    out={}
    for region,chs in REGIONS.items():
        idx=[CHANNELS.index(c) for c in chs]
        for name,(lo,hi) in BANDS.items():out[f'spectral_{region}_{name}']=float(np.log(np.mean(p[idx][:,(f>=lo)&(f<hi)].sum(axis=1)/total[idx])+1e-8))
    for name,(lo,hi) in BANDS.items():
        filtered=sosfiltfilt(butter(4,[lo,hi],fs=128,btype='bandpass',output='sos'),x,axis=1)
        cov=OAS().fit(filtered.T).covariance_;vector=matrix_log_vector(cov)
        out.update({f'cov_{name}_{j:03d}':float(v) for j,v in enumerate(vector)})
    assert len(out)==564 and np.isfinite(list(out.values())).all()
    return out

def aggregate(trials,labels,fs):
    rows=[segment_features(t,labels,fs) for t in trials[:24]]
    assert rows
    return {k:float(np.mean([r[k] for r in rows])) for k in rows[0]}

def main():
    manifest={'adapter_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'source':[],'external':[],'label_mapping_source_blob':'b6b9c130b9e519366c2844a8c203b80c9d5d8536'}
    dev,_,_,forbidden=experiment.load_development('eeg_ad_ftd')
    meta=pd.read_csv(ROOT.parent/'extension_v2/data_raw/participants.tsv',sep='\t')
    chosen=meta[meta.participant_id.isin(dev.loc[dev.y.eq(1),'id'])|meta.Group.eq('C')]
    assert len(chosen)==54 and set(chosen.participant_id).isdisjoint(forbidden)
    rows=[]
    for row in chosen.itertuples():
        eeg,provenance=read_window(row.participant_id);fs=int(eeg['srate']);x=eeg['data'];labels=[c['labels'] for c in eeg['chanlocs']]
        trials=[x[:,i*5*fs:(i+1)*5*fs] for i in range(24)]
        values=aggregate(trials,labels,fs)
        rows.append({'id':row.participant_id,'y':int(row.Group=='A'),**values})
        manifest['source'].append({'id':row.participant_id,'url':provenance['url'],'data_window_sha256':provenance['data_window_sha256'],'segments_used':24})
        print('Extracted source',row.participant_id,flush=True)
    pd.DataFrame(rows).sort_values('id').to_csv(ROOT/'data_raw/source_features.csv',index=False)
    path=ROOT/'data_raw/APAVA_AD_Data.tar.gz';digest=hashlib.sha256(path.read_bytes()).hexdigest();assert digest=='125b85ae83c5258a25cb46935069fe6c7aa3aea9482c54c3710a9c3ed17d0812'
    rows=[]
    with tarfile.open(path) as archive:
        members=sorted([m for m in archive.getmembers() if m.isfile()],key=lambda m:m.name);assert len(members)==23
        for m in members:
            raw=archive.extractfile(m).read();d=loadmat(io.BytesIO(raw),simplify_cells=True)['data']
            number=int(Path(m.name).stem.removeprefix('preproctrials'));assert 1<=number<=23
            trials=d['trial'];trials=[trials] if trials.ndim==2 and trials.dtype!=object else list(trials)
            labels=list(d['label']);fs=int(d['fsample']);assert fs==256
            values=aggregate(trials,labels,fs);pid=f'APAVA-{number:02d}'
            rows.append({'id':pid,'y':int(number in AD_POSITIVE),**values})
            manifest['external'].append({'file':m.name,'sha256':hashlib.sha256(raw).hexdigest(),'segments_available':len(trials),'segments_used':min(24,len(trials)),'channels':labels,'fs':fs})
            print('Extracted external recording',pid,flush=True)
    frame=pd.DataFrame(rows).sort_values('id');assert frame.id.is_unique and frame.y.sum()==12
    frame.to_csv(ROOT/'data_raw/external_features.csv',index=False)
    manifest['archive_sha256']=digest
    manifest['feature_hashes']={name:hashlib.sha256((ROOT/'data_raw'/name).read_bytes()).hexdigest() for name in ['source_features.csv','external_features.csv']}
    (ROOT/'results/feature_provenance.json').write_text(json.dumps(manifest,indent=2))
if __name__=='__main__':
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter('always',RuntimeWarning);main()
    (ROOT/'results/feature_warnings.json').write_text(json.dumps(dict(collections.Counter(str(x.message) for x in w)),indent=2))
