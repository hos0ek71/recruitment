"""Offline, sample-specific feasibility spike; never requests a website.

Usage: python3 jobkorea_paste.py samples/page1-seoul-newgrad.txt --page-number 1
Page numbers come from the caller's checklist, not inferred from this sample.
"""

import argparse
import json
import math
from pathlib import Path
import re


REGISTRATION = re.compile(r'(?:\d{2}/\d{2}\([^)]+\)|\d+일 전) 등록')
DEADLINE = re.compile(r'(?:~\d{2}/\d{2}\([^)]+\)|상시채용|모레마감)')
METADATA = re.compile(
    r'(?P<experience>\S+) (?P<education>초대졸↑) '
    r'(?P<location>서울 \S+(?: 외)?) '
    r'(?P<employment_type>정규직|계약직)(?P<extra> 외)?(?: (?P<tail>.*))?'
)


def _lines(text):
    return [re.sub(r'\s+', ' ', line).strip() for line in text.splitlines()
            if line.strip()]


def _items(lines, warnings):
    """Registration + deadline delimit complete records in the supplied sample."""
    items = []
    start = 0
    for index, line in enumerate(lines):
        if not DEADLINE.fullmatch(line):
            continue
        chunk = lines[start:index + 1]
        start = index + 1
        if len(chunk) < 6 or not REGISTRATION.fullmatch(chunk[-2]):
            warnings.append('unparsed_record: registration/deadline structure differs')
            continue
        metadata = METADATA.fullmatch(chunk[2])
        if not metadata or chunk.count('미리보기') != 1:
            warnings.append('unparsed_record: metadata/preview structure differs')
            continue
        preview = chunk.index('미리보기')
        if preview < 3 or chunk[preview + 1:-2] != ['즉시지원']:
            warnings.append('unparsed_record: action structure differs')
            continue
        values = metadata.groupdict()
        items.append({
            'company': chunk[0], 'title': chunk[1],
            'experience': values['experience'], 'education': values['education'],
            'location': values['location'],
            'employment_type': values['employment_type'] + (values['extra'] or ''),
            'tail': values['tail'] or '',
            'keywords': '\n'.join(chunk[3:preview]),
            'registration': chunk[-2], 'deadline': line,
        })
    if start < len(lines):
        warnings.append(f'unparsed_tail: {len(lines) - start} nonempty lines')
    return items


def parse_page(text, page_number=None):
    """Return JSON-safe data, retaining relative dates verbatim.

    Only the observed sample grammar is supported. Unknown layouts warn; they
    are never silently treated as a complete import. No full-page text is copied
    to the output (navigation can contain personal account information).
    """
    if page_number is not None and (type(page_number) is not int or page_number < 1):
        raise ValueError('page_number must be a positive integer or None')
    lines = _lines(text)
    warnings = ['surrogate_identity: no posting URL/ID; count equality is provisional']
    total_index = next((i for i, line in enumerate(lines)
                        if re.match(r'전체 \([\d,]+건\)', line)), None)
    total_match = re.match(r'전체 \(([\d,]+)건\)', lines[total_index]) if total_index is not None else None
    total = int(total_match[1].replace(',', '')) if total_match else None
    filter_lines = [line for line in lines if line.endswith('삭제')]
    filters = filter_lines[-1].split('삭제')[:-1] if filter_lines else []
    size_indices = [i for i, line in enumerate(lines)
                    if re.fullmatch(r'\d+개씩', line) and total_index is not None
                    and i > total_index]
    size = int(lines[size_indices[0]][:-2]) if size_indices else None
    end = next((i for i, line in enumerate(lines)
                if line == '선택한 공고 한번에 지원하기'), None)
    pages_shown = []
    if end is not None and end + 1 < len(lines) and re.fullmatch(r'\d+(?: \d+)*', lines[end + 1]):
        pages_shown = [int(n) for n in lines[end + 1].split()]
    # The sample repeats the page-size label as a control and its selected value.
    start = size_indices[0] + 1 if size_indices else None
    if start is not None and start < len(lines) and lines[start] == lines[start - 1]:
        start += 1
    if start is None or end is None or start >= end:
        items = []
        warnings.append('unparsed_main_section: required boundaries missing')
    else:
        items = _items(lines[start:end], warnings)
    excluded = []
    if total_index is not None and '스마트픽' in lines[:total_index]:
        ad_start = lines.index('스마트픽')
        thumbnails = [i for i in range(ad_start, total_index)
                      if lines[i].endswith(' 썸네일')]
        for n, index in enumerate(thumbnails):
            stop = thumbnails[n + 1] if n + 1 < len(thumbnails) else total_index
            block = lines[index:stop]
            excluded.append({'reason': 'smartpick_ad', 'company': block[1],
                             'title': block[2], 'lines': block})
    agency = next((i for i, line in enumerate(lines)
                   if line.startswith('파견대행 채용정보 ')), None)
    if agency is not None:
        agency_sizes = [i for i in range(agency + 1, len(lines))
                        if lines[i] == '10개씩']
        if agency_sizes:
            index = agency_sizes[-1] + 1
            stop = next((i + 1 for i in range(index, len(lines))
                         if DEADLINE.fullmatch(lines[i])), index)
            block = lines[index:stop]
            if len(block) >= 2:
                excluded.append({'reason': 'dispatch_agency_section',
                                 'company': block[0], 'title': block[1], 'lines': block})
    if total is None or size is None or not filters or not pages_shown:
        warnings.append('missing_header_metadata: copy range/layout needs review')
    if page_number is None:
        warnings.append('unknown_current_page: 페이지 식별 불가')
    if page_number is not None and total is not None and size:
        expected = max(0, min(size, total - (page_number - 1) * size))
        if len(items) != expected:
            warnings.append(f'page_item_count_mismatch: expected {expected}, parsed {len(items)}')
        if page_number > math.ceil(total / size):
            warnings.append('page_number_out_of_range')
    return {'reported_total': total, 'page_size': size, 'pages_shown': pages_shown,
            'current_page': page_number,
            'current_page_evidence': '호출자가 체크리스트에서 제공한 번호' if page_number else
            '숫자 목록만 있고 활성 페이지 표시가 텍스트에 없어 추론 불가',
            'applied_filters': filters,
            'sort_order': '추천순' if '추천순' in lines[:start] else None,
            'items': items, 'excluded_blocks': excluded, 'warnings': warnings}


def reconcile(pages):
    """Compare a single search session, deduplicating by company/title/date.

    Missing pages are known only when every input carries a caller-supplied
    number. Matching counts do NOT prove identities or snapshot completeness.
    """
    pages = list(pages)
    warnings = sorted({w for page in pages for w in page['warnings']})
    totals = {p['reported_total'] for p in pages}
    sizes = {p['page_size'] for p in pages}
    filters = {tuple(p['applied_filters']) for p in pages}
    sorts = {p['sort_order'] for p in pages}
    compatible = (bool(pages) and len(totals) == len(sizes) == len(filters) == len(sorts) == 1
                  and None not in totals and None not in sizes and all(filters))
    total = next(iter(totals)) if len(totals) == 1 else None
    size = next(iter(sizes)) if len(sizes) == 1 else None
    seen = {}
    duplicates = conflicts = 0
    for page in pages:
        for item in page['items']:
            key = tuple(re.sub(r'\s+', ' ', item[field]).strip()
                        for field in ('company', 'title', 'registration'))
            if key in seen:
                duplicates += 1
                if seen[key] != item:
                    conflicts += 1
            else:
                seen[key] = item
    if conflicts:
        warnings.append('identity_conflict: same surrogate key with different fields')
    if duplicates:
        warnings.append('duplicate_or_collision: identical surrogate keys are not proof of same posting')
    if not compatible:
        warnings.append('incompatible_or_missing_search_metadata')
    known = bool(pages) and all(p['current_page'] is not None for p in pages)
    missing_pages = None
    if compatible and known and size:
        missing_pages = sorted(set(range(1, math.ceil(total / size) + 1)) -
                               {p['current_page'] for p in pages})
    deficit = max(0, total - len(seen)) if compatible else None
    invalid = any(any(w.startswith(('unparsed', 'missing_header', 'page_item', 'page_number'))
                      for w in p['warnings']) for p in pages)
    if not compatible or conflicts or invalid or (total is not None and len(seen) > total):
        status = 'unverifiable'
    elif deficit or missing_pages:
        status = 'incomplete'
    else:
        status = 'count_matches_provisionally'
    return {'status': status, 'reported_total': total, 'unique_count': len(seen),
            'missing_count': deficit, 'missing_pages': missing_pages,
            'duplicate_count': duplicates, 'identity_conflicts': conflicts,
            'completeness_verified': False, 'warnings': warnings}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('sample', type=Path)
    parser.add_argument('--page-number', type=int)
    args = parser.parse_args()
    page = parse_page(args.sample.read_text(encoding='utf-8'), args.page_number)
    print(json.dumps({'page': page, 'reconciliation': reconcile([page])},
                     ensure_ascii=False, indent=2))
