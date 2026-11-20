"""Read public BrainLat metadata; never accept terms or use restricted resources."""
import urllib.request,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE='https://repo-prod.prod.sagebase.org/repo/v1'
def get(path,payload=None):
    req=urllib.request.Request(BASE+path,data=None if payload is None else json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=45) as r:return json.load(r)
def children(pid):return get('/entity/children',{'parentId':pid,'includeTypes':['folder','file','link','table'],'sortBy':'NAME','sortDirection':'ASC'})
if __name__=='__main__':
    records=[]
    def walk(pid,depth):
        result=children(pid);records.append({'parent':pid,**result})
        print(pid,json.dumps(result))
        if depth:
            for x in result['page']:
                if x['type'].endswith('Folder'):walk(x['id'],depth-1)
    walk('syn53972960',1)
    (ROOT/'data_raw/brainlat_inventory.json').write_text(json.dumps(records,indent=2))
