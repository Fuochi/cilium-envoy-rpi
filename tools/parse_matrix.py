#!/usr/bin/env python3
import json, os, re, subprocess, sys

readme = sys.argv[1] if len(sys.argv) > 1 else "README.md"

# --- 1. parse the markdown compatibility table -------------------------------
rows, in_table = [], False
for raw in open(readme):
    line = raw.strip()
    if line.startswith("| Cilium Version"):
        in_table = True
        continue
    if in_table:
        if not line.startswith("|"):
            break
        if set(line) <= set("|-: "):      # separator row
            continue
        cols = [c.strip() for c in line.strip("|").split("|")]
        if len(cols) >= 2:
            rows.append((cols[0], cols[1]))   # (cilium, envoy)

# --- 2a. keep only the newest patch within each Cilium minor -----------------
# Toggle with LATEST_PATCH_ONLY (default "true"); "false" builds every patch.
def ver(v):
    m = re.match(r"v(\d+)\.(\d+)\.(\d+)$", v)
    return tuple(int(x) for x in m.groups()) if m else None

if os.environ.get("LATEST_PATCH_ONLY", "true") == "true":
    newest = {}                       # minor -> (version_tuple, cilium, envoy)
    for cil, env in rows:
        t = ver(cil)
        if not t:                     # skip "(main)" and similar
            continue
        minor = (t[0], t[1])
        if minor not in newest or t > newest[minor][0]:
            newest[minor] = (t, cil, env)
    selected = [(c, e) for _, c, e in newest.values()]
else:
    selected = rows

# --- 2b. dedupe by concrete Envoy version, map to release branch -------------
groups = {}
for cil, env in selected:
    if "(" in cil or "x" in env:           # skip moving targets: (main) / v1.36.x
        continue
    m = re.match(r"v(\d+)\.(\d+)\.\d+", env)
    if not m:
        continue
    branch = f"v{m.group(1)}.{m.group(2)}"
    g = groups.setdefault(env, {"envoy": env, "branch": branch, "ciliums": []})
    g["ciliums"].append(cil)

# --- 3. find tags already in GHCR so we only build what's new ----------------
owner = os.environ["OWNER"]
existing = set()
try:
    out = subprocess.check_output(
        ["gh", "api", "--paginate",
         f"/users/{owner}/packages/container/cilium-envoy/versions",
         "--jq", ".[].metadata.container.tags[]"],
        stderr=subprocess.DEVNULL).decode()
    existing = set(out.split())
except Exception:
    pass   # package may not exist yet on the first run

force = os.environ.get("FORCE_ALL", "false") == "true"
include = []
for env, g in sorted(groups.items()):
    if not force and f"{env}-arm64-rpi" in existing:
        continue
    include.append({"envoy": env, "branch": g["branch"],
                    "ciliums": " ".join(g["ciliums"])})

matrix = {"include": include}
with open(os.environ["GITHUB_OUTPUT"], "a") as f:
    f.write(f"matrix={json.dumps(matrix)}\n")
    f.write(f"any={'true' if include else 'false'}\n")
print(json.dumps(matrix, indent=2))
