"""Download the public APAVA archive; verify the protocol-pinned digest."""
from pathlib import Path
import urllib.request,hashlib,os
ROOT=Path(__file__).resolve().parents[1]
URL='https://osf.io/download/xy8qa/'
SHA='125b85ae83c5258a25cb46935069fe6c7aa3aea9482c54c3710a9c3ed17d0812'
def main():
    dest=ROOT/'data_raw/APAVA_AD_Data.tar.gz';dest.parent.mkdir(exist_ok=True)
    if not dest.exists():
        temp=dest.with_suffix('.download')
        request=urllib.request.Request(URL,headers={'User-Agent':'BrainTriageResearch/4 public research replication'})
        with urllib.request.urlopen(request,timeout=120) as response,temp.open('wb') as stream:
            while chunk:=response.read(1024*1024):stream.write(chunk)
        assert hashlib.sha256(temp.read_bytes()).hexdigest()==SHA,'Archive digest mismatch'
        os.replace(temp,dest)
    assert hashlib.sha256(dest.read_bytes()).hexdigest()==SHA
    print('Public APAVA archive verified; no raw files are published with the study.')
if __name__=='__main__':main()
