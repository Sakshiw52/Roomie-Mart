import os
import sys
import importlib.util

# Load app.py by absolute path (handles spaces in workspace path)
root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
app_path = os.path.join(root, 'app.py')

spec = importlib.util.spec_from_file_location('app', app_path)
app_module = importlib.util.module_from_spec(spec)
sys.modules['app'] = app_module
sys.path.insert(0, root)
spec.loader.exec_module(app_module)
app = app_module.app

# Print sorted endpoints and rules
endpoints = sorted([(r.endpoint, r.rule) for r in app.url_map.iter_rules()])
for endpoint, rule in endpoints:
    print(f"{endpoint} -> {rule}")
