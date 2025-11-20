# print_routes.py
import importlib
app = importlib.import_module("backend.app").app
for r in app.routes:
    print(r.path, getattr(r, "methods", "GET"), r.name)
