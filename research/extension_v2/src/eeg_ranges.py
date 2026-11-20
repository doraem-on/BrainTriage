"""Read only the prespecified 120 seconds, retaining exact source-byte hashes.

The OpenNeuro EEGLAB files use uncompressed MATLAB v5 matrices. This reader
checks that format and reads the same values as scipy.loadmat without fetching
unused minutes. Unsupported encodings fail rather than silently approximating.
"""
from pathlib import Path
import io, struct, hashlib, urllib.request, json, time
import numpy as np
from scipy.io import loadmat
from acquire_eeg import ROOT, BASE

def tag(buf,pos):
    a,b=struct.unpack_from('<II',buf,pos);small=a>>16
    if small:return a&65535,small,buf[pos+4:pos+4+small],pos+8
    return a,b,buf[pos+8:pos+8+b],pos+8+8*((b+7)//8)

def matrix_header(block):
    kind,n=struct.unpack_from('<II',block,0);assert kind==14,'Compressed/nested MAT structure unsupported'
    pos=8
    for _ in range(2):kind2,size,value,pos=tag(block,pos)
    dims=np.frombuffer(value,dtype='<i4')
    _,_,name,pos=tag(block,pos)
    return n,name.decode('ascii'),dims,pos

def read_window(pid):
    relative=f'derivatives/{pid}/eeg/{pid}_task-eyesclosed_eeg.set'
    full=ROOT/'data_raw'/relative;cache=ROOT/'data_raw/ranges'/pid;cache.mkdir(parents=True,exist_ok=True)
    records=[];etag=[None]
    def read(start,length):
        target=cache/f'{start}_{length}.bin';metadata=target.with_suffix('.json')
        if target.exists() and metadata.exists():
            data=target.read_bytes();meta=json.loads(metadata.read_text())
        else:
            if full.exists():
                with full.open('rb') as f:f.seek(start);data=f.read(length)
                meta={'source':'previously downloaded complete file','object_bytes':full.stat().st_size}
            else:
                req=urllib.request.Request(BASE+relative,headers={'Range':f'bytes={start}-{start+length-1}'})
                for attempt in range(3):
                    try:
                        with urllib.request.urlopen(req,timeout=60) as response:
                            assert response.status==206,'Server did not honor Range request'
                            content=response.headers['Content-Range']
                            assert content.startswith(f'bytes {start}-')
                            data=response.read();meta={'source':'HTTP byte range','content_range':content,'etag':response.headers.get('ETag'),'object_bytes':int(content.split('/')[1])}
                        break
                    except Exception:
                        if attempt==2:raise
                        time.sleep(1)
            assert len(data)==min(length,meta['object_bytes']-start)
            target.write_bytes(data);metadata.write_text(json.dumps(meta))
        if meta.get('etag'):
            if etag[0] is not None:assert etag[0]==meta['etag'],'Source changed during acquisition'
            etag[0]=meta['etag']
        records.append({'start':start,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),**meta})
        return data
    first=read(0,4096);assert first[126:128]==b'IM','Requires little-endian MATLAB v5'
    header=first[:128];offset=128;small={};data_start=None
    while data_start is None:
        block=first[offset:] if offset+256<=len(first) else read(offset,4096)
        n,name,dims,pos=matrix_header(block)
        if name in ['srate','nbchan','pnts']:
            small[name]=loadmat(io.BytesIO(header+block[:n+8]),simplify_cells=True)[name]
        if name=='data':
            dtype,size=struct.unpack_from('<II',block,pos)
            assert dtype in [7,9] and len(dims)==2 and dims[0]==19
            data_start=offset+pos+8;dtype=np.dtype('<f4' if dtype==7 else '<f8')
            after=offset+8+8*((n+7)//8)
        offset+=8+8*((n+7)//8)
    fs=float(small['srate']);samples=int(120*fs);assert dims[1]>=samples
    raw=read(data_start,19*samples*dtype.itemsize)
    data=np.frombuffer(raw,dtype=dtype).reshape((19,samples),order='F').astype(float)
    tail=read(after,65536);pos=0
    while True:
        n,name,_,_=matrix_header(tail[pos:])
        if name=='chanlocs':
            channels=loadmat(io.BytesIO(header+tail[pos:pos+n+8]),simplify_cells=True)['chanlocs'];break
        pos+=8+8*((n+7)//8)
        assert pos+256<len(tail),'Channel metadata outside bounded read'
    eeg={'data':data,'srate':fs,'chanlocs':channels}
    provenance={'id':pid,'path':relative,'url':BASE+relative,'range_reads':records,
        'recording_seconds':int(small['pnts'])/fs,'source_values':'Exact first 120 seconds of source data matrix; not resampled or synthesized',
        'data_window_sha256':hashlib.sha256(raw).hexdigest()}
    return eeg,provenance
