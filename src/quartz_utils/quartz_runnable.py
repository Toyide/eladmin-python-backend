# coding=utf-8
"""
Copyright 2019-2022 Ge Yide

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

# @Time    : 2022/7/11 18:13
# @Author  : Fang Jin Biao
# @Modified: Ge Yide
# @Email   : yge@dal.ca
# @File    : quartz_runnable.py
# @Project : eladmin_py_backend
import importlib
import inspect
import os
import sys
from multiprocessing import Process


class QuartzRunnable(Process):
    def __init__(self, bean_name, method_name, params):
        super().__init__()
        self.bean_name = bean_name
        self.method_name = method_name
        self.params = params
        self.result = None

    def run(self):
        print(f"QuartzRunnable::call: beanName={self.bean_name}, method={self.method_name}")
        module_path = os.path.dirname(self.bean_name)
        sys.path.insert(0, module_path)
        try:
            module_name = inspect.getmodulename(self.bean_name)
            module = importlib.import_module(module_name)
            func = getattr(module, self.method_name)
            self.result = func(*self.params.split(","))
        except Exception as e:
            print(e)
            raise e
        finally:
            sys.path.remove(module_path)
