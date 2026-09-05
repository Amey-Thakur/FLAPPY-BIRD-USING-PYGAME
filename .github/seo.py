#!/usr/bin/env python3
"""Write the page metadata into the built index.html.

Pygbag generates the page, so the head cannot be edited in the repository. It
is written here instead, at build time, from codemeta.json, so the page and the
repository metadata cannot drift apart. The generated title is "source.code",
which says nothing and is what a search result would show, so it is replaced.
"""

import html
import json
import re

BUILT = "dist/index.html"
URL = "https://amey-thakur.github.io/FLAPPY-BIRD-USING-PYGAME/"
IMAGE = ("https://raw.githubusercontent.com/Amey-Thakur/"
         "FLAPPY-BIRD-USING-PYGAME/main/.github/social-preview.png")
TITLE = "Flappy Bird | Amey Thakur"

cm = json.load(open("codemeta.json", encoding="utf-8"))
desc = cm.get("description", "")
kws = ", ".join(k for k in cm.get("keywords", [])
                if k not in ("amey", "ameythakur", "amey-thakur", "ameyarc",
                             "megasatish"))

e = html.escape
tags = """
    <meta name="description" content="{d}">
    <meta name="keywords" content="{k}">
    <meta name="author" content="Amey Thakur">
    <link rel="canonical" href="{u}">

    <meta property="og:type" content="website">
    <meta property="og:title" content="{t}">
    <meta property="og:description" content="{d}">
    <meta property="og:url" content="{u}">
    <meta property="og:image" content="{i}">

    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{t}">
    <meta name="twitter:description" content="{d}">
    <meta name="twitter:image" content="{i}">
""".format(t=e(TITLE), d=e(desc), k=e(kws), u=URL, i=IMAGE)

page = open(BUILT, encoding="utf-8").read()
page = re.sub(r"<title>.*?</title>", "<title>%s</title>" % e(TITLE), page,
              count=1, flags=re.S)
page = page.replace("</head>", tags + "</head>", 1)
open(BUILT, "w", encoding="utf-8").write(page)
print("metadata written: title, description, %d keywords, canonical, "
      "Open Graph, Twitter card" % len(kws.split(",")))
