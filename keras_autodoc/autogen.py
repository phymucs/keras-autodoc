import shutil
import pathlib
from inspect import getdoc
from typing import Dict, Union

from .docstring import process_docstring
from .examples import copy_examples
from .get_signatures import get_signature

from . import utils
from .utils import get_type


class DocumentationGenerator:
    """Generates the documentation.

    # Arguments

        pages: A dictionary. The keys are the files' paths, the values
            are lists of strings, functions /classes / methods names
            with dotted access to the object. For example,
            `pages = {'my_file.md': ['keras.layers.Dense']}` is valid.
        project_url: The url pointing to the module directory of your project on
            GitHub. This will be used to make a `[Sources]` link.
        template_dir: Where to put the markdown files which will be copied and
            filled in the destination directory. You should put files like
            `index.md` inside. If you want a markdown file to be filled with
            the docstring of a function, use the `{{autogenerated}}` tag inside,
            and then add the markdown file to the `pages` dictionary.
        example_dir: Where you store examples in your project. Usually standalone
            files with a markdown docstring at the top. Will be inserted in the docs.
    """
    def __init__(self,
                 pages: Dict[str, list] = None,
                 project_url: Union[str, Dict[str, str]] = None,
                 template_dir=None,
                 examples_dir=None):
        self.template_dir = template_dir
        self.pages = pages
        self.project_url = project_url
        self.examples_dir = examples_dir

    def generate(self, dest_dir):
        """Generate the docs.

        # Arguments

            dest_dir: Where to put the resulting markdown files.
        """
        dest_dir = pathlib.Path(dest_dir)
        print("Cleaning up existing sources directory.")
        if dest_dir.exists():
            shutil.rmtree(dest_dir)

        print("Populating sources directory with templates.")
        if self.template_dir:
            shutil.copytree(self.template_dir, dest_dir)

        for file_path, elements in self.pages.items():
            markdown_text = ''
            for element in elements:
                markdown_text += self._render(element)
            utils.insert_in_file(markdown_text, dest_dir / file_path)

        if self.examples_dir is not None:
            copy_examples(self.examples_dir, dest_dir / "examples")

    def process_docstring(self, docstring):
        """Can be overridden."""
        return process_docstring(docstring)

    def process_signature(self, signature):
        """Can be overridden."""
        return signature

    def _render(self, element):
        if isinstance(element, str):
            object_ = utils.import_object(element)
            if utils.ismethod(object_):
                # we remove the modules when displaying the methods
                signature_override = '.'.join(element.split('.')[-2:])
            else:
                signature_override = element
        else:
            signature_override = None
            object_ = element

        return self._render_from_object(object_, signature_override)

    def _render_from_object(self, object_, signature_override: str):
        subblocks = []
        if self.project_url is not None:
            subblocks.append(utils.make_source_link(object_, self.project_url))
        signature = get_signature(object_, signature_override)
        signature = self.process_signature(signature)
        subblocks.append(f"### {object_.__name__} {get_type(object_)}\n")
        subblocks.append(utils.code_snippet(signature))

        docstring = getdoc(object_)
        if docstring:
            docstring = self.process_docstring(docstring)
            subblocks.append(docstring)
        return "\n\n".join(subblocks) + '\n\n----\n\n'
