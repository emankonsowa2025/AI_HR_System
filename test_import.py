# D:\asktech\test_import.py
import importlib, traceback

try:
    importlib.import_module("backend.app")
    print("OK: backend.app imported successfully")
except Exception:
    traceback.print_exc()
