import importlib, sys, os
sys.path.insert(0, os.path.abspath(os.getcwd()))
mod = importlib.import_module('screen_recorder')
print('screen_recorder __file__:', mod.__file__)
