import unittest
import os
import grader
from grader.decorators import create_file, delete_file, expose_ast, add_value
#from macropy.tracing import macros, trace

CURRENT_FOLDER = os.path.dirname(__file__)
HELPERS_FOLDER = os.path.join(CURRENT_FOLDER, "helpers")

dynamic_tests = []
def dyn_test(f):
    " Create a dynamic test which is called by Tests class automatically "
    f = grader.test(f)
    dynamic_tests.append((f.__name__, f))
    return f

@dyn_test
def stdin_stdout_available(module):
    assert hasattr(module, "stdin")
    assert hasattr(module, "stdout")
    #module.stdin.write("Karl")

@dyn_test
def module_availability(module):
    # module.module should be available after no more reads
    module.stdin.write("Karl")
    assert hasattr(module, "module")

@dyn_test
def stdout_read(module):
    module.stdin.write("Karl")
    stdout = module.stdout.read()
    assert stdout == "Hi, Karl 6\n", stdout


@dyn_test
def finished_property(m):
    assert not m.finished
    m.stdin.write("foo")
    assert m.finished

@dyn_test
def function_call(m):
    m.stdin.write("Karl")
    assert m.module.add_one(9) == 10

@dyn_test
def stdout_new(m):
    m.stdin.write("Karl")
    m.stdout.reset() # reset stdout
    m.module.add_one(193)
    assert(m.stdout.new() == "Got 193\n")


# @dyn_test
# def trace_macro_available(m):
#     m.stdin.write("Karl")
#     m.stdout.reset() # reset stdout
#     trace[1+2+3]
#     n = m.stdout.new()
#     assert "1+2 -> 3\n" in n, n
#     assert "1+2+3 -> 6\n" in n, n

@dyn_test
def io_within_function(m):
    m.stdin.write("Karl")
    m.stdout.reset()
    m.stdin.write("Hello world")
    m.module.askInput()
    assert "Hello world" in m.stdout.read(), m.stdout.read()

@dyn_test
def users_name(m):
    "When running tests, the __name__ within solution module should be set to __main__"
    m.stdin.write("Karl")
    assert hasattr(m, "module")
    assert hasattr(m.module, "something")
    assert m.module.__name__ == "__main__", m.module.__name__
    assert m.module.something == "something"

@grader.test
def doc_only_function(m):
    "this function should have the docstring as its name in grader"

@grader.test
def multiline_doc_function(m):
    """This function should have a multiline docstring 
        as its name in grader
    """

@grader.test
@grader.before_test(create_file('hello.txt', 'Hello world!'))
@grader.after_test(delete_file('hello.txt'))
def hook_test(m):
    with open('hello.txt') as file:
        txt = file.read()
        assert txt == 'Hello world!', txt

@grader.test
@grader.after_test(add_value('x', 1))
@grader.after_test(add_value('x', lambda r: r["description"]))
def add_value_test(m): pass

@dyn_test
@expose_ast
def ast_hook_test(m, AST):
    import ast
    assert isinstance(AST, ast.AST)

@grader.test
def exceptions(m):
    m.stdin.write("Karl")
    m.module.raiseException("SomeAwesomeMessage")

@grader.test
def test_logging(m):
    m.log("something")

class Tests(unittest.TestCase):
    tester_path = os.path.join(CURRENT_FOLDER, "core_tester.py")
    solution_path = os.path.join(HELPERS_FOLDER, "_helper_tested_module.py")

    @classmethod
    def setUpClass(cls):
        grader.reset()
        cls.results = grader.test_module(
            tester_path = cls.tester_path,
            solution_path = cls.solution_path
        )["results"]

    def find_result(self, function):
        test_name = grader.get_test_name(function)
        result = next(filter(lambda x: x["description"] == test_name, self.results))
        return result

    def run_test(self, test_function):
        result = self.find_result(test_function)
        assert result["success"], result

    def tester_initialization(self):
        self.assertTrue(len(grader.testcases) >= len(dynamic_tests) + 3)

    def test_docstring_added_as_test_name(self):
        import inspect
        self.assertIn(inspect.getdoc(doc_only_function), 
                    grader.testcases)

    def test_multiline_docstring(self):
        doc = "This function should have a multiline docstring as its name in grader"
        self.assertIn(doc, grader.testcases)

    def test_hooks(self):
        result = self.find_result(hook_test)
        assert result["success"], result
        assert not os.path.exists(os.path.join(CURRENT_FOLDER, "hello.txt"))

    def test_add_value_hook(self):
        result = self.find_result(add_value_test)
        assert result["success"], result
        assert result["x"] == 1, result

    def test_exceptions_cause_test_failure(self):
        result = self.find_result(exceptions)
        assert not result["success"], result
        assert "SomeAwesomeMessage" in result["traceback"], result

    def test_trace_contains_file_lines(self):
        result = self.find_result(exceptions)
        assert not result["success"], result
        trace = result["traceback"]
        # check if tester module trace is in
        self.assertIn('core_tester.py", line 113', trace)
        # check if user code gets a line
        self.assertIn('line 19, in raiseException', trace)

    def test_logging(self):
        result = self.find_result(test_logging)
        assert result["success"], result
        assert result["log"] == ["something"], result

for test_name, test_function in dynamic_tests:
    setattr(Tests, "test_" + test_name,
            lambda self, t=test_function: self.run_test(t))
