#!/usr/bin/env python
"""
Comprehensive pagination pattern analysis tool for transcriptions.
Analyzes pagination markers and checks coverage by transcription-sync.js support.
"""
import os
import re
import sys
from collections import Counter, defaultdict

# Add Django project to path
sys.path.insert(0, '/workspaces/lumieres-lausanne/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lumieres_project.settings')

import django

django.setup()

from fiches.models import Transcription


def extract_all_markers(text):
    """
    Extract all pagination markers matching the patterns supported by transcription-sync.js.
    
    Supported formats:
    1. /p. N/ format
    2. <Nr> or <Nv> explicit recto/verso in angle brackets
    3. [Nr] or [Nv] explicit recto/verso in square brackets
    4. <N> implicit recto in angle brackets
    5. [N] implicit recto in square brackets (1-3 digits, excludes years)
    """
    if not text:
        return []
    
    markers = []
    
    # Format 1: /p. N/
    pattern1 = r'/p\.\s*(\d+)/'
    for m in re.finditer(pattern1, text):
        markers.append({
            'pattern': m.group(0),
            'type': 'p-format',
            'page': int(m.group(1))
        })
    
    # Format 2: Explicit recto/verso in angle brackets <Nr> <Nv>
    pattern2 = r'(?:<|&lt;)(\d+)([rv])(?:>|&gt;)'
    for m in re.finditer(pattern2, text, re.IGNORECASE):
        num = int(m.group(1))
        side = m.group(2).lower()
        markers.append({
            'pattern': m.group(0),
            'type': 'rv-explicit-angle',
            'folio': num,
            'side': side,
            'page': (num * 2 - 1) if side == 'r' else (num * 2)
        })
    
    # Format 3: Explicit recto/verso in square brackets [Nr] [Nv]
    pattern3 = r'\[(\d{1,3})([rv])\]'
    for m in re.finditer(pattern3, text, re.IGNORECASE):
        num = int(m.group(1))
        side = m.group(2).lower()
        markers.append({
            'pattern': m.group(0),
            'type': 'rv-explicit-bracket',
            'folio': num,
            'side': side,
            'page': (num * 2 - 1) if side == 'r' else (num * 2)
        })
    
    # Format 4: Implicit recto in angle brackets <N>
    # Exclude patterns already matched and HTML tags
    pattern4 = r'(?:<|&lt;)(\d+)(?:>|&gt;)'
    explicit_angle_positions = set(m.span() for m in re.finditer(pattern2, text, re.IGNORECASE))
    
    for m in re.finditer(pattern4, text):
        # Skip if already matched as explicit
        if m.span() in explicit_angle_positions:
            continue
        
        # Check if it's likely an HTML tag by looking at context
        start = max(0, m.start() - 20)
        end = min(len(text), m.end() + 20)
        context = text[start:end]
        
        # Skip if it looks like HTML
        if '=' in context or 'class' in context or 'style' in context:
            continue
        
        num = int(m.group(1))
        markers.append({
            'pattern': m.group(0),
            'type': 'rv-implicit-angle',
            'folio': num,
            'side': 'r',
            'page': num * 2 - 1
        })
    
    # Format 5: Implicit recto in square brackets [N] (1-3 digits only)
    pattern5 = r'\[(\d{1,3})\]'
    explicit_bracket_positions = set(m.span() for m in re.finditer(pattern3, text, re.IGNORECASE))
    
    for m in re.finditer(pattern5, text):
        # Skip if already matched as explicit
        if m.span() in explicit_bracket_positions:
            continue
        
        num = int(m.group(1))
        markers.append({
            'pattern': m.group(0),
            'type': 'rv-implicit-bracket',
            'folio': num,
            'side': 'r',
            'page': num * 2 - 1
        })
    
    return markers


def analyze_patterns():
    """Analyze all pagination patterns across all transcriptions."""
    
    print("=" * 80)
    print("PAGINATION PATTERN ANALYSIS")
    print("=" * 80)
    print()
    
    transcriptions = Transcription.objects.filter(text__isnull=False).exclude(text='')
    total = transcriptions.count()
    
    print(f"Total transcriptions analyzed: {total}\n")
    
    # Collect all markers
    all_markers = []
    trans_with_markers = []
    trans_without_markers = []
    
    for t in transcriptions:
        markers = extract_all_markers(t.text)
        if markers:
            trans_with_markers.append({
                'id': t.id,
                'markers': markers,
                'count': len(markers),
                'types': set(m['type'] for m in markers),
                'first_page': markers[0]['page'] if markers else None
            })
            all_markers.extend(markers)
        else:
            trans_without_markers.append(t.id)
    
    print(f"Transcriptions with pagination markers: {len(trans_with_markers)} ({len(trans_with_markers)/total*100:.1f}%)")
    print(f"Transcriptions without markers: {len(trans_without_markers)} ({len(trans_without_markers)/total*100:.1f}%)")
    print(f"Total pagination markers found: {len(all_markers)}\n")
    
    # Analyze by pattern type
    print("=" * 80)
    print("PATTERN TYPES")
    print("=" * 80)
    
    type_counts = Counter(m['type'] for m in all_markers)
    
    for pattern_type, count in type_counts.most_common():
        percentage = (count / len(all_markers) * 100) if all_markers else 0
        print(f"\n{pattern_type.replace('-', ' ').upper()}:")
        print(f"  Total: {count} markers ({percentage:.1f}%)")
        
        # Show some examples
        examples = [m['pattern'] for m in all_markers if m['type'] == pattern_type]
        unique_examples = list(dict.fromkeys(examples))[:5]
        print(f"  Examples: {', '.join(unique_examples)}")
    
    # Mixed pattern analysis
    print("\n" + "=" * 80)
    print("MIXED PATTERN ANALYSIS")
    print("=" * 80)
    
    mixed_transcriptions = []
    for item in trans_with_markers:
        types = item['types']
        has_implicit = any('implicit' in t for t in types)
        has_explicit = any('explicit' in t for t in types)
        
        if has_implicit and has_explicit:
            mixed_transcriptions.append(item)
    
    if mixed_transcriptions:
        print(f"\nFound {len(mixed_transcriptions)} transcriptions with MIXED patterns")
        print("(Both implicit and explicit recto/verso)\n")
        for item in mixed_transcriptions[:10]:
            types_str = ', '.join(sorted(item['types']))
            print(f"  Transcription {item['id']}: {item['count']} markers ({types_str})")
    else:
        print("\nNo transcriptions with mixed implicit/explicit patterns found.")
    
    # First page analysis
    print("\n" + "=" * 80)
    print("FIRST PAGE ANALYSIS")
    print("=" * 80)
    
    first_pages = [item['first_page'] for item in trans_with_markers if item['first_page']]
    
    starts_at_1 = sum(1 for p in first_pages if p == 1)
    starts_after_1 = sum(1 for p in first_pages if p > 1)
    
    print(f"\nTranscriptions starting at page 1: {starts_at_1}")
    print(f"Transcriptions starting at page > 1: {starts_after_1}")
    
    if first_pages:
        print(f"\nFirst page statistics:")
        print(f"  Min: {min(first_pages)}")
        print(f"  Max: {max(first_pages)}")
        print(f"  Average: {sum(first_pages)/len(first_pages):.1f}")
    
    # Show examples of high page starters
    high_starters = [item for item in trans_with_markers if item['first_page'] and item['first_page'] > 50]
    if high_starters:
        print(f"\nExamples starting at high page numbers:")
        for item in sorted(high_starters, key=lambda x: x['first_page'], reverse=True)[:5]:
            print(f"  Trans {item['id']}: starts at page {item['first_page']}")
    
    # Pattern type examples
    print("\n" + "=" * 80)
    print("EXAMPLE TRANSCRIPTIONS BY PATTERN")
    print("=" * 80)
    
    examples_by_type = defaultdict(list)
    
    for item in trans_with_markers:
        types = item['types']
        
        # Categorize
        if len(types) == 1:
            pattern_type = list(types)[0]
            if len(examples_by_type[pattern_type]) < 5:
                examples_by_type[pattern_type].append(item['id'])
        elif 'implicit' in str(types) and 'explicit' in str(types):
            if len(examples_by_type['mixed']) < 5:
                examples_by_type['mixed'].append(item['id'])
    
    for pattern_type in sorted(examples_by_type.keys()):
        ids = examples_by_type[pattern_type]
        print(f"\n{pattern_type.replace('-', ' ').upper()}:")
        print(f"  Example IDs: {ids}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"\nCoverage: {len(trans_with_markers)}/{total} transcriptions ({len(trans_with_markers)/total*100:.1f}%)")
    print(f"Total markers: {len(all_markers)}")
    print(f"Unique pattern types: {len(type_counts)}")
    
    if trans_without_markers[:10]:
        print(f"\nExample transcription IDs without markers:")
        print(f"  {trans_without_markers[:10]}")
    
    return trans_with_markers, all_markers


if __name__ == '__main__':
    analyze_patterns()
