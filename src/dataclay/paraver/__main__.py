"""Entry point for easy dump to get extrae values per method and class module. 

This module can be run as a standalone and will dump a file to be read from all python nodes 
(must be same event number in all nodes) to be added into PCF paraver file. 
"""

__author__ = 'Alex Barcelo <alex.barcelo@bsc.es>'
__copyright__ = '2015 Barcelona Supercomputing Center (BSC-CNS)'

import ast
import os

if __name__ == "__main__":
    source_dir = "%s/src" % str(os.getcwd())
    current_dir = "%s/dataclay" % source_dir
    dest_dir = "%s/python_paraver_values.properties" % (os.getcwd())
    final_file = open(dest_dir, 'w') 
    current_method_value = 10000
    for root, dirname, filename in os.walk(current_dir):
        pth_build = ""
        if os.path.isfile(root + "/__init__.py"):
            for i in filename:
                if i != "__init__.py" and i != "__init__.pyc":
                    if i.split('.')[1] == "py":
                        slot = list(set(root.split('\\')) - set(os.getcwd().split('\\')))
                        pth_build = slot[0]
                        del slot[0]
                        for j in slot:
                            pth_build = pth_build + "/" + j
                        
                        class_name = i.split('.')[0]
                        module_dir = pth_build + "/" + i
                        module_name = module_dir.replace("/", ".").replace(".py", "")
                        # print pth_build + "." + i.split('.')[0]
                        with open(module_dir) as file:
                            node = ast.parse(file.read())
                        
                        classes = [n for n in node.body if isinstance(n, ast.ClassDef)]
                        for class_ in classes:
                            methods = [n for n in class_.body if isinstance(n, ast.FunctionDef)]
                            for method in methods:
                                actual_module_name = module_dir.replace(source_dir, "").replace("/", ".").replace(".py", "")[1:]
                                actual_method = actual_module_name + "." + class_.name + "." + method.name
                                final_file.write(actual_method + "=" + str(current_method_value) + "\n")
                                current_method_value = current_method_value + 1

    final_file.close()
    
