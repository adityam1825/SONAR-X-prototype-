import subprocess, os
r = subprocess.run(["npm","run","build"], cwd=os.path.dirname(__file__),
    capture_output=True, text=True, shell=True)
with open(os.path.join(os.path.dirname(__file__),"..","final_build.txt"),"w",encoding="utf-8") as f:
    f.write(f"EXIT:{r.returncode}\n{r.stdout}\n{r.stderr}")
print(f"exit={r.returncode}")
for l in (r.stdout+r.stderr).split("\n")[-10:]: print(l)
