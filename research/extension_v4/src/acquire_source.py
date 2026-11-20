"""Acquire source-only healthy-control windows; preserve original AD holdouts."""
from pathlib import Path
import sys,json,concurrent.futures
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parent/'extension_v3/src'))
import experiment
from eeg_ranges import read_window
if __name__=='__main__':
    dev,_,_,forbidden=experiment.load_development('eeg_ad_ftd')
    meta=pd.read_csv(ROOT.parent/'extension_v2/data_raw/participants.tsv',sep='\t')
    ad=set(dev.loc[dev.y.eq(1),'id']);chosen=meta[meta.participant_id.isin(ad)|meta.Group.eq('C')]
    assert len(chosen)==54 and chosen.Group.eq('A').sum()==25 and set(chosen.participant_id).isdisjoint(forbidden)
    def one(pid):
        _,record=read_window(pid);print('Cached source window',pid,flush=True);return record
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:records=list(pool.map(one,chosen.participant_id))
    (ROOT/'data_raw/source_windows.json').write_text(json.dumps(records,indent=2));print('Completed',len(records),'source participants')
