"""
Generate reference pages for the API. Uses concurrency to speed things up, and
ensures that generation of references pages in enabled in the environment via
the `GEN_REF_PAGES` var.

For more info on how this is done, see:
https://mkdocstrings.github.io/recipes/#automatic-code-reference-pages
"""

import concurrent.futures
import os
from pathlib import Path

import mkdocs_gen_files

# The code source directory
src = Path(__file__).parent.parent.parent / "hypha"
skip_folders = ["public", "tests", "migrations"]


def process_path(path):
    module_path = path.relative_to(src).with_suffix("")
    doc_path = path.relative_to(src).with_suffix(".md")
    full_doc_path = Path("references/API", doc_path)
    parts = tuple(module_path.parts)
    # Don't document any code in public/ or tests/ directories
    for skip_folder in skip_folders:
        if skip_folder in parts:
            return
    if parts[-1] == "__init__":
        parts = parts[:-1]
        doc_path = doc_path.with_name("index.md")
        full_doc_path = full_doc_path.with_name("index.md")
    elif parts[-1] in ["__main__"]:
        return
    # Create the required files on build with mkdocs_gen_files, see:
    # https://oprypin.github.io/mkdocs-gen_files/
    if len(parts) > 0:
        with mkdocs_gen_files.open(full_doc_path, "w") as fd:
            identifier = f"::: hypha.{'.'.join(parts)}"
            fd.write(identifier)
    mkdocs_gen_files.set_edit_path(full_doc_path, path)


def generate_pages():
    with concurrent.futures.ThreadPoolExecutor() as executor:
        list(executor.map(process_path, sorted(src.rglob("*.py"))))


# Confirm `GEN_REF_PAGES` is enabled in the env
if os.getenv("GEN_REF_PAGES", False):
    generate_pages()
