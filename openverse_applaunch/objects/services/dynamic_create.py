"""
dynamic_functions.py

Module for dynamically creating and executing functions based on configuration.

This module provides:
  1. A way to define function configurations (parameter names and body)
  via dictionaries.
  2. Dynamic generation of functions at runtime based on those configurations.
  3. Automatic argument binding when calling the generated functions.

Usage example:
    configurations = [
        {
            "params": ["a", "b"],
            "body": "return a + b"
        },
        {
            "params": ["text1", "text2", "separator"],
            "body": "return text1 + separator + text2"
        },
        {
            "params": ["base", "exponent"],
            "body": "return base * exponent"
        },
        {
            "params": ["*args", "**kwargs"],
            "body": (
                "result = sum(args)\n"
                "for key, value in kwargs.items():\n"
                "    result += value\n"
                "return result"
            )
        },
    ]
    arguments = {
        "a": 1,
        "b": 2,
        "text1": "Hello, World!",
        "text2": "!",
        "separator": " ",
        "base": 1,
        "exponent": 10,
    }

    funcs = create_dynamic_functions(configurations)
    for f in funcs:
        execute_dynamic_function(f, arguments)
"""

import inspect
from typing import Any, Callable, MutableMapping, Optional, TypeAlias, TypedDict

from tools_openverse import setup_logger

# setup logger
logger = setup_logger()


# ----- Type Definitions -----
class FuncConfig(TypedDict, total=False):
    """
    Configuration for a single dynamic function.

    Keys:
        params: List of parameter names for the function (
            e.g. ["a", "b"] or ["*args", "**kwargs"]
        ).
        body:   Either a string with the function body or a list of strings,
        each representing a line of code.
    """
    params: list[str]
    body: str | list[str]


ConfigType: TypeAlias = list[FuncConfig]
ListFuncType: TypeAlias = list[Callable[..., Any]]
FuncType: TypeAlias = Callable[..., Any]


# ----- Module Functions -----
# def create_dynamic_functions(func_configurations: ConfigType) -> ListFuncType:
#     """
#     Creates a list of functions based on the provided configuration.

#     Each item in `func_configurations` is a dictionary with:
#       - "params": list of parameter names for the dynamic function.
#       - "body":   a string or list of strings constituting the function body.

#     Returns a list of functions in the same order as the configurations. All
#     generated functions will be named "dynamic_function" internally.

#     Args:
#         func_configurations (ConfigType): List of configurations
#         for function generation.

#     Returns:
#         ListFuncType: List of generated functions.
#     """
#     generated_funcs: ListFuncType = []

#     for idx, config in enumerate(func_configurations):
#         params_list = config.get("params", [])
#         raw_body = config.get("body", "")

#         # If body is given as a list of lines, join them into one string with newlines
#         if isinstance(raw_body, list):
#             body_code = "\n".join(raw_body)
#         else:
#             body_code = raw_body

#         # Construct the parameter string, e.g. "a, b, *args, **kwargs"
#         params_str = ", ".join(params_list)

#         # Build the full source code for the function
#         func_lines = [f"def dynamic_function({params_str}):"]
#         for line in body_code.split("\n"):
#             func_lines.append(f"    {line}")

#         func_code = "\n".join(func_lines)

#         logger.debug("Generated code for function #%d:\n%s", idx + 1, func_code)

#         # Prepare namespaces for exec
#         local_vars: dict[str, Any] = {}
#         global_vars = globals().copy()

#         try:
#             exec(func_code, global_vars, local_vars)
#             dynamic_func = local_vars["dynamic_function"]
#             generated_funcs.append(dynamic_func)
#             logger.info("Successfully created dynamic function #%d", idx + 1)
#         except Exception as exc:
#             logger.error(
#                 "Error compiling dynamic function #%d: %s", idx + 1, exc
#             )
#             # Skip invalid configurations
#             continue

#     return generated_funcs


def execute_dynamic_func(
    function: FuncType, available_args: MutableMapping[str, Any]
) -> Optional[Any]:
    """
    Invokes a dynamically created function, automatically supplying arguments.

    This function examines the named parameters in `function`’s signature (excluding
    *args and **kwargs) and for each parameter:
      - If the parameter name exists in `available_args`, its value is taken from
        `available_args` and passed to the target function.
      - Any entries in `available_args` that do not match the function’s parameters
        are ignored when calling the function.

    After a successful call, it removes from `available_args` any keys that were
    passed into `function`.

    Args:
        function (FuncType): The function to be called.
        available_args (MutableMapping[str, Any]): A dictionary containing all
            possible argument values (key = parameter name, value = argument value).

    Returns:
        Any: The result returned by `function`, or None if an error occurred.
    """
    sig = inspect.getfullargspec(function)
    call_args: dict[str, Any] = {}

    for arg_name in sig.args:
        if arg_name in available_args:
            call_args[arg_name] = available_args.get(arg_name)

    try:
        logger.debug("All available arguments: %s", available_args)
        logger.debug("Calling function '%s' with sig: %s", function.__name__, sig.args)
        logger.debug("Calling function '%s' with arguments: %s",
                     function.__name__, call_args)
        logger.debug("")
        result_func = function(**call_args)
        if result_func:
            for arg in call_args:
                available_args.pop(arg)

        logger.info("Result of '%s': %s", function.__name__, result_func)
        return result_func
    except Exception as exc:
        logger.error("Error while calling function '%s': %s", function.__name__, exc)
        return None


# ----- Example Usage -----
if __name__ == "__main__":
    # Sample arguments that can be used by any function
    arguments = {
        "a": 1,
        "b": 2,
        "text1": "Hello, World!",
        "text2": "!",
        "separator": " ",
        "base": 1,
        "exponent": 10,
    }

    configurations: ConfigType = [
        {
            "params": ["a", "b"],
            "body": "return a + b",
        },
        {
            "params": ["text1", "text2", "separator"],
            "body": "return text1 + separator + text2",
        },
        {
            "params": ["base", "exponent"],
            "body": "return base * exponent",
        },
        {
            "params": ["*args", "**kwargs"],
            "body": [
                "result = sum(args)",
                "for key, value in kwargs.items():",
                "    result += value",
                "return result",
            ],
        },
    ]

    # Step 1: Generate functions
    # funcs = create_dynamic_functions(configurations)

    # Step 2: Execute each generated function with available arguments
    # for func in funcs:
    #     execute_dynamic_func(func, arguments)
