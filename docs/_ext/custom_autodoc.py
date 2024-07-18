# SPDX-FileCopyrightText: 2024 Thomas Touhey
# SPDX-License-Identifier: GPL-3.0-only
"""Sphinx extension to remove the first line from module docstrings."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sphinx.application import Sphinx


def remove_first_line_in_module_docstring(
    _app: Sphinx,
    what: str,
    _name: str,
    _obj: Any,
    _options: Any,
    lines: list[str],
) -> None:
    """Remove the first line from the docstring.

    This is because the first line of the docstring is summed up in the
    document title, before the module autodoc.
    """
    if what != "module" or not lines:
        return

    for i in range(1, len(lines)):
        if not lines[i]:
            lines[: i + 1] = []
            return

    lines[:] = []


def setup(app: Sphinx) -> None:
    """Set up the extension."""
    app.connect(
        "autodoc-process-docstring",
        remove_first_line_in_module_docstring,
    )
