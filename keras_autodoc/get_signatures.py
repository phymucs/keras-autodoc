import warnings
from sphinx.util.inspect import Signature
from . import utils
import black
import inspect


def get_signature_start(function):
    """For the Dense layer, it should return the string 'keras.layers.Dense'"""
    if utils.ismethod(function):
        prefix = f'{utils.get_class_from_method(function).__name__}.'
    else:
        try:
            prefix = f'{function.__module__}.'
        except AttributeError:
            warnings.warn(f'function {function} has no module. '
                          f'It will not be included in the signature.')
            prefix = ''

    return f'{prefix}{function.__name__}'


def get_signature_end(function):
    signature_end = Signature(function).format_args()
    if utils.ismethod(function):
        signature_end = signature_end.replace('(self, ', '(')
        signature_end = signature_end.replace('(self)', '()')
    return signature_end


def get_function_signature(function, override=None):
    if override is None:
        signature_start = get_signature_start(function)
    else:
        signature_start = override
    signature_end = get_signature_end(function)
    return format_signature(signature_start, signature_end)


def get_class_signature(cls, override=None):
    if override is None:
        signature_start = f'{cls.__module__}.{cls.__name__}'
    else:
        signature_start = override
    signature_end = get_signature_end(cls.__init__)
    return format_signature(signature_start, signature_end)


def get_signature(object_, override=None):
    if inspect.isclass(object_):
        return get_class_signature(object_, override)
    else:
        return get_function_signature(object_, override)


def format_signature(signature_start: str, signature_end: str):
    """pretty formatting to avoid long signatures on one single line"""

    # first, we make it look like a real function declaration.
    fake_signature_start = 'x' * len(signature_start)
    fake_signature = fake_signature_start + signature_end
    fake_python_code = f'def {fake_signature}:\n    pass\n'

    # we format with black
    mode = black.FileMode(line_length=110)
    formatted_fake_python_code = black.format_str(fake_python_code, mode=mode)

    # we make the final, multiline signature
    new_signature_end = extract_signature_end(formatted_fake_python_code)
    return signature_start + new_signature_end


def extract_signature_end(function_definition):
    start = function_definition.find('(')
    stop = function_definition.rfind(')')
    return function_definition[start: stop + 1]
