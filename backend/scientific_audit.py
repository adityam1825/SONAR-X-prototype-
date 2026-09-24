"""
SONAR-X Scientific Claims Audit
Searches all product code for unsupported or incorrect claims.
Distinguishes between legitimate warning documentation vs. product claims.
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {'.venv','node_modules','dist','.git','__pycache__','migrations',
             'pytest_cache','.pytest_cache','staticfiles'}
SKIP_FILES = {'scientific_audit.py','audit_claims.py'}

EXTENSIONS = {'.py','.tsx','.ts','.md'}

# Patterns that are BANNED in actual product claims
# Key = pattern, Value = exempt contexts (substrings that make it OK)
BANNED = {
    r'accuracy\s*[=:]\s*9[5-9][\d.]*%?': ['MUST NOT', 'must not', 'Never', 'never', 'do not', 'NOT display', '# '],
    r'precision\s*[=:]\s*9[5-9][\d.]*%?': ['MUST NOT', 'must not', 'Never', 'never', '# '],
    r'recall\s*[=:]\s*9[5-9][\d.]*%?': ['MUST NOT', 'must not', 'Never', 'never', '# '],
    r'field (validated|validation|performance)': ['not field', 'NOT field', 'Synthetic', 'synthetic', '# ', 'MUST NOT'],
    r'real.world (accuracy|performance|validation)': ['not real', 'NOT real', '# ', 'MUST NOT'],
    r'This is a (mine|bomb|munition|weapon|explosive)': [],  # Always banned
    r'sonar.*(provides|measures).*(temperature|depth|bathymetry)': ['does not', 'NOT', 'cannot'],
    r'object (was|has been) (moved|removed|relocated)': ['not', 'NOT', 'does not', 'POTENTIALLY'],
    r'probability of debris': [],  # Always banned
    r'confirmed (movement|relocation)': ['not confirmed', 'NOT confirmed', 'requires verification'],
}

issues = []
for dirpath, dirnames, filenames in os.walk(ROOT):
    dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
    for fn in filenames:
        if fn in SKIP_FILES: continue
        if os.path.splitext(fn)[1] not in EXTENSIONS: continue
        fpath = os.path.join(dirpath, fn)
        try:
            lines = open(fpath, encoding='utf-8', errors='ignore').readlines()
        except: continue
        for i, line in enumerate(lines, 1):
            for pattern, exemptions in BANNED.items():
                if re.search(pattern, line, re.IGNORECASE):
                    # Check if it's in an exempt context
                    is_exempt = any(ex.lower() in line.lower() for ex in exemptions)
                    if not is_exempt:
                        rel = os.path.relpath(fpath, ROOT)
                        issues.append(f"{rel}:{i}: {line.strip()[:100]}")

print("=" * 60)
print("SCIENTIFIC CLAIMS AUDIT")
print("=" * 60)
if issues:
    print(f"\nPOTENTIAL ISSUES FOUND ({len(issues)}):")
    for iss in issues:
        print(f"  ISSUE: {iss}")
else:
    print(f"\n[CLEAN] No unsupported scientific claims found.")

# Check for required disclaimers in key files
print("\n--- Disclaimer Check ---")
required_disclaimers = {
    'ai/report_generator.py': 'not field performance',
    'ai/demo/demo_engine.py': 'DATA SOURCE: DEMO',
    'ai/hazard/hazard_engine.py': 'precautionary',
    'ai/temporal/temporal_engine.py': 'NOT confirmed',
    'ai/fusion/evidence_fusion.py': 'NOT scientifically validated',
}
for rel_path, required_text in required_disclaimers.items():
    full_path = os.path.join(ROOT, rel_path.replace('/', os.sep))
    if not os.path.exists(full_path):
        print(f"  MISSING FILE: {rel_path}")
        continue
    content = open(full_path, encoding='utf-8', errors='ignore').read()
    if required_text.lower() in content.lower():
        print(f"  [OK] {rel_path}: contains '{required_text}'")
    else:
        print(f"  [MISSING] {rel_path}: must contain '{required_text}'")

sys.exit(0 if not issues else 1)
