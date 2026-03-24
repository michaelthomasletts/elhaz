import os
import sys
from datetime import date
from pathlib import Path

import tomlkit

# fetching pyproject.toml
path = Path("../pyproject.toml")

with path.open("r", encoding="utf-8") as f:
    pyproject = tomlkit.parse(f.read())

# adding project root and docs source to path
sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath(".."))

# sphinx config
language = "en"
project = str(pyproject["project"]["name"])  # type: ignore
author = str(pyproject["project"]["maintainers"][0]["name"])  # type: ignore
copyright = f"{date.today().year}, {author}"
release = str(pyproject["project"]["version"])  # type: ignore
source_encoding = "utf-8"
source_suffix = {".rst": "restructuredtext", ".md": "markdown"}
extensions = [
    "sphinx.ext.intersphinx",
    "sphinx_copybutton",
    "sphinxext.opengraph",
    "myst_parser",
]
templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# html config
html_logo = "_static/favicon.ico"
html_favicon = html_logo
html_theme = "furo"
html_static_path = ["_static"]
html_file_suffix = ".html"
htmlhelp_basename = project
html_baseurl = str(pyproject["project"]["urls"]["Documentation"]).rstrip("/")  # type: ignore
repository_url = str(pyproject["project"]["urls"]["Repository"]).rstrip("/")  # type: ignore
repository_branch = "main"
repository_root = Path(__file__).resolve().parent.parent
html_favicon = "_static/favicon.ico"
html_theme_options = {
    "top_of_page_buttons": ["view"],
    "source_view_link": repository_url,
}

# opengraph config
ogp_site_url = html_baseurl
ogp_image = "_static/og.png"
ogp_description_length = 100
ogp_description = str(pyproject["project"]["description"]).rstrip("/")  # type: ignore

# intersphinx
intersphinx_mapping = {
    "boto3": (
        "https://boto3.amazonaws.com/v1/documentation/api/latest/",
        None,
    ),
    "boto3_refresh_session": (
        "https://61418.io/boto3-refresh-session/",
        (
            "https://61418.io/boto3-refresh-session/objects.inv",
            "https://61418.io/boto3-refresh-session/reference/objects.inv",
        ),
    ),
    "python": ("https://docs.python.org/3", None),
}
