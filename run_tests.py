"""Run pytest and write output to file.
Sets PYTHONPATH so both backend/ and ai/ are importable.
backend/ must come before ai/ for Django's config module.
"""
import subprocess
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(ROOT, 'backend')
AI = os.path.join(ROOT, 'ai')

python = os.path.join(BACKEND, '.venv', 'Scripts', 'python.exe')

env = dict(os.environ)
# Set PYTHONPATH: backend first (for Django config), then ai
existing = env.get('PYTHONPATH', '')
env['PYTHONPATH'] = f"{BACKEND};{AI}" + (f";{existing}" if existing else "")
env['DJANGO_SETTINGS_MODULE'] = 'config.settings_check'

result = subprocess.run(
    [python, "-m", "pytest", "tests/", "-v", "--tb=short"],
    cwd=ROOT,
    capture_output=True,
    text=True,
    env=env
)

out_path = os.path.join(ROOT, 'test_output.txt')
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(f"EXIT: {result.returncode}\n")
    f.write("STDOUT:\n")
    f.write(result.stdout)
    f.write("\nSTDERR (last 30 lines):\n")
    lines = result.stderr.strip().split('\n') if result.stderr else []
    f.write('\n'.join(lines[-30:]))

print(f"Done. exit={result.returncode}")
print(f"Output written to: {out_path}")
