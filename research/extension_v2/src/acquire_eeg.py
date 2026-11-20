"""Acquire real public OpenNeuro EEG recordings and derive one row per person."""
from pathlib import Path
import json, hashlib, urllib.request, time, concurrent.futures
import numpy as np
import pandas as pd
from scipy.io import loadmat
from scipy.signal import welch
ROOT=Path(__file__).resolve().parents[1]
BASE='https://s3.amazonaws.com/openneuro.org/ds004504/'
REGIONS={'frontal':['Fp1','Fp2','F7','F3','Fz','F4','F8'],
         'central':['C3','Cz','C4'],'temporal':['T3','T4','T5','T6'],
         'parietal':['P3','Pz','P4'],'occipital':['O1','O2']}
BANDS={'delta':(.5,4),'theta':(4,8),'alpha':(8,13),'beta':(13,30)}

def fetch(relative):
    out=ROOT/'data_raw'/relative;out.parent.mkdir(parents=True,exist_ok=True)
    if not out.exists():
        for attempt in range(3):
            try:
                with urllib.request.urlopen(BASE+relative,timeout=120) as r:
                    data=r.read();etag=r.headers.get('ETag','')
                tmp=out.with_suffix(out.suffix+'.tmp');tmp.write_bytes(data);tmp.replace(out)
                break
            except Exception:
                if attempt==2:raise
                time.sleep(2)
    data=out.read_bytes()
    return out,{'path':relative,'url':BASE+relative,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}

def features(path):
    mat=path if isinstance(path,dict) else loadmat(path,simplify_cells=True)
    eeg=mat.get('EEG',mat)
    data=np.asarray(eeg['data'],dtype=float);fs=float(eeg['srate'])
    assert data.ndim==2 and data.shape[0]==19 and np.isfinite(data).all()
    assert data.shape[1]>=int(120*fs),'Recording shorter than fixed window'
    channels=[str(c['labels']) for c in eeg['chanlocs']]
    f,psd=welch(data[:,:int(120*fs)],fs=fs,nperseg=int(2*fs),noverlap=int(fs),window='hann',axis=1,detrend='constant')
    total=psd[:,(f>=.5)&(f<30)].sum(axis=1)
    active=total>np.finfo(float).eps
    out={}
    for region,labels in REGIONS.items():
        idx=[channels.index(c) for c in labels if active[channels.index(c)]]
        assert len(idx)>0
        for band,(lo,hi) in BANDS.items():
            relative=psd[idx][:,(f>=lo)&(f<hi)].sum(axis=1)/total[idx]
            out[f'eeg_{region}_{band}']=float(np.log(relative.mean()+1e-8))
    return out,{'sampling_hz':fs,'recording_seconds':data.shape[1]/fs,'window_seconds':120,'channels':channels,'active_channels':int(active.sum())}

def main():
    (ROOT/'results').mkdir(exist_ok=True,parents=True)
    meta=[]
    for rel in ['participants.tsv','participants.json','dataset_description.json','README']:
        path,record=fetch(rel);meta.append(record)
    description=json.loads((ROOT/'data_raw/dataset_description.json').read_text())
    assert description['License']=='CC0'
    d=pd.read_csv(ROOT/'data_raw/participants.tsv',sep='\t');d=d[d.Group.isin(['A','F'])].copy()
    assert len(d)==59 and (d.Group=='A').sum()==36 and d.participant_id.is_unique
    def process(row):
        pid=row.participant_id;rel=f'derivatives/{pid}/eeg/{pid}_task-eyesclosed_eeg.set'
        from eeg_ranges import read_window
        eeg,record=read_window(pid);feat,quality=features(eeg)
        quality['recording_seconds']=record['recording_seconds']
        result={'id':pid,'age':row.Age,'male':int(row.Gender=='M'),'mmse':row.MMSE,'y':int(row.Group=='A'),**feat}
        print(f'{pid}: exact 120-second window, {quality["recording_seconds"]:.1f}s source, 20 measured EEG features',flush=True)
        return result,{**record,**quality,'id':pid}
    rows=[];records=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for result,record in pool.map(process,d.itertuples(index=False)):
            rows.append(result);records.append(record)
    frame=pd.DataFrame(rows).sort_values('id');assert np.isfinite(frame.drop(columns='id')).all().all()
    frame.to_csv(ROOT/'data_raw/eeg_features.csv',index=False)
    manifest={'dataset':'OpenNeuro ds004504','dataset_doi':description['DatasetDOI'],'license':description['License'],
        'source_metadata':meta,'recordings':records,'participants':len(frame),'ad_n':int(frame.y.sum()),
        'feature_file_sha256':hashlib.sha256((ROOT/'data_raw/eeg_features.csv').read_bytes()).hexdigest(),
        'pipeline_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (ROOT/'results/eeg_provenance.json').write_text(json.dumps(manifest,indent=2))
    print('Completed actual EEG feature extraction for all 59 AD/FTD participants',flush=True)

if __name__=='__main__':main()
