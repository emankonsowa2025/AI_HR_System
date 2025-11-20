import os, sys
print("cwd:", os.getcwd())
print("sys.path[0]:", sys.path[0])
print("exists backend\\__init__.py:", os.path.exists("backend\\__init__.py"))
print("exists backend\\api\\__init__.py:", os.path.exists("backend\\api\\__init__.py"))
exit