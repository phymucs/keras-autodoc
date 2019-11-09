import re
import os
import inspect
import importlib


def count_leading_spaces(s):
    ws = re.search(r"\S", s)
    if ws:
        return ws.start()
    else:
        return 0


def insert_in_file(markdown_text, file_path):
    """Save module page.

    Either insert content into existing page,
    or create page otherwise."""
    if file_path.exists():
        template = file_path.read_text(encoding="utf-8")
        if "{{autogenerated}}" not in template:
            raise RuntimeError(f"Template found for {file_path} but missing "
                               f"{{autogenerated}} tag.")
        markdown_text = template.replace("{{autogenerated}}", markdown_text)
        print("...inserting autogenerated content into template:", file_path)
    else:
        print("...creating new page with autogenerated content:", file_path)
    os.makedirs(file_path.parent, exist_ok=True)
    file_path.write_text(markdown_text, encoding="utf-8")


def code_snippet(snippet):
    return f'```python\n{snippet}\n```\n'


def make_source_link(cls, project_url):
    if isinstance(project_url, dict):
        base_module = cls.__module__.split('.')[0]
        project_url = project_url[base_module]
    path = cls.__module__.replace(".", "/")
    line = inspect.getsourcelines(cls)[-1]
    return (f'<span style="float:right;">'
            f'[[source]]({project_url}/{path}.py#L{line})'
            f'</span>')


def format_classes_list(classes, page_name):
    for i in range(len(classes)):
        if not isinstance(classes[i], (list, tuple)):
            classes[i] = (classes[i], [])
    for class_, class_methods in classes:
        if not inspect.isclass(class_):
            # TODO: add a test for this
            raise TypeError(f'{class_} was given in the class list '
                            f'of {page_name} but {class_} is not a Python class.')
    return classes


def get_class_from_method(meth):
    """See
    https://stackoverflow.com/questions/3589311/
    get-defining-class-of-unbound-method-object-in-python-3/
    25959545#25959545
    """
    if inspect.ismethod(meth):
        for cls in inspect.getmro(meth.__self__.__class__):
            if cls.__dict__.get(meth.__name__) is meth:
                return cls
        meth = meth.__func__  # fallback to __qualname__ parsing
    if inspect.isfunction(meth):
        cls = getattr(inspect.getmodule(meth),
                      meth.__qualname__.split('.<locals>', 1)[0].rsplit('.', 1)[0])
        if isinstance(cls, type):
            return cls
    return getattr(meth, '__objclass__', None)  # handle special descriptor objects


def ismethod(function):
    return get_class_from_method(function) is not None


def import_object(string: str):
    """Import an object from a string.

    The object can be a function, class or method.
    For example: `'keras.layers.Dense.get_weights'` is valid.
    """
    last_object_got = None
    seen_names = []
    for name in string.split('.'):
        seen_names.append(name)
        try:
            last_object_got = importlib.import_module('.'.join(seen_names))
        except ModuleNotFoundError:
            last_object_got = getattr(last_object_got, name)
    return last_object_got
