import os


SECTION_HEADER = """<a id="{name}">
    <{level}>{name}</{level}>
</a>
"""
PARAGRAPH = '<p>{}</p>\n'
INDENT = '&nbsp;&nbsp;&nbsp;&nbsp;'


def make_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def paragraph(line):
    if line.startswith('\t'):
        return PARAGRAPH.format(INDENT + line.strip())
    else:
        return PARAGRAPH.format(line.strip())


def count_leading_characters(line, character):
    for i, char in enumerate(line):
        if char != character:
            return i
    return 0


def href(anchor, text, title=None, fancy=''):
    if title:
        return '<a href="{anchor}" title="{title}" {fancy}>{text}</a>'.format(anchor=anchor, text=text,
                                                                              title=title, fancy=fancy)
    else:
        return '<a href="{anchor}" {fancy}>{text}</a>'.format(anchor=anchor, text=text, fancy=fancy)
