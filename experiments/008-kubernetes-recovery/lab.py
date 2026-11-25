#!/usr/bin/env python3
import json, subprocess, uuid
from pathlib import Path

def k(*args, data=None, ok=True):
    p=subprocess.run(["kubectl",*args],input=json.dumps(data) if data else None,text=True,capture_output=True,timeout=30)
    if ok and p.returncode: raise RuntimeError(p.stderr)
    return p

def obj(ns,name,value):
    return {"apiVersion":"v1","kind":"ConfigMap","metadata":{"namespace":ns,"name":name},"data":{"state":value}}

def main():
    ns="recourse-"+uuid.uuid4().hex[:12]
    k("create","namespace",ns)
    try:
        for name in ("a","b"): k("create","-f","-",data=obj(ns,name,"initial"))
        def get(name): return json.loads(k("-n",ns,"get","configmap",name,"-o","json").stdout)
        a,b=get("a"),get("b")
        a["data"]["state"]="recovered"
        b["data"]["state"]="recovered"
        k("replace","--dry-run=server","-f","-",data=b)
        assert get("b")["data"]["state"]=="initial"
        k("replace","-f","-",data=a)
        k("-n",ns,"patch","configmap","b","--type=merge","-p",'{"data":{"state":"changed"}}')
        p=k("replace","-f","-",data=b,ok=False)
        final_a,final_b=get("a"),get("b")
        evidence={"stale_update_exit":p.returncode,"stale_update_stderr":p.stderr,"initial_b_version":b["metadata"]["resourceVersion"],"final_a":final_a,"final_b":final_b}
        Path("evidence-008.json").write_text(json.dumps(evidence,indent=2)+"\n")
        assert p.returncode != 0 and "Conflict" in p.stderr, evidence
        assert final_a["data"]["state"]=="recovered" and final_b["data"]["state"]=="changed", evidence
        print("PASS: dry-run did not persist; stale update rejected; partial workflow state observed")
    finally:
        k("delete","namespace",ns,"--wait=false")
if __name__=="__main__": main()
