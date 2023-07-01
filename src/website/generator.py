import json
import os
import shutil
import sys

from src.common import SECTION_HEADER, paragraph, count_leading_characters, make_dir


CURRENT_PATH = os.path.dirname(os.path.realpath(sys.argv[0]))
HTML_PATH = os.path.join(CURRENT_PATH, 'html')
HTML_TEMPLATES = os.path.join(HTML_PATH, 'templates')
HTML_GENERATED = os.path.join(HTML_PATH, 'generated')
RULEBOOK_PATH = os.path.join(CURRENT_PATH, 'rulebook')

SECTION_HTML = '<article>\n{content}\n</article>\n<br>\n'
LINK_HTML = '<a href="#{name}">{name}</a>\n'
BOLD_HTML = '<b>{}</b>'
BOLD_PLUS_HTML = '<b>{}:</b> {}'


def _generate_nav_sidebar(outline):
    content = ''
    for level1, level2 in outline.items():
        content += LINK_HTML.format(name=level1)
        if level2 is not None:
            content += '<div class="sidenav-subsection">\n'
            for subsection in level2:
                content += '\t' + LINK_HTML.format(name=subsection)
            content += '</div>\n'

    return content


def _load_section_from(section_title, source_path):
    section_file_name_base = section_title.lower().replace(' ', '_')
    html_file = os.path.join(source_path, section_file_name_base + '.html')
    json_file = os.path.join(source_path, section_file_name_base + '.json')

    if os.path.exists(html_file):
        with open(html_file, 'r', encoding='utf-8') as f:
            return f.read()

    if os.path.exists(json_file):
        with open(json_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    raise FileNotFoundError(f'No data file found for {section_title}')


def _convert_bulleted_lines_html(header, lines):
    if not lines:
        return paragraph(header + ' None')

    text = ''
    last_depth = 0
    for line in lines:
        current_depth = count_leading_characters(line, ' ')
        assert current_depth % 2 == 0
        current_depth = int(current_depth / 2)
        line = line.strip().lstrip('*').strip()

        if current_depth == last_depth:
            if text:
                text += f'</li>\n<li>{line}'
            else:
                text += f'<li>{line}'
        elif current_depth > last_depth:
            text += f'\n<ul>\n<li>{line}'
        else:
            text += f'</li>\n</ul>\n<li>{line}'

        last_depth = current_depth

    # Close any open tags
    for i in range(last_depth + 1):
        text += '</li>\n</ul>\n'
    text = f'<ul>\n{text}'

    return f'{paragraph(header)}\n{text}'


def _process_moveset(section_title, moveset):
    with open(os.path.join(HTML_TEMPLATES, 'move.html'), encoding='utf8') as f:
        move_template = f.read()

    content = SECTION_HEADER.format(name=section_title, level='h2')

    for move in moveset:
        poise_requirement = BOLD_PLUS_HTML.format('Poise Requirement', move['poise_requirement'])

        poise_cost_gain = move['poise_cost']
        if poise_cost_gain.startswith('-'):
            poise_cost_gain = BOLD_PLUS_HTML.format('Poise Cost', poise_cost_gain)
        elif poise_cost_gain.startswith('+'):
            poise_cost_gain = BOLD_PLUS_HTML.format('Poise Gain', poise_cost_gain)
        else:
            poise_cost_gain = BOLD_PLUS_HTML.format('Poise Cost', 'None')

        description = '\n'.join(move['description'])
        additional_requirements = _convert_bulleted_lines_html(BOLD_HTML.format('Additional Requirements:'),
                                                               move['additional_requirements'])
        effects = _convert_bulleted_lines_html(BOLD_HTML.format('Effects:'), move['effects'])

        move_html = move_template.format(**{
            'order': move['order'],
            'name': move['name'],
            'poise_requirement': poise_requirement,
            'poise_cost_gain': poise_cost_gain,
            'description': description,
            'additional_requirements': additional_requirements,
            'effects': effects,
        })
        content += move_html

    return SECTION_HTML.format(content=content)


def _generate_rulebook_html(log):
    log('Generating rulebook HTML')

    with open(os.path.join(RULEBOOK_PATH, 'outline.json'), encoding='utf8') as f:
        outline = json.load(f)

    # Make sidebar content
    nav_content = _generate_nav_sidebar(outline)

    # Make main content
    content = ''
    for section_title in outline.keys():
        section_content = _load_section_from(section_title, RULEBOOK_PATH)
        if isinstance(section_content, str):
            content += SECTION_HTML.format(content=section_content)
        else:
            content += _process_moveset(section_title, section_content)

    # Fill out the rulebook HTML template
    with open(os.path.join(HTML_TEMPLATES, 'painted_lands.html'), encoding='utf8') as f:
        rulebook_template = f.read().strip()
    format_args = {
        'nav': nav_content,
        'content': content,
    }
    rulebook_html = rulebook_template.format(**format_args)

    with open(os.path.join(HTML_GENERATED, 'PaintedLands.html'), 'w', encoding='utf8') as f:
        f.write(rulebook_html)

    log('Generated rulebook HTML')


def generate_html(log):
    make_dir(HTML_GENERATED)
    _generate_rulebook_html(log)
    shutil.copyfile(os.path.join(HTML_TEMPLATES, 'style.css'), os.path.join(HTML_GENERATED, 'style.css'))
