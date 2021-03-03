import json
import os
import sys

from src.common import count_leading_characters

CURRENT_PATH = os.path.dirname(os.path.realpath(sys.argv[0]))
RULEBOOK_PATH = os.path.join(CURRENT_PATH, 'rulebook')


def check_for_duplicates(components, log):
    seen = dict()
    for component in components:
        if component['name'] in seen:
            log('Warning: %s is a repeat move name' % component['name'])
        seen[component['name']] = component


def check_move_fields(moves):
    fields = {
        'order': str,
        'name': str,
        'poise_requirement': str,
        'poise_cost': str,
        'description': list,
        'additional_requirements': list,
        'effects': list,
    }

    for move in moves:
        if 'name' not in move:
            raise Exception('Missing "name" field in move, move=%s' % move)

        for field, json_type in fields.items():
            if field not in move:
                raise Exception('Expected field "%s" to be present in move "%s"' % (field, move['name']))
            if not isinstance(move[field], json_type):
                raise Exception('Expected field "%s" to be type "%s" in move "%s"'
                                % (field, str(json_type), move['name']))


def check_ints(moves):
    def _check(move, key):
        value = move[key]
        if value == 'None':
            return

        try:
            int(value)
        except ValueError:
            raise Exception('In {}, non-numeric value for "{}" field'.format(move['name'], key))

    for move in moves:
        _check(move, 'order')
        _check(move, 'poise_requirement')
        _check(move, 'poise_cost')


def check_bullets(moves):
    def _check(move, key):
        lines = move[key]
        if not lines:
            return

        for line in lines:
            if not line.strip().startswith('*'):
                raise Exception('In {}, a line in {} does not begin with a "*"'.format(move['name'], key))
            spaces = count_leading_characters(line, ' ')
            if spaces % 2 != 0:
                raise Exception('In {}, a line in {} does not begin with an even number of spaces'
                                .format(move['name'], key))

    for move in moves:
        _check(move, 'additional_requirements')
        _check(move, 'effects')


def validate(log):
    log('Validating rulebook files')

    with open(os.path.join(RULEBOOK_PATH, 'outline.json'), 'r', encoding='utf-8') as f:
        outline = json.load(f)

    movesets = [key for key in outline.keys() if 'Moveset' in key]

    all_moves = []
    for moveset in movesets:
        file_name = moveset.lower().replace(' ', '_') + '.json'
        with open(os.path.join(RULEBOOK_PATH, file_name), 'r', encoding='utf-8') as f:
            moves = json.load(f)
            all_moves.extend(moves)

    check_for_duplicates(all_moves, log)
    check_move_fields(moves)
    check_ints(moves)
    check_bullets(moves)

    log('Validated rulebook files')
