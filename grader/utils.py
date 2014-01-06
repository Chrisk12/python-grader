""" An utility module containing utility functions used by the grader module 
    and some useful pre-test hooks.
"""
import os
import json
import contextlib
import traceback

from tempfile import NamedTemporaryFile

def import_module(path, name=None):
    if name is None:
        name = path
    import importlib.machinery
    loader = importlib.machinery.SourceFileLoader(name, path)
    module = loader.load_module(name)
    return module

def get_module_AST(path):
    import tokenize
    import ast
    with tokenize.open(path) as sourceFile:
        contents = sourceFile.read()
    return ast.parse(contents)


@contextlib.contextmanager
def tempModule(code, working_dir=None, encoding="utf8"):
    if working_dir is None: 
        working_dir = os.getcwd()
    file = NamedTemporaryFile(
        dir = working_dir,
        mode = "wb",
        suffix = ".py",
        delete = False
    )
    file.write(code.encode(encoding))
    file.close()
    try:
        yield file.name
    finally:
        os.remove(file.name)


## Function descriptions
def beautifyDescription(description):
    """ Converts docstring of a function to a test description
        by removing excess whitespace and joining the answer on one
        line """
    lines = (line.strip() for line in description.split('\n'))
    return " ".join(filter(lambda x:x, lines))

def setDescription(function, description):
    import grader
    old_description = grader.get_test_name(function)
    if old_description in grader.testcases:
        del grader.testcases[old_description]
    description = beautifyDescription(description)
    function.__doc__ = description
    grader.testcases[description] = function



## Json managing
def load_json(json_string):
    " Loads json_string into an dict "
    return json.loads(json_string)

def dump_json(ordered_dict):
    " Dumps the dict to a string, indented "
    return json.dumps(ordered_dict, indent=4)#, ensure_ascii=False)


## 
def get_traceback(exception):
    type_, value, tb = type(exception), exception, exception.__traceback__
    return "".join(traceback.format_exception(type_, value, tb))



## File creation, deletion for hooks
def create_file(filename, contents = ""):
    " Hook for creating files "
    import collections
    if isinstance(contents, collections.Iterable) and not isinstance(contents, str):
        contents = "\n".join(map(str, contents))

    def _inner(info):
        with open(filename, "w") as f:
            f.write(contents)

    return _inner

def delete_file(filename):
    " Hook for deleting files "

    def _inner():
        try: os.remove(filename)
        except: pass

    return _inner

def expose_ast(test_function):
    """ Decorator for exposing the ast of the solution module
        as an argument to the tester. Uses a pre-test hook. """
    from grader.core import before_test
    def _hook(info):
        module_ast = get_module_AST(info["user_module"])
        info["extra_kwargs"]["AST"] = module_ast

    return before_test(_hook)(test_function)


def create_temporary_file(filename, contents = ""):
    from grader.core import before_test, after_test
    """ Decorator for constructing a file which is available
        during a single test and is deleted afterwards. """
    def _inner(test_function):
        before_test(create_file(filename, contents))(test_function)
        after_test(delete_file(filename))(test_function)
        return test_function
    return _inner