"""
Root conftest.py for SONAR-X test suite.

Must add backend/ to sys.path FIRST (for Django's config module),
then ai/ AFTER (AI modules with same names as Django app stubs).

The AI engine tests explicitly insert ai/ at position 0 in their
own module-level sys.path setup to get the correct fingerprint/fusion/etc.
"""
import sys
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT, 'backend')
AI_DIR = os.path.join(ROOT, 'ai')

# backend must come first for Django's config module
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# ai after backend (AI tests will override locally when needed)
if AI_DIR not in sys.path:
    sys.path.append(AI_DIR)
