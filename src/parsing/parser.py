import docx2python
import docx2python.iterators
import json
import os

from collections import Callable, OrderedDict

from src.common import count_leading_characters, make_dir, paragraph, SECTION_HEADER


CURRENT_PATH = os.getcwd()
DATA_PATH = os.path.join(CURRENT_PATH, 'data')
DATA_DOCX = os.path.join(DATA_PATH, 'The Painted Lands_ Rulebook.docx')
DATA_TXT = os.path.join(DATA_PATH, 'data.txt')
RULEBOOK_PATH = os.path.join(CURRENT_PATH, 'rulebook')


def _fix_quotes(obj):
    if isinstance(obj, str):
        return obj.replace(u'\u201C', '"').replace(u'\u201D', '"').replace(u'\u2019', "'")
    elif isinstance(obj, list):
        return [_fix_quotes(o) for o in obj]
    elif isinstance(obj, dict):
        return {_fix_quotes(k): _fix_quotes(v) for k, v in obj.items()}
    else:
        return obj


def _write_section(f, section):
    for line in section:
        f.write(paragraph(line))
    f.write('<br>\n')


def _lines_to_sections(lines, section_headers):
    section_indices = []
    for index, line in enumerate(lines):
        if line in section_headers:
            section_indices.append(index)

    assert len(section_headers) == len(section_indices)

    if section_indices[0] != 0:
        preface = lines[0:section_indices[0]]
    else:
        preface = None

    sections = {}
    for i, start_index in enumerate(section_indices):
        section_title = lines[start_index]
        if i + 1 < len(section_indices):
            end_index = section_indices[i + 1]
        else:
            end_index = len(lines)

        sections[section_title] = lines[start_index + 1:end_index]

    assert len(section_headers) == len(sections)
    return preface, sections


def _process_subsection(f, outline, section, depth):
    if outline is None:
        _write_section(f, section)
    else:
        preface, subsections = _lines_to_sections(section, outline.keys())
        for subsection_header, subsection in subsections.items():
            f.write(SECTION_HEADER.format(name=subsection_header, level='h' + str(depth)))
            if preface is not None:
                _write_section(f, preface)
            _process_subsection(f, outline[subsection_header], subsection, depth + 1)


def _find_line_index(lines, keys):
    for i, line in enumerate(lines):
        if any(key in line for key in keys):
            return i
    raise ValueError(f'{keys} not found in given lines, {lines}')


def _convert_bulleted_lines(lines):
    text = ''
    for line in lines:
        current_depth = count_leading_characters(line, '\t')
        indent = ' ' * (current_depth * 2)
        line = line.strip().lstrip('-').strip()
        text += f'{indent}* {line}\n'

    return text.splitlines()


def _parse_move_block(log, lines):
    order = lines[0]
    name = lines[1]

    poise_requirement_index = _find_line_index(lines, ['Poise Requirement'])
    poise_cost_index = _find_line_index(lines, ['Poise Cost', 'Poise Gain'])
    additional_requirements_index = _find_line_index(lines, ['Additional Requirements'])
    effects_index = _find_line_index(lines, ['Effects'])

    poise_requirement = lines[poise_requirement_index]
    poise_requirement = poise_requirement.split(':')[1].strip()

    poise_cost = lines[poise_cost_index]
    poise_cost = poise_cost.split(':')[1].strip()

    description = lines[poise_cost_index + 1:additional_requirements_index]

    additional_requirements_lines = lines[additional_requirements_index + 1:effects_index]
    if len(additional_requirements_lines) == 0:
        if 'Additional Requirements: None' not in lines[additional_requirements_index]:
            log(f'Unexpected additional requirements in {name}')
    else:
        additional_requirements_lines = _convert_bulleted_lines(additional_requirements_lines)

    effects_lines = lines[effects_index + 1:]
    if len(effects_lines) == 0:
        if 'Effects: None' not in lines[effects_index]:
            print(f'Unexpected effects in {name}')
    else:
        effects_lines = _convert_bulleted_lines(effects_lines)

    return {
        'order': order,
        'name': name,
        'poise_requirement': poise_requirement,
        'poise_cost': poise_cost,
        'description': description,
        'additional_requirements': additional_requirements_lines,
        'effects': effects_lines,
    }


def _process_moveset(log, section_title, section):
    block_indices = []
    for index, line in enumerate(section):
        try:
            int(line)
            block_indices.append(index)
        except ValueError:
            pass

    move_blocks = []
    for i, start_index in enumerate(block_indices):
        if i + 1 < len(block_indices):
            end_index = block_indices[i + 1]
        else:
            end_index = len(section)
        move_blocks.append(section[start_index:end_index])

    moves = []
    for block in move_blocks:
        moves.append(_parse_move_block(log, block))
    moves.sort(key=lambda move: int(move['order']))

    section_file_name = section_title.lower().replace(' ', '_') + '.json'
    with open(os.path.join(RULEBOOK_PATH, section_file_name), 'w', encoding='utf-8') as f:
        json.dump(moves, f, indent=4)


def _record_outline(outline):
    abbreviated_outline = {}
    for level1, level2 in outline.items():
        if isinstance(level2, OrderedDict):
            level2 = [str(key) for key in level2.keys()]
        else:
            level2 = None
        abbreviated_outline[level1] = level2

    with open(os.path.join(RULEBOOK_PATH, 'outline.json'), 'w', encoding='utf-8') as f:
        json.dump(abbreviated_outline, f, indent=4)


OUTLINE = OrderedDict()
OUTLINE['Foreword'] = None
OUTLINE['Design Goals'] = OrderedDict()
OUTLINE['Design Goals']['Simplicity'] = None
OUTLINE['Design Goals']['Flavor'] = None
OUTLINE['Design Goals']['Skill'] = None
OUTLINE['Design Goals']['Fiction First'] = None
OUTLINE['Setting'] = None
OUTLINE['System Basics'] = OrderedDict()
OUTLINE['System Basics']['Skill Checks'] = None
OUTLINE['System Basics']['Combat'] = None
OUTLINE['System Basics']['Position'] = None
OUTLINE['Character Creation'] = None
OUTLINE['Skills'] = OrderedDict()
OUTLINE['Skills']['Weapon Skills'] = OrderedDict()
OUTLINE['Skills']['Weapon Skills']['Axes'] = None
OUTLINE['Skills']['Weapon Skills']['Blunt'] = None
OUTLINE['Skills']['Weapon Skills']['Longblades'] = None
OUTLINE['Skills']['Weapon Skills']['Polearms'] = None
OUTLINE['Skills']['Weapon Skills']['Ranged'] = None
OUTLINE['Skills']['Weapon Skills']['Shortblades'] = None
OUTLINE['Skills']['Vagabond Skills'] = OrderedDict()
OUTLINE['Skills']['Vagabond Skills']['Vigor'] = None
OUTLINE['Skills']['Vagabond Skills']['Finesse'] = None
OUTLINE['Skills']['Vagabond Skills']['Intellect'] = None
OUTLINE['Skills']['Vagabond Skills']['Judgment'] = None
OUTLINE['Skills']['Vagabond Skills']['Allure'] = None
OUTLINE['Skills']['Vagabond Skills']['Edge'] = None
OUTLINE['Skills']['Magic Skills'] = OrderedDict()
OUTLINE['Skills']['Magic Skills']['Runekeeping'] = None
OUTLINE['Skills']['Magic Skills']['Mentalism'] = None
OUTLINE['Skills']['Magic Skills']['Earthcraft'] = None
OUTLINE['Longblades Moveset'] = _process_moveset
OUTLINE['Axes Moveset'] = _process_moveset
OUTLINE['Blunt Weapons Moveset'] = _process_moveset
OUTLINE['Polearms Moveset'] = _process_moveset
OUTLINE['Ranged Weapons Moveset'] = _process_moveset
OUTLINE['Shortblades Moveset'] = _process_moveset


def parse_data(log):
    log('Parsing .docx rulebook')

    make_dir(DATA_PATH)
    make_dir(RULEBOOK_PATH)

    # We need to save to docx and then convert to plaintext so that we can preserve bullet points
    content = docx2python.docx2python(DATA_DOCX)
    lines = list(docx2python.iterators.iter_paragraphs(content.document))

    with open(DATA_TXT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    # Ignore blank lines and page breaks
    lines = [line for line in lines if line.strip() != '']
    lines = [line for line in lines if line.strip() != '________________']
    # Use straight quotation marks
    lines = [_fix_quotes(line) for line in lines]
    # Ignore title page
    lines = lines[2:]

    preface, sections = _lines_to_sections(lines, OUTLINE.keys())

    for section_title, section in sections.items():
        if isinstance(OUTLINE[section_title], Callable):
            OUTLINE[section_title](log, section_title, section)
            continue

        section_file_name = section_title.lower().replace(' ', '_') + '.html'
        with open(os.path.join(RULEBOOK_PATH, section_file_name), 'w', encoding='utf-8') as f:
            f.write(SECTION_HEADER.format(name=section_title, level='h2'))
            if preface is not None:
                _write_section(f, preface)
            _process_subsection(f, OUTLINE[section_title], section, depth=3)

    _record_outline(OUTLINE)

    log('Parsed rulebook text')
