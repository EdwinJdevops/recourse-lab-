import json
import os
import subprocess
import sys
import uuid
from pathlib import Path

def k(*args, data=None, check=True):
    return subprocess.run(["kubectl", *args], input=json.dumps(data) if data is not None else None,
                          text=True, capture_output=True, check=check, timeout=30)

def get(ns, name):
    return json.loads(k("-n", ns, "get", "cm", name, "-o", "json").stdout)

def replace(obj, state, check=True):
    obj["data"]["state"] = state
    return k("replace", "-f", "-", data=obj, check=check)

def worker(ns):
    replace(get(ns, "a"), "recovered")
    os._exit(17)

def main():
    ns = "recourse-" + uuid.uuid4().hex[:12]
    k("create", "namespace", ns)
    try:
        for name in ("a", "b"):
            k("-n", ns, "create", "cm", name, "--from-literal=state=initial")
        child = subprocess.run([sys.executable, __file__, "worker", ns], timeout=45)
        assert child.returncode == 17
        a, b = get(ns, "a"), get(ns, "b")
        assert (a["data"]["state"], b["data"]["state"]) == ("recovered", "initial")
        # A separate actor changes A after the recovery worker exits.
        k("-n", ns, "patch", "cm", "a", "--type=merge", "-p", '{"data":{"state":"operator-change"}}')
        stale = replace(a, "initial", check=False)
        assert stale.returncode != 0 and "Conflict" in stale.stderr
        # Resume B without overwriting the operator's change to A.
        replace(b, "recovered")
        before = get(ns, "b")
        if before["data"]["state"] != "recovered":
            replace(before, "recovered")
        after = get(ns, "b")
        final_a = get(ns, "a")
        complete = all(x["data"]["state"] == "recovered" for x in (final_a, after))
        evidence = {"worker_exit": child.returncode, "compensation_error": stale.stderr,
                    "final_a": final_a, "final_b": after, "completion": complete,
                    "repeat_no_write": before["metadata"]["resourceVersion"] == after["metadata"]["resourceVersion"]}
        Path("evidence-009.json").write_text(json.dumps(evidence, indent=2) + "\n")
        assert final_a["data"]["state"] == "operator-change"
        assert after["data"]["state"] == "recovered"
        assert not complete and evidence["repeat_no_write"]
        print("PASS: interruption persisted; stale compensation rejected; operator change preserved; incomplete recovery detected")
    finally:
        k("delete", "namespace", ns, "--wait=false")

if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "worker":
        worker(sys.argv[2])
    else:
        main()
