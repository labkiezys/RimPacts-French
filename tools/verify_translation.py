#!/usr/bin/env python3
from __future__ import annotations

import collections
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
SOURCE = PROJECT / 'source-mods' / '3762723122'
FRENCH = PROJECT / 'Languages' / 'French'
PLACEHOLDER = re.compile(r'\{\d+\}')
FRENCH_COGNATES = {'Permanent', 'Conversion', 'Embargo', 'Coalition', 'Ultimatum', 'Ultimatum…', '(vacant)'}


def xml_files(root: Path):
    return sorted(root.rglob('*.xml'))


def leaves(path: Path):
    root = ET.parse(path).getroot()
    return {node.tag: (node.text or '') for node in list(root)}


def all_entries(root: Path):
    entries = {}
    for path in xml_files(root):
        for key, value in leaves(path).items():
            if key in entries:
                raise ValueError(f'Clé dupliquée: {key}')
            entries[key] = value
    return entries


def source_def_entries(keys):
    values = {}
    for path in xml_files(SOURCE / 'Defs'):
        root = ET.parse(path).getroot()
        for definition in list(root):
            def_name = definition.findtext('defName')
            if not def_name:
                continue

            def walk(node, parts):
                counts = collections.Counter()
                for child in list(node):
                    index = counts[child.tag]
                    counts[child.tag] += 1
                    segment = str(index) if child.tag == 'li' else child.tag
                    child_parts = [*parts, segment]
                    key = f'{def_name}.{".".join(child_parts)}'
                    if len(child) == 0 and child.text and key in keys:
                        values[key] = child.text
                    else:
                        walk(child, child_parts)

            walk(definition, [])
    return values


def main() -> int:
    failures = []
    for path in xml_files(PROJECT):
        try:
            ET.parse(path)
        except ET.ParseError as exc:
            failures.append(f'XML invalide: {path}: {exc}')

    source_keyed = all_entries(SOURCE / 'Languages' / 'English' / 'Keyed')
    french_keyed = all_entries(FRENCH / 'Keyed')
    if set(source_keyed) != set(french_keyed):
        failures.append(
            f'Couverture Keyed incorrecte: source={len(source_keyed)}, fr={len(french_keyed)}, '
            f'manquantes={sorted(set(source_keyed)-set(french_keyed))}, '
            f'en trop={sorted(set(french_keyed)-set(source_keyed))}'
        )

    manifest_def = all_entries(SOURCE / 'Languages' / 'Russian (Русский)' / 'DefInjected')
    french_def = all_entries(FRENCH / 'DefInjected')
    if set(manifest_def) != set(french_def):
        failures.append(
            f'Couverture DefInjected incorrecte: manifeste={len(manifest_def)}, fr={len(french_def)}, '
            f'manquantes={sorted(set(manifest_def)-set(french_def))}, '
            f'en trop={sorted(set(french_def)-set(manifest_def))}'
        )
    source_def = source_def_entries(set(manifest_def))
    if set(source_def) != set(manifest_def):
        failures.append(
            f'Sources DefInjected introuvables: {sorted(set(manifest_def)-set(source_def))}'
        )

    unchanged = []
    placeholder_errors = []
    newline_errors = []
    for source_entries, french_entries in (
        (source_keyed, french_keyed),
        (source_def, french_def),
    ):
        for key in set(source_entries) & set(french_entries):
            src, dst = source_entries[key], french_entries[key]
            if (
                src.strip() == dst.strip()
                and src.strip() not in FRENCH_COGNATES
                and re.search(r'[A-Za-z]{3}', src)
            ):
                unchanged.append(key)
            if collections.Counter(PLACEHOLDER.findall(src)) != collections.Counter(PLACEHOLDER.findall(dst)):
                placeholder_errors.append(key)
            if src.count(r'\n') != dst.count(r'\n'):
                newline_errors.append(key)

    if unchanged:
        failures.append(f'Textes anglais inchangés ({len(unchanged)}): {unchanged}')
    if placeholder_errors:
        failures.append(f'Placeholders modifiés ({len(placeholder_errors)}): {placeholder_errors}')
    if newline_errors:
        failures.append(f'Sauts de ligne modifiés ({len(newline_errors)}): {newline_errors}')

    print(f'XML vérifiés: {len(xml_files(PROJECT))}')
    print(f'Keyed français: {len(french_keyed)}/{len(source_keyed)}')
    print(f'DefInjected français: {len(french_def)}/{len(source_def)}')
    print(f'Textes anglais inchangés: {len(unchanged)}')
    print(f'Erreurs de placeholders: {len(placeholder_errors)}')
    print(f'Erreurs de sauts de ligne: {len(newline_errors)}')
    if failures:
        print('\nÉCHEC')
        for failure in failures:
            print(f'- {failure}')
        return 1
    print('\nVALIDATION RÉUSSIE')
    return 0


if __name__ == '__main__':
    sys.exit(main())
