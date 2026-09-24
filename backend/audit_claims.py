"""Scientific claims audit — search for dangerous unsupported claims."""
import os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FORBIDDEN_PATTERNS = [
    r'accuracy\s*=\s*9[5-9]',
    r'precision\s*=\s*9[5-9]',
    r'recall\s*=\s*9[5-9]',
    r'This is a mine',
    r'This is a bomb',
    r'is a munition',
    r'is a wreck',
    r'field validated',
    r'real-world accuracy',
    r'This is the location of',
]

EXTENSIONS = {'.py', '.tsx', '.ts'}
SKIP_DIRS = {'.venv', 'node_modules', 'dist', '.git', '__pycache__', 'migrations'}

found = []
for dirpath, dirnames, filenames in os.walk(ROOT):
    # Skip unwanted directories
    dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
    for fn in filenames:
        ext = os.path.splitext(fn)[1]
        if ext not in EXTENSIONS:
            continue
        fpath = os.path.join(dirpath, fn)
        try:
            text = open(fpath, encoding='utf-8', errors='ignore').read()
        except:
            continue
        for pattern in FORBIDDEN_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                found.append(f"{fpath}: pattern '{pattern}'")

if found:
    print("DANGEROUS CLAIMS FOUND:")
    for f in found: print(f"  {f}")
else:
    print("[CLEAN] No dangerous scientific claims found.")

# Count files scanned
total = sum(
    1 for d, ds, fs in os.walk(ROOT)
    for f in fs if os.path.splitext(f)[1] in EXTENSIONS
    and not any(s in d for s in SKIP_DIRS)
)
print(f"Scanned {total} files.")
