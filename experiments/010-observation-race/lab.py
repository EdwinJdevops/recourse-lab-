import json
import subprocess
import sys
import uuid
from pathlib import Path

def k(*args):
    return json.loads(subprocess.check_output(["kubectl", *args, "-o", "json"], text=True, timeout=30))

def read(ns, name):
    return k("-n", ns, "get", "cm", name)["data"]["state"]

def snapshot(ns):
    obj = k("-n", ns, "get", "cm")
    return {x["metadata"]["name"]: x["data"]["state"] for x in obj["items"] if x["metadata"]["name"] in ("a", "b")}

def patch(ns, name, state):
    k("-n", ns, "patch", "cm", name, "--type=merge", "-p", json.dumps({"data":{"state":state}}))

def actor(ns):
    if sys.stdin.readline().strip() != "advance":
        raise RuntimeError("missing synchronization signal")
    patch(ns, "a", "initial")
    middle = snapshot(ns)
    patch(ns, "b", "recovered")
    print(json.dumps({"middle":middle,"final":snapshot(ns)}), flush=True)

def main():
    ns = "recourse-" + uuid.uuid4().hex[:12]
    k("create", "namespace", ns)
    try:
        k("-n", ns, "create", "cm", "a", "--from-literal=state=recovered")
        k("-n", ns, "create", "cm", "b", "--from-literal=state=initial")
        initial = snapshot(ns)
        with subprocess.Popen([sys.executable, __file__, "actor", ns], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) as child:
            try:
                observed_a = read(ns, "a")
                out, err = child.communicate("advance\n", timeout=100)
            except BaseException:
                child.kill()
                child.communicate()
                raise
            if child.returncode:
                raise RuntimeError(err)
        history = json.loads(out)
        observed_b = read(ns, "b")
        final = snapshot(ns)
        states = [initial, history["middle"], history["final"], final]
        naive = observed_a == observed_b == "recovered"
        collection = all(final.get(n) == "recovered" for n in ("a","b"))
        evidence = {"observations":{"a":observed_a,"b":observed_b},"states":states,"naive_completion":naive,"collection_completion":collection}
        Path("evidence-010.json").write_text(json.dumps(evidence, indent=2)+"\n")
        assert states == [{"a":"recovered","b":"initial"},{"a":"initial","b":"initial"},{"a":"initial","b":"recovered"},{"a":"initial","b":"recovered"}], evidence
        assert naive and not collection, evidence
        print("PASS: separate reads falsely report completion; collection read rejects completion")
    finally:
        subprocess.run(["kubectl","delete","namespace",ns,"--wait=false"],check=True,timeout=30)

if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "actor":
        actor(sys.argv[2])
    else:
        main()
