"""Label-blind EEG representations for original development participants only."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
import pandas as pd
from scipy.signal import welch,butter,sosfiltfilt
from sklearn.covariance import OAS
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parent/'extension_v2/src'))
import research as prior
from acquire_eeg import features,REGIONS,BANDS
from eeg_ranges import read_window

def matrix_log_vector(cov):
    cov=(cov+cov.T)/2
    assert np.isfinite(cov).all() and np.trace(cov)>0
    cov=cov/np.trace(cov)
    values,vectors=np.linalg.eigh(cov)
    logged=(vectors*np.log(np.maximum(values,1e-10)))@vectors.T
    i,j=np.triu_indices(len(cov))
    return logged[i,j]*np.where(i==j,1,np.sqrt(2))

def extract(eeg):
    original,quality=features(eeg);out=dict(original)
    fs=float(eeg['srate']);x=np.asarray(eeg['data'],float)[:,:int(120*fs)]
    labels=[str(c['labels']) for c in eeg['chanlocs']]
    freq,power=welch(x,fs=fs,nperseg=int(2*fs),noverlap=int(fs),window='hann',detrend='constant',axis=1)
    power=power[:,(freq>=.5)&(freq<30)];active=power.sum(axis=1)>np.finfo(float).eps
    mass=power/np.maximum(power.sum(axis=1,keepdims=True),1e-15)
    spectral_entropy=-np.sum(mass*np.log(np.maximum(mass,1e-15)),axis=1)/np.log(mass.shape[1])
    var0=np.var(x,axis=1);var1=np.var(np.diff(x,axis=1)*fs,axis=1);var2=np.var(np.diff(x,n=2,axis=1)*fs**2,axis=1)
    mobility=np.sqrt(var1/np.maximum(var0,1e-15));complexity=np.sqrt(var2/np.maximum(var1,1e-15))/np.maximum(mobility,1e-15)
    for region,channels in REGIONS.items():
        idx=[labels.index(c) for c in channels if active[labels.index(c)]];assert idx
        logpowers={b:out[f'eeg_{region}_{b}'] for b in BANDS}
        out[f'rich_{region}_theta_alpha']=logpowers['theta']-logpowers['alpha']
        out[f'rich_{region}_slow_fast']=float(np.logaddexp(logpowers['delta'],logpowers['theta'])-np.logaddexp(logpowers['alpha'],logpowers['beta']))
        for name,values in [('entropy',spectral_entropy),('mobility',mobility),('complexity',complexity)]:out[f'rich_{region}_{name}']=float(np.mean(values[idx]))
    for band,(lo,hi) in BANDS.items():
        filtered=sosfiltfilt(butter(4,[lo,hi],btype='bandpass',fs=fs,output='sos'),x,axis=1)
        covariance=OAS().fit(filtered.T).covariance_
        vector=matrix_log_vector(covariance)
        out.update({f'cov_{band}_{j:03d}':float(v) for j,v in enumerate(vector)})
    assert len(out)==805 and np.isfinite(list(out.values())).all()
    return out

def main():
    full,basic,_,train,test=prior.load('eeg_ad_ftd');dev=full.iloc[train]
    rows=[];sources=[]
    for row in dev.itertuples():
        eeg,provenance=read_window(row.id);values=extract(eeg)
        for name in [c for c in full if c.startswith('eeg_')]:
            assert abs(values[name]-getattr(row,name))<1e-12
        rows.append({'id':row.id,'y':row.y,**{c:getattr(row,c) for c in basic},**values})
        sources.append({'id':row.id,'url':provenance['url'],'data_window_sha256':provenance['data_window_sha256']})
        print(f'Extracted development recording {row.id}',flush=True)
    frame=pd.DataFrame(rows).sort_values('id')
    assert set(frame.id)==set(dev.id) and set(frame.id).isdisjoint(full.iloc[test].id)
    (ROOT/'data_raw').mkdir(exist_ok=True);(ROOT/'results').mkdir(exist_ok=True)
    path=ROOT/'data_raw/eeg_development_features.csv';frame.to_csv(path,index=False)
    manifest={'participants':len(frame),'original_spectral_features':20,'additional_spectral_hjorth_features':25,'log_covariance_features':760,'holdout_recordings_processed':0,'feature_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'extractor_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'source_recordings':sources}
    (ROOT/'results/feature_provenance.json').write_text(json.dumps(manifest,indent=2))
    print('Completed 41 development recordings, zero holdout recordings')

if __name__=='__main__':main()
