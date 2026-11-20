"""Download the exact public mirrors used in this study and verify every CSV.

Review the original dataset access and reuse terms before running. This script
does not grant a data license. No ZIP extraction to archive-controlled paths.
"""
from pathlib import Path
import hashlib, urllib.request, zipfile, io, json
ROOT=Path(__file__).resolve().parents[1]
SOURCES=[
 ('jboysen/mri-and-alzheimers', [
 ('oasis_cross-sectional.csv','data/oasis_cross-sectional.csv','059f0c5ea237a20e1455c2a22decac1224f542bf108d7befd0e12a9b48abfe57'),
 ('oasis_longitudinal.csv','data/oasis_longitudinal.csv','d2f0a15ff35fa4a65c35c064b848fc1b396e9d2f4aec935c88d6e1588d31d40e')]),
 ('fereshtehjozaghkar/plasma-lipidomics-in-alzheimers-disease', [
 ('Plasma lipidomics in Alzheimers disease and its progression-1.csv','data_external/csf_biomarkers.csv','af92a64e588b154bb6d48052be6aaa3b1eda3aea5a884d91da2f62592822b142')])]

def main():
    records=[]
    for source,files in SOURCES:
        url='https://www.kaggle.com/api/v1/datasets/download/'+source
        req=urllib.request.Request(url,headers={'User-Agent':'BrainTriage-research/1.0'})
        with urllib.request.urlopen(req,timeout=120) as response: archive=response.read()
        with zipfile.ZipFile(io.BytesIO(archive)) as z:
            for member,dest,expected in files:
                data=z.read(member); actual=hashlib.sha256(data).hexdigest()
                if actual!=expected: raise RuntimeError(f'Source changed: {member}; expected {expected}, got {actual}')
                output=ROOT/'data_raw'/dest; output.parent.mkdir(parents=True,exist_ok=True)
                output.write_bytes(data)
                records.append({'source':source,'file':dest,'sha256':actual,'bytes':len(data)})
    (ROOT/'data_raw/acquisition.json').write_text(json.dumps(records,indent=2))
    print('Verified three CSVs. Set BRAINTRIAGE_SOURCE to '+str(ROOT/'data_raw'))

if __name__=='__main__': main()
