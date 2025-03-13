import functools
from functools import cached_property
from inspect import getmembers, isclass, isfunction, signature
from typing import Any, Callable, Optional

from kensho_finance import kfinance, llm_tools


MODULES = [kfinance, llm_tools]
TAB = "    "


def _func_doc(func: Callable, indent: int = 1) -> str:
    name_indent = f"{TAB}" * indent
    doc_indent = f"{TAB}" * (indent + 1)
    is_property = isinstance(func, cached_property)
    if is_property and hasattr(func, "func"):
        func = func.func
    func_name = func.__name__
    func_doc = func.__doc__
    """
    Code blocks are generated in Sphinx from rst blocks in the format of :: followed by indented lines.
    The doc string cannot have indented lines without upsetting the linter and potentially affecting how the docstring appears in other places,
    so the indents are made inside of this script.
    """
    func_doc_lines = func_doc.split("\n") if func_doc is not None else None
    if func_doc_lines is not None and func_doc_lines[0][-2:] == "::":
        func_doc_lines[1] = func_doc_lines[1] + "\n"
        for i in range(1, len(func_doc_lines)):
            func_doc_lines[i] = f"{TAB}{TAB}" + func_doc_lines[i]
        func_doc = "\n".join(func_doc_lines)
    func_signature = signature(func)
    if is_property:
        return f"{name_indent}.. py:attribute:: {func_name}\n\n{doc_indent}{func_doc}"
    return f"{name_indent}.. py:function:: {func_name}{func_signature}\n\n{doc_indent}{func_doc}"


def _func_in_module(module_name: Optional[str] = None) -> Callable:
    def _helper(member: Any) -> bool:
        if not (
            isfunction(member)
            or isinstance(member, cached_property)
            or isinstance(member, functools._lru_cache_wrapper)  # noqa: SLF001
        ):
            return False
        return (
            module_name is None or member.__module__ == module_name
        ) and member.__doc__ is not None

    return _helper


def _cls_doc(cls: Any) -> str:
    cls_name = cls.__name__
    cls_doc = cls.__doc__
    cls_doc_list = [f".. py:class:: {cls_name}\n\n{TAB}{cls_doc}"]
    cls_funcs = getmembers(cls, _func_in_module())
    cls_func_doc_list = list(map(lambda f: _func_doc(f[1]), cls_funcs))
    return "\n\n".join(cls_doc_list + cls_func_doc_list)


def _class_in_module(module_name: str) -> Callable:
    def _helper(member: Any) -> bool:
        if not isclass(member):
            return False
        return member.__module__ == module_name and member.__doc__ is not None

    return _helper


def _module_doc(module: Any) -> str:
    classes = getmembers(module, _class_in_module(module.__name__))
    funcs = getmembers(module, _func_in_module(module.__name__))
    classes_doc_list = list(map(lambda c: _cls_doc(c[1]), classes))
    funcs_doc_list = list(map(lambda mf: _func_doc(mf[1], indent=0), funcs))
    return "\n\n".join(classes_doc_list + funcs_doc_list)


for module in MODULES:
    module_name = module.__name__
    module_short_name = module_name[module_name.find(".") + 1 :]
    mod_doc = _module_doc(module)
    with open(f"docs/{module_short_name}.rst", "w+") as f:
        f.write(f"{module_short_name}\n")
        f.write("#####################\n\n")
        f.write(mod_doc)
        f.close()

with open(f"docs/index.rst", "w+") as f:
    f.write(f"Index\n")
    f.write("#####################\n\n")
    f.write("Documentation page for Kensho Finance library.\n\n")
    f.write(f".. toctree::\n\n{TAB}")
    module_names = map(lambda m: m.__name__, MODULES)
    module_short_names = list(map(lambda mn: mn[mn.find(".") + 1 :], module_names))
    module_entries = f"\n{TAB}".join(module_short_names)
    f.write(module_entries)
    f.close()
