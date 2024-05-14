#!/usr/bin/env python3
import importlib.util
import sys

def load_class_from_path(path, class_name):
    module_name = path.split('/')[-1].split('.')[0]
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return getattr(module, class_name)

path = '../hystfit/hystfit.py'
Fit = load_class_from_path(path, 'Fit')
f = Fit()
f.debug = True
f.test()
