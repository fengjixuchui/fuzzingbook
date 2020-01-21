#!/usr/bin/env python3
# Expand elements in generated HTML
# Usage: post-html.py CHAPTER_NAME CHAPTER_1 CHAPTER_2 ...

# Note: I suppose this could also be done using Jinja2 templates and ipypublish,
# but this thing here works pretty well.
# If you'd like to convert this into some more elegant framework,
# implement it and send me a pull request -- AZ

import argparse
import os.path
import time
import datetime
import re
import sys
import io
import html

try:
    import nbformat
    have_nbformat = True
except:
    have_nbformat = False
    


# Some fixed strings
booktitle = "The Fuzzing Book"
authors = "Andreas Zeller, Rahul Gopinath, Marcel Böhme, Gordon Fraser, and Christian Holler"
site_html = "https://www.fuzzingbook.org/"
github_html = "https://github.com/uds-se/fuzzingbook/"
notebook_html = "https://mybinder.org/v2/gh/uds-se/fuzzingbook/master?filepath=docs/"

# Menus
# For icons, see https://fontawesome.com/cheatsheet
menu_start = r"""
<nav>
<div id="cssmenu">
  <ul>
     <li class="has-sub"><a href="#"><span title="__BOOKTITLE__"><i class="fa fa-fw fa-bars"></i> </span><span class="menu_1">__BOOKTITLE_BETA__</span></a>
        <ol>
           <__STRUCTURED_ALL_CHAPTERS_MENU__>
           <li><a href="__SITE_HTML__html/00_Index.html">Index (beta)</a></i></li>
        </ol>
     </li>
     <li class="has-sub"><a href="#"><span title="__CHAPTER_TITLE__"><i class="fa fa-fw fa-list-ul"></i></span> <span class="menu_2">__CHAPTER_TITLE_BETA__</span></a>
           <__ALL_SECTIONS_MENU__>
     </li>
     """

menu_end = r"""
     <li class="has-sub"><a href="#"><span title="Share"><i class="fa fa-fw fa-comments"></i> </span> <span class="menu_4">Share</span></a>
        <ul>
            <li><a href="__SHARE_TWITTER__" target="popup" __TWITTER_ONCLICK__><i class="fa fa-fw fa-twitter"></i> Share on Twitter</a>
            <li><a href="__SHARE_FACEBOOK__" target="popup" __FACEBOOK_ONCLICK__><i class="fa fa-fw fa-facebook"></i> Share on Facebook</a>
            <li><a href="__SHARE_MAIL__"><i class="fa fa-fw fa-envelope"></i> Share by Email</a>
            <li><a href="#citation" id="cite" onclick="revealCitation()"><i class="fa fa-fw fa-mortar-board"></i> Cite</a>
        </ul>
     </li>
     <li class="has-sub"><a href="#"><span title="Help"><i class="fa fa-fw fa-question-circle"></i></span> <span class="menu_5">Help</span></a>
        <ul>
          <li><a href="__SITE_HTML__#Troubleshooting"><i class="fa fa-fw fa-wrench"></i> Troubleshooting</a></li>
          <li><a href="https://docs.python.org/3/tutorial/" target=_blank><i class="fa fa-fw fa-question-circle"></i> Python Tutorial</a>
          <li><a href="https://www.dataquest.io/blog/jupyter-notebook-tutorial/" target=_blank><i class="fa fa-fw fa-question-circle"></i> Jupyter Notebook Tutorial</a>
          <li><a href="__GITHUB_HTML__issues/" target="_blank"><i class="fa fa-fw fa-commenting"></i> Report an Issue</a></li>
        </ul>
     </li>
  </ul>
</div>
</nav>
"""

site_header_template = menu_start + r"""
     <li class="has-sub"><a href="#"><span title="Resources"><i class="fa fa-fw fa-cube"></i> </span><span class="menu_3">Resources</span></a>
     <ul>
     <li><a href="__CHAPTER_NOTEBOOK_IPYNB__" target="_blank" class="edit_as_notebook"><i class="fa fa-fw fa-edit"></i> Edit Notebooks</a></li>
     <li><a href="__SITE_HTML__dist/fuzzingbook-code.zip"><i class="fa fa-fw fa-cube"></i> All Code (.zip)</a></li>
     <li><a href="__SITE_HTML__dist/fuzzingbook-notebooks.zip"><i class="fa fa-fw fa-cube"></i> All Notebooks (.zip)</a></li>
     <li><a href="__GITHUB_HTML__" target="_blank"><i class="fa fa-fw fa-github"></i> Project Page</a></li>
     <li><a href="html/ReleaseNotes.html" target="_blank"><i class="fa fa-fw fa-calendar"></i> Release Notes</a></li>
     </ul>
     </li>
""" + menu_end

# Chapters
chapter_header_template = menu_start + r"""
     <li class="has-sub"><a href="#"><span title="Resources"><i class="fa fa-fw fa-cube"></i> </span><span class="menu_3">Resources</span></a>
     <ul>
     <li><a href="__CHAPTER_NOTEBOOK_IPYNB__" target="_blank" class="edit_as_notebook"><i class="fa fa-fw fa-edit"></i> Edit as Notebook</a></li>
     <li><a href="__SITE_HTML__slides/__CHAPTER__.slides.html" target="_blank"><i class="fa fa-fw fa-video-camera"></i> View Slides</a></li>
     <li><a href="__SITE_HTML__code/__CHAPTER__.py"><i class="fa fa-fw fa-download"></i> Download Code (.py)</a></li>
     <li><a href="__SITE_HTML__notebooks/__CHAPTER__.ipynb"><i class="fa fa-fw fa-download"></i> Download Notebook (.ipynb)</a></li>
     <li><a href="__SITE_HTML__dist/fuzzingbook-code.zip"><i class="fa fa-fw fa-cube"></i> All Code (.zip)</a></li>
     <li><a href="__SITE_HTML__dist/fuzzingbook-notebooks.zip"><i class="fa fa-fw fa-cube"></i> All Notebooks (.zip)</a></li>
     <li><a href="__GITHUB_HTML__" target="_blank"><i class="fa fa-fw fa-github"></i> Project Page</a></li>
     <li><a href="ReleaseNotes.html" target="_blank"><i class="fa fa-fw fa-calendar"></i> Release Notes</a></li>
     </ul>
     </li>
     """ + menu_end


# Footers
site_citation_template = r"""
<div id="citation" class="citation" style="display: none;">
<a name="citation"></a>
<h2>How to Cite this Work</h2>
<p>
__AUTHORS__: "<a href="__SITE_HTML__">__BOOKTITLE__</a>".  Retrieved __DATE__.
</p>
<pre>
@incollection{fuzzingbook__YEAR__:__CHAPTER__,
    author = {__AUTHORS_BIBTEX__},
    booktitle = {__BOOKTITLE__},
    title = {__BOOKTITLE__},
    year = {__YEAR__},
    publisher = {Saarland University},
    howpublished = {\url{__SITE_HTML__}},
    note = {Retrieved __DATE__},
    url = {__SITE_HTML__},
    urldate = {__DATE__}
}
</pre>
</div>
"""

chapter_citation_template = r"""
<div id="citation" class="citation" style="display: none;">
<a name="citation"></a>
<h2>How to Cite this Work</h2>
<p>
__AUTHORS__: "<a href="__CHAPTER_HTML__">__CHAPTER_TITLE__</a>".  In __AUTHORS__ (eds.), "<a href="__SITE_HTML__">__BOOKTITLE__</a>", <a href="__CHAPTER_HTML__">__CHAPTER_HTML__</a>.  Retrieved __DATE__.
</p>
<pre>
@incollection{fuzzingbook__YEAR__:__CHAPTER__,
    author = {__AUTHORS_BIBTEX__},
    booktitle = {__BOOKTITLE__},
    title = {__CHAPTER_TITLE__},
    year = {__YEAR__},
    publisher = {Saarland University},
    howpublished = {\url{__CHAPTER_HTML__}},
    note = {Retrieved __DATE__},
    url = {__CHAPTER_HTML__},
    urldate = {__DATE__}
}
</pre>
</div>
"""

common_footer_template = r"""
<p class="imprint">
<img style="float:right" src="https://i.creativecommons.org/l/by-nc-sa/4.0/88x31.png" alt="Creative Commons License">
The content of this project is licensed under the
<a href="https://creativecommons.org/licenses/by-nc-sa/4.0/" target=_blank>Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License</a>.
The source code that is part of the content, as well as the source code used to format and display that content is licensed under the <a href="https://github.com/github/choosealicense.com/blob/gh-pages/LICENSE.md">MIT License</a>.
<a href="__GITHUB_HTML__commits/master/notebooks/__CHAPTER__.ipynb" target=_blank)>Last change: __DATE__</a> &bull; 
<a href="#citation" id="cite" onclick="revealCitation()">Cite</a> &bull;
<a href="https://www.uni-saarland.de/en/footer/dialogue/legal-notice.html" target=_blank>Imprint</a>
</p>

<iframe src="http://fuzzingbook.cispa.saarland/rVBkxhK1wuOrGfGe1HZL/__CHAPTER_TITLE__" style="width:0;height:0;border:0; border:none;"></iframe>

<script>
function revealCitation() {
    var c = document.getElementById("citation");
    c.style.display = "block";
}
</script>
"""

chapter_footer_template = common_footer_template + chapter_citation_template
site_footer_template = common_footer_template + site_citation_template

from nbdepend import get_text_contents, get_title

def get_description(notebook):
    """Return the first 2-4 sentences from a notebook file, after the title"""
    contents = get_text_contents(notebook)
    match = re.search(r'^# .*$([^#]*)^#', contents, re.MULTILINE)
    if match is None:
        desc = contents
    else:
        desc = match.group(1).replace(r'\n', '').replace('\n', '')
    desc = re.sub(r"\]\([^)]*\)", "]", desc).replace('[', '').replace(']', '')
    desc = re.sub(r"[_*]", "", desc)
    # print("Description", desc.encode('utf-8'))
    return desc

def get_sections(notebook):
    """Return the section titles from a notebook file"""
    contents = get_text_contents(notebook)
    matches = re.findall(r'^(# .*)', contents, re.MULTILINE)
    if len(matches) >= 5:
        # Multiple top sections (book?) - use these
        pass
    else:
        # Use sections and subsections instead
        matches = re.findall(r'^(###? .*)', contents, re.MULTILINE)

    sections = [match.replace(r'\n', '') for match in matches]
    # print("Sections", repr(sections).encode('utf-8'))

    # Filter out second synopsis section
    if '## Synopsis' in sections:
        sections = ['## Synopsis'] + [sec for sec in sections if sec != '## Synopsis']
    return sections

    
def anchor(title):
    """Return an anchor '#a-title' for a title 'A title'"""
    return '#' + title.replace(' ', '-')


def decorate(section, depth):
    if depth != 2:
        return section
    
    if section == "Synopsis":
        section = '<i class="fa fa-fw fa-map"></i> ' + section
    elif section == "Lessons Learned":
        section = '<i class="fa fa-fw fa-trophy"></i> ' + section
    elif section == "Next Steps":
        section = '<i class="fa fa-fw fa-arrows"></i> ' + section
    elif section == "Background":
        section = '<i class="fa fa-fw fa-mortar-board"></i> ' + section
    elif section == "Exercises":
        section = '<i class="fa fa-fw fa-edit"></i> ' + section
    else:
        section = '&nbsp;&bull;&nbsp;&nbsp; ' + section

    return section

# Authors
def bibtex_escape(authors):
    """Return list of authors in BibTeX-friendly form"""
    tex_escape_table = {
        "ä": r'{\"a}',
        "ö": r'{\"o}',
        "ü": r'{\"u}',
        "Ä": r'{\"A}',
        "Ö": r'{\"O}',
        "Ü": r'{\"U}',
        "ß": r'{\ss}'
    }
    return "".join(tex_escape_table.get(c,c) for c in authors)

assert bibtex_escape("Böhme") == r'B{\"o}hme'

authors_bibtex = bibtex_escape(authors).replace(", and ", " and ").replace(", ", " and ")


# The other way round
# Use "grep '\\' fuzzingbook.bib" to see accents currently in use
def bibtex_unescape(contents):
    """Fix TeX escapes introduced by BibTeX"""
    tex_unescape_table = {
        r'{\"a}': "ä",
        r'{\"o}': "ö",
        r'{\"u}': "ü",
        r'{\"i}': "ï",
        r'{\"e}': "ë",
        r'{\"A}': "Ä",
        r'{\"O}': "Ö",
        r'{\"U}': "Ü",
        r'{\ss}': "ß",
        r'{\`e}': "è",
        r'{\'e}': "é",
        r'{\`a}': "à",
        r'{\'a}': "á",
        r'{\`i}': "ì",
        r'{\'i}': "í",
        r'{\`o}': "ò",
        r'{\'o}': "ó",
        r'{\`u}': "ù",
        r'{\'u}': "ú",
        r'{\d{s}}': "ṣ",
        r'{\d{n}}': "ṇ",
        r'{\d{t}}': "ṭ",
        r'{\=a}': "ā",
        r'{\=i}': "ī"
    }
    for key in tex_unescape_table:
        contents = contents.replace(key, tex_unescape_table[key])
    return contents

assert bibtex_unescape(r"B{\"o}hme") == 'Böhme'
assert bibtex_unescape(r"P{\`e}zze") == 'Pèzze'



# Imports are in <span class="nn">NAME</span>
RE_IMPORT = re.compile(r'<span class="nn">([^<]+)</span>')

# Add links to imports
def add_links_to_imports(contents):
    imports = re.findall(RE_IMPORT, contents)
    for module in imports:
        link = None
        if module.startswith("fuzzingbook_utils"):
            link = "https://github.com/uds-se/fuzzingbook/tree/master/notebooks/fuzzingbook_utils"
        elif module == "requests":
            link = "http://docs.python-requests.org/en/master/"
        elif module.startswith("IPython"):
            # Point to IPython doc
            link = "https://ipython.readthedocs.io/en/stable/api/generated/" + module + ".html"
        elif module.startswith("selenium"):
            # Point to Selenium doc
            link = "https://selenium-python.readthedocs.io/"
        elif module.startswith("fuzzingbook"):
            # Point to notebook
            link = module[module.find('.') + 1:] + '.html'
        elif module[0].islower():
            # Point to Python doc
            link = "https://docs.python.org/3/library/" + module + ".html"
        else:
            # Point to notebook
            link = module + '.html'

        if link is not None:
            contents = contents.replace(r'<span class="nn">' + module + r'</span>',
                r'<span class="nn"><a href="' + link 
                + r'" class="import" target="_blank">' 
                + module + r"</a>" + r'</span>')

    return contents


# Sharing
def cgi_escape(text):
    """Produce entities within text."""
    cgi_escape_table = {
        " ": r"%20",
        "&": r"%26",
        '"': r"%22",
        "'": r"%27",
        ">": r"%3e",
        "<": r"%3c",
        ":": r"%3a",
        "/": r"%2f",
        "?": r"%3f",
        "=": r"%3d",
    }
    return "".join(cgi_escape_table.get(c,c) for c in text)

    
# Highlight Synopsis
def highlight_synopsis(text):
    synopsis_start = text.find('<h2 id="Synopsis">')
    if synopsis_start < 0:
        return text  # No synopsis

    synopsis_end = text.find('<div class="input_markdown">', synopsis_start + 1)
    if synopsis_end < 0:
        return text  # No synopsis
        
    text = (text[:synopsis_start] + 
        '<div class="synopsis">' +  
        text[synopsis_start:synopsis_end] +
        '</div>\n\n' +  
        text[synopsis_end:])
    
    # Strip original synopsis
    orig_synopsis_start = text.find('<h2 id="Synopsis">', synopsis_end + 1)
    orig_synopsis_end = text.find('<h2 ', orig_synopsis_start + 1)
    
    text = (text[:orig_synopsis_start] + text[orig_synopsis_end:])

    return text

# Handle Details switchers
# Cells with <details> or </details> are moved to top level, allowing to
# switch contents between them on or off
# note: *? is non-greedy, minimal match
RE_BEGIN_DETAILS = re.compile(r'''
<div[^>]*?>[^<]*?  # four divs
<div[^>]*?>[^<]*?
<div[^>]*?>[^<]*?
<div[^>]*?>[^<]*?
<p>[^<]*?
(?P<cell><details>.*?)  # our group
</p>[^<]*?
</div>[^<]*?      # four closing divs
</div>[^<]*?
</div>[^<]*?
</div>''', re.DOTALL | re.VERBOSE)

RE_END_DETAILS = re.compile(r'''
<div[^>]*?>[^<]*?  # four divs
<div[^>]*?>[^<]*?
<div[^>]*?>[^<]*?
<div[^>]*?>[^<]*?
<p>[^<]*?
(?P<cell></details>).*?  # our group
</p>[^<]*?
</div>[^<]*?      # four closing divs
</div>[^<]*?
</div>[^<]*?
</div>''', re.DOTALL | re.VERBOSE)

def fix_detail_switchers(text):
    text = text.replace('&lt;details&gt;',  '<details>')
    text = text.replace('&lt;/details&gt;', '</details>')

    text = RE_BEGIN_DETAILS.sub(r'\g<cell>', text)
    text = RE_END_DETAILS.sub(r'\g<cell>', text)
    return text
    
text1 = '''
Some stuff to begin with

<div class="input_markdown">
<div class="cell border-box-sizing text_cell rendered">
<div class="inner_cell">
<div class="text_cell_render border-box-sizing rendered_html"><p><details>
    <summary>How does this work?</summary></p>
</div>
</div>
</div>
</div>

<div class="input_markdown">
<div class="cell border-box-sizing text_cell rendered">
<div class="inner_cell">
<div class="text_cell_render border-box-sizing rendered_html">
Some more stuff
</div>
</div>
</div>
</div>

<div class="input_markdown">
<div class="cell border-box-sizing text_cell rendered">
<div class="inner_cell">
<div class="text_cell_render border-box-sizing rendered_html"><p>&lt;/details&gt;</p>
</div>
</div>
</div>
</div>

Some other stuff
'''

# print(fix_detail_switchers(text1))
# sys.exit(0)


# Process arguments
parser = argparse.ArgumentParser()
parser.add_argument("--home", help="omit links to notebook, code, and slides", action='store_true')
parser.add_argument("--include-ready", help="include ready chapters", action='store_true')
parser.add_argument("--include-todo", help="include work-in-progress chapters", action='store_true')
parser.add_argument("--menu-prefix", help="prefix to html files in menu")
parser.add_argument("--public-chapters", help="List of public chapters")
parser.add_argument("--ready-chapters", help="List of ready chapters")
parser.add_argument("--todo-chapters", help="List of work-in-progress chapters")
parser.add_argument("--new-chapters", help="List of new chapters")
parser.add_argument("chapter", nargs=1)
args = parser.parse_args()

# Get template elements
chapter_html_file = args.chapter[0]
chapter = os.path.splitext(os.path.basename(chapter_html_file))[0]
chapter_notebook_file = os.path.join("notebooks", chapter + ".ipynb")
notebook_modification_time = os.path.getmtime(chapter_notebook_file)    
notebook_modification_datetime = datetime.datetime.fromtimestamp(notebook_modification_time) \
    .astimezone().isoformat(sep=' ', timespec='seconds')
notebook_modification_year = repr(datetime.datetime.fromtimestamp(notebook_modification_time).year)

# Get list of chapters
if args.public_chapters is not None:
    public_chapters = args.public_chapters.split()
else:
    public_chapters = []

if args.include_ready and args.ready_chapters is not None:
    ready_chapters = args.ready_chapters.split()
else:
    ready_chapters = []

if args.include_todo and args.todo_chapters is not None:
    todo_chapters = args.todo_chapters.split()
else:
    todo_chapters = []
    
new_chapters = args.new_chapters.split()
beta_chapters = ready_chapters + todo_chapters
all_chapters = public_chapters # + beta_chapters
include_beta = args.include_ready or args.include_todo

new_suffix = ' <strong class="new_chapter">&bull;</strong>'
todo_suffix = '<i class="fa fa-fw fa-wrench"></i>'
ready_suffix = '<i class="fa fa-fw fa-warning"></i>'

booktitle_beta = booktitle
if include_beta:
    booktitle_beta += "&nbsp;" + todo_suffix

menu_prefix = args.menu_prefix
if menu_prefix is None:
    menu_prefix = ""

if args.home:
    header_template = site_header_template
    footer_template = site_footer_template
else:
    header_template = chapter_header_template
    footer_template = chapter_footer_template
    
# Popup menus
twitter_onclick = r"""
onclick="window.open('__SHARE_TWITTER__','popup','width=600,height=600'); return false;"
"""
facebook_onclick = r"""
onclick="window.open('__SHARE_FACEBOOK__','popup','width=600,height=600'); return false;"
"""
if args.home:
    # Including the Twitter timeline already creates a popup
    twitter_onclick = ""

# Set base names
if include_beta:
    site_html += "beta/"

# Book image
bookimage = site_html + "html/PICS/wordcloud.png"

# Binder
if include_beta:
    notebook_html += "beta/"
notebook_html += "notebooks/"

# Construct sections menu

basename = os.path.splitext(os.path.basename(chapter_html_file))[0]
chapter_ipynb_file = os.path.join("notebooks", basename + ".ipynb")

all_sections_menu = ""
sections = get_sections(chapter_ipynb_file)
current_depth = 1

for section in sections:
    depth = section.count('#')
    while section.startswith('#') or section.startswith(' '):
        section = section[1:]

    if depth == current_depth:
        all_sections_menu += '</li>'
    
    if depth > current_depth:
        all_sections_menu += "<ul>" * (depth - current_depth)

    if depth < current_depth:
        all_sections_menu += "</ul></li>" * (current_depth - depth)

    all_sections_menu += '<li class="has-sub"><a href="%s">%s</a>\n' % (anchor(section), decorate(section, depth))
    current_depth = depth

while current_depth > 1:
    all_sections_menu += '</ul></li>'
    current_depth -= 1


# Construct chapter menu

if args.home:
    chapter_html = site_html
    chapter_notebook_ipynb = notebook_html + "00_Table_of_Contents.ipynb"
else:
    chapter_html = site_html + "html/" + basename + ".html"
    chapter_notebook_ipynb = notebook_html + basename + ".ipynb"

chapter_title = get_title(chapter_ipynb_file)
# if chapter_ipynb_file in new_chapters:
#     chapter_title += " " + new_suffix

chapter_title_beta = chapter_title
is_todo_chapter = include_beta and chapter_ipynb_file in todo_chapters
is_ready_chapter = include_beta and chapter_ipynb_file in ready_chapters
if is_todo_chapter:
    chapter_title_beta += " " + todo_suffix
if is_ready_chapter:
    chapter_title_beta += " " + ready_suffix

if args.home:
    link_class = ' class="this_page"'
else:
    link_class = ''
all_chapters_menu = '''
<li><a href="%s"%s><span class="part_number"><i class="fa fa-fw fa-home"></i></span> About this book</a></li>
<li><a href="__SITE_HTML__html/00_Table_of_Contents.html"><i class="fa fa-fw fa-sitemap"></i></span> Sitemap</a></li>
''' % (site_html, link_class)
structured_all_chapters_menu = all_chapters_menu

this_chapter_counter = 1
for counter, menu_ipynb_file in enumerate(all_chapters):
    if menu_ipynb_file == chapter_ipynb_file:
        this_chapter_counter = counter

in_sublist = False
for counter, menu_ipynb_file in enumerate(all_chapters):
    basename = os.path.splitext(os.path.basename(menu_ipynb_file))[0]
    structured_title = '' # '<span class="chnum">' + repr(counter + 1) + '</span> '
    title = ""

    if menu_ipynb_file == chapter_ipynb_file:
        link_class = ' class="this_page"'
    else:
        link_class = ''
    file_title = get_title(menu_ipynb_file)
    
    if menu_ipynb_file in new_chapters:
        file_title += new_suffix
        
    is_part = file_title.startswith("Part ") or file_title.startswith("Append")
    if file_title.startswith("Part "):
        file_title = '<span class="part_number">' + \
            file_title.replace("Part ", "") \
            .replace(":", '</span>')
            # .replace("I:",    '&#x2160;') \
            # .replace("II:",   '&#x2161;') \
            # .replace("III:",  '&#x2162;') \
            # .replace("IV:",   '&#x2163;') \
            # .replace("V:",    '&#x2164;') \
            # .replace("VI:",   '&#x2165;') \
            # .replace("VII:",  '&#x2166;') \
            # .replace("VIII:", '&#x2167;') \
            # .replace("IX:",   '&#x2168;') \
            # .replace("X:",    '&#x2169;') \
            # .replace("XI:",   '&#x216a;') \
            # .replace("XII:",  '&#x216b;') \
            # .replace(';', ';</span>') \

    title += file_title
    structured_title += file_title

    beta_indicator = ''
    if menu_ipynb_file in ready_chapters:
        beta_indicator = "&nbsp;" + ready_suffix
    if menu_ipynb_file in todo_chapters:
        beta_indicator = "&nbsp;" + todo_suffix
    menu_html_file = menu_prefix + basename + ".html"
    
    if is_part:
        # New part
        if in_sublist:
            structured_all_chapters_menu += "</ul>"
            in_sublist = False
        structured_all_chapters_menu += \
            '<li class="has-sub"><a href="%s" class="chapters">%s%s' \
            % (menu_html_file, file_title, beta_indicator)
        structured_all_chapters_menu += ' <i class="fa fa-fw fa-caret-right"></i></a>\n<ul>\n'
        in_sublist = True
    else:
        structured_item = '<li><a href="%s"%s>%s%s</a></li>\n' % \
            (menu_html_file, link_class, structured_title, beta_indicator)
        structured_all_chapters_menu += structured_item
    
        item = '<li><a href="%s"%s>%s%s</a></li>\n' % \
            (menu_html_file, link_class, title, beta_indicator)
        all_chapters_menu += item
    
if in_sublist:
    structured_all_chapters_menu += "</ul>"
    in_sublist = False

# Description
description = html.escape(get_description(chapter_ipynb_file))

# Exercises
end_of_exercise = '''
<p><div class="solution_link"><a href="__CHAPTER_NOTEBOOK_IPYNB__#Exercises" target=_blank>Use the notebook</a> to work on the exercises and see solutions.</div></p>
'''

if args.home:
    share_message = (r'I just read "' + booktitle 
        + r'" (@FuzzingBook) at ' + site_html)
    share_title = booktitle
else:
    share_message = (r'I just read "' + chapter_title 
        + r'" (part of @FuzzingBook) at ' + chapter_html)
    share_title = chapter_title

share_twitter = "https://twitter.com/intent/tweet?text=" + cgi_escape(share_message)
share_facebook = "https://www.facebook.com/sharer/sharer.php?u=" + cgi_escape(chapter_html)
share_mail = ("mailto:?subject=" + cgi_escape(share_title) 
    + "&body=" + cgi_escape(share_message))

# Page title
if args.home:
    page_title = booktitle
else:
    page_title = chapter_title + " - " + booktitle

# sys.exit(0)

# Read it in
print("Reading", chapter_html_file)
chapter_contents = open(chapter_html_file, encoding="utf-8").read()

# Replacement orgy
# 1. Replace all markdown links to .ipynb by .html, such that cross-chapter links work
# 2. Fix extra newlines in cell output produced by ipypublish
# 3. Insert the menus and templates as defined above
chapter_contents = chapter_contents \
    .replace("\n\n</pre>", "\n</pre>") \
    .replace("<__HEADER__>", header_template) \
    .replace("<__FOOTER__>", footer_template) \
    .replace("<__ALL_CHAPTERS_MENU__>", all_chapters_menu) \
    .replace("<__STRUCTURED_ALL_CHAPTERS_MENU__>", structured_all_chapters_menu) \
    .replace("<__ALL_SECTIONS_MENU__>", all_sections_menu) \
    .replace("<__END_OF_EXERCISE__>", end_of_exercise) \
    .replace("__PAGE_TITLE__", page_title) \
    .replace("__BOOKTITLE_BETA__", booktitle_beta) \
    .replace("__BOOKTITLE__", booktitle) \
    .replace("__BOOKIMAGE__", bookimage) \
    .replace("__DESCRIPTION__", description) \
    .replace("__AUTHORS__", authors) \
    .replace("__CHAPTER__", chapter) \
    .replace("__CHAPTER_TITLE__", chapter_title) \
    .replace("__CHAPTER_TITLE_BETA__", chapter_title_beta) \
    .replace("__CHAPTER_HTML__", chapter_html) \
    .replace("__SITE_HTML__", site_html) \
    .replace("__NOTEBOOK_HTML__", notebook_html) \
    .replace("__CHAPTER_NOTEBOOK_IPYNB__", chapter_notebook_ipynb) \
    .replace("__GITHUB_HTML__", github_html) \
    .replace("__TWITTER_ONCLICK__", twitter_onclick) \
    .replace("__FACEBOOK_ONCLICK__", facebook_onclick) \
    .replace("__SHARE_TWITTER__", share_twitter) \
    .replace("__SHARE_FACEBOOK__", share_facebook) \
    .replace("__SHARE_MAIL__", share_mail) \
    .replace("__DATE__", notebook_modification_datetime) \
    .replace("__YEAR__", notebook_modification_year)

# Add links to imports
chapter_contents = add_links_to_imports(chapter_contents)

# Fix simple .ipynb links within text and XML
if args.home:
    chapter_contents = re.sub(r'<a (xlink:href|href)="([a-zA-Z0-9_]*)\.ipynb', 
        r'<a \1="html/\2.html', chapter_contents)
else:
    chapter_contents = re.sub(r'<a (xlink:href|href)="([a-zA-Z0-9_]*)\.ipynb', 
        r'<a \1="\2.html', chapter_contents)

# Recode TeX accents imported from fuzzingbook.bib
chapter_contents = bibtex_unescape(chapter_contents)

# Expand BibTeX authors at the end, because Marcel needs his Umlaut encoded
chapter_contents = \
    chapter_contents.replace("__AUTHORS_BIBTEX__", authors_bibtex)
    
# Highlight details switchers
chapter_contents = fix_detail_switchers(chapter_contents)

# Handle the (first) synopsis
chapter_contents = highlight_synopsis(chapter_contents)

# Get proper links for CSS and Favicon
if args.home:
    chapter_contents = chapter_contents.replace("custom.css", menu_prefix + "custom.css")
    chapter_contents = chapter_contents.replace("favicon/", menu_prefix + "favicon/")

# Get a title
# The official way is to set a title in document metadata, 
# but a) Jupyter Lab can't edit it, and b) the title conflicts with the chapter header - AZ
chapter_contents = re.sub(r"<title>.*</title>", 
    "<title>" + page_title + "</title>", chapter_contents, 1)

beta_warning = None
if is_todo_chapter:
    beta_warning = '<p><em class="beta">' + todo_suffix + '&nbsp;This chapter is work in progress ("beta").  It is incomplete and may change at any time.</em></p>'
elif is_ready_chapter:
    beta_warning = '<p><em class="beta">' + ready_suffix + '&nbsp;This chapter is still under review ("beta").  It may change at any time.</em></p>'

if beta_warning is not None:
    chapter_contents = chapter_contents.replace("</h1>", "</h1>" + beta_warning)

# And write it out again
print("Writing", chapter_html_file)
open(chapter_html_file, mode="w", encoding="utf-8").write(chapter_contents)
