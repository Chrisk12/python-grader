""" Wrappers to make writing tests easier """

#from macropy.tracing import macros, require
from .core import *
from .utils import *
from .assertions import *
from .decorators import *


def io_test(description, writes_list, expected_read):
    """ Tests whether after writing each element of writes_list to stdin we
        can find expected_read in the resulting output.

        Note that this also tests whether the program is waiting for before
        each write and that it's not after the last one. """
    
    def f(module):
        for i, write in enumerate(writes_list):
            assert module.is_waiting_input(), \
                "Did you forget to use input()? Writes so far: %s" % writes_list[:i]
            module.stdout.reset()
            module.stdin.write(write)
        require_contains(module.stdout.new(), expected_read)
        assert not module.is_waiting_input(), \
            "Make sure there isn't a stray input() after your code"
    setDescription(f, description)
    return test(f)


def check_function(function_name, args, expected_result, description=None):
    """ Tests that calling function with the given name exists and calling it
        with args gives expected_result.

        If description is given, it is used as test name, else the description
        will before similar to "Check add(1, 2, 3) == 6" """

    def f(m):
        assert hasattr(m, "module"), "Do not use input() in this solution"
        assert hasattr(m.module, function_name), \
            "Please define the function with name " + function_name
        function = getattr(m.module, function_name)
        assertEquals(function(*args), expected_result)

    if description is None:
        description = "Check " + function_name + \
            "(" + ", ".join(map(repr, args)) + ") == " + repr(expected_result)
    setDescription(f, description)
    return test(f)

def set_description(d):
    def inner(f):
        setDescription(f, d)
        return f
    return inner


def test_with_args(test_args, description=None, **arg_functions):
    if description is None:
        description = ", ".join(str(i)+"={"+key+"}" for i, key in enumerate(test_args[0]))

    def calc_function_kwargs(values):
        out = {}
        for k, fun in arg_functions.items():
            out[k] = fun(*values)
        return out


    def _inner(function):
        # remove from tests if there
        def make_f(args, kw):
            @test
            @set_description(description.format(*args, **kw))
            def _inner(m):
                function(m, *args, **kw)

        for args in test_args:
            if not isinstance(args, list) and not isinstance(args, tuple):
                args = [args]
            kw = calc_function_kwargs(args)
            make_f(args, kw)
    return _inner


def assertEquals(a, b, template = "Expected {a} but got {b}", **kw):
    if a != b:
        message = template.format(a=a, b=b, **kw)
        raise AssertionError(message)

def assertNContains(input, collection, N, template=None):
    if template is None:
        template = "Expected input to contain {N} of {collection}.\nInput was:{input}"
    count = sum(A in input for A in collection)
    if count != N:
        raise AssertionError(template.format(N=N, count=count, collection=collection, input=repr(input)))

def assertOneContains(input, collection, template=None):
    if template is None:
        template = "Sisend peaks sisaldama maksimaalselt ühte järgnevatest({count}): {collection}.\nSisend oli: {input}"
    assertNContains(input, collection, 1, template)

def function_test(function_name, args, expected, description=None, before_test_call=None):
    args_str = ", ".join(map(repr, args))
    if description is None:
        description = "Test - {function}({args}) == {expected}"
    description = description.format(
        function=function_name, 
        args=args_str, 
        expected=repr(expected))

    @test
    def test_function(m):
        if before_test_call is not None:
            before_test_call(m)
        assert hasattr(m, 'module'), "Programmi täitmine ei lõppenud. Failis ei tohiks olla üleliigseid input() käski"
        assert hasattr(m.module, function_name), "Peab leiduma funktsioon nimega {name}!".format(name=function_name, dict=m.module.__dict__)
        user_function = getattr(m.module, function_name)
        result = user_function(*args)
        assertEquals(result, expected,
            "{function_name}({args_str}) peaks tagastama {expected} aga tagastas {result}",
            expected=expected,
            result=result,
            function_name=function_name,
            args_str=args_str)

    setDescription(test_function, description)
    return test_function

def make_checker(tester, function_name=None):
    if function_name is None:
        function_name = tester.__name__
    return lambda *args, **kw: function_test(function_name, args, tester(*args), **kw)
