"""Generate the code reference pages."""

from pathlib import Path

import mkdocs_gen_files

src = Path(__file__).parent.parent.parent / "hypha"

for path in sorted(src.rglob("*.py")):
    module_path = path.relative_to(src).with_suffix("")
    doc_path = path.relative_to(src).with_suffix(".md")
    full_doc_path = Path("reference", doc_path)

    parts = tuple(module_path.parts)

    if "public" in parts or "tests" in parts:
        continue

    if parts[-1] == "__init__":
        parts = parts[:-1]
        doc_path = doc_path.with_name("index.md")
        full_doc_path = full_doc_path.with_name("index.md")
    elif parts[-1] in ["__main__"]:
        continue

    if len(parts) > 0:
        with mkdocs_gen_files.open(full_doc_path, "w") as fd:
            heading = f"*hypha.{'.'.join(parts)}*"
            identifier = f"::: hypha.{'.'.join(parts)}"
            fd.write(f"{heading}\n{identifier}")

    mkdocs_gen_files.set_edit_path(full_doc_path, path)
