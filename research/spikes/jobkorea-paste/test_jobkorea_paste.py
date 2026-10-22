import copy
import json
from pathlib import Path
import unittest

from jobkorea_paste import parse_page, reconcile

SAMPLE = Path(__file__).parent / 'samples' / 'page1-seoul-newgrad.txt'


class PasteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = SAMPLE.read_text(encoding='utf-8')

    def test_sample_counts_and_first(self):
        page = parse_page(self.text)
        self.assertEqual((page['reported_total'], page['page_size']), (109, 40))
        self.assertEqual(page['pages_shown'], [1, 2, 3])
        self.assertEqual(len(page['items']), 40)
        item = page['items'][0]
        self.assertEqual(item['company'], '㈜위즈브레인')
        self.assertEqual(item['title'], '영상관제/IP WALL 시스템 엔지니어 채용')
        self.assertEqual((item['experience'], item['education'], item['location'],
                          item['employment_type']),
                         ('신입·경력', '초대졸↑', '서울 금천구', '정규직'))
        self.assertIn('스토리지', item['keywords'])
        json.dumps(page, ensure_ascii=False)

    def test_current_page_not_visible(self):
        page = parse_page(self.text)
        self.assertIsNone(page['current_page'])
        self.assertIn('활성', page['current_page_evidence'])

    def test_filters(self):
        self.assertEqual(parse_page(self.text)['applied_filters'],
                         ['서울', '신입', '대학졸업(2,3년)', '백엔드개발자',
                          '웹개발자', '소프트웨어개발자', '시스템엔지니어'])

    def test_exclusions(self):
        blocks = parse_page(self.text)['excluded_blocks']
        self.assertEqual([b['reason'] for b in blocks],
                         ['smartpick_ad'] * 3 + ['dispatch_agency_section'])
        self.assertEqual(blocks[-1]['company'], 'Farben Information Co., Ltd.')

    def test_variants_and_empty_keywords(self):
        items = parse_page(self.text)['items']
        dimoa = next(i for i in items if i['company'] == '주식회사 디모아')
        self.assertEqual(dimoa['registration'], '6일 전 등록')
        self.assertEqual(dimoa['deadline'], '상시채용')
        self.assertTrue(any(i['deadline'] == '모레마감' for i in items))
        self.assertEqual(next(i for i in items if i['company'] == '㈜한네트')['keywords'], '')
        self.assertEqual(items[4]['tail'], '3,000만원 이상 팀장/매니저/실장')
        self.assertEqual(items[16]['location'], '서울 금천구 외')
        self.assertEqual(items[16]['employment_type'], '정규직 외')

    def test_same_company_different_titles_retained(self):
        items = parse_page(self.text)['items']
        self.assertEqual(len([i for i in items if i['company'] == '㈜에이엔에이치코리아']), 2)
        self.assertEqual(reconcile([parse_page(self.text)])['unique_count'], 40)

    def test_newline_and_whitespace_variants(self):
        changed = '\r\n'.join('\t' + line.strip() for line in self.text.splitlines())
        self.assertEqual(parse_page(changed)['items'], parse_page(self.text)['items'])

    def test_truncated_item_warns(self):
        changed = self.text.replace('~10/28(수)\n 선택한', ' 선택한', 1)
        page = parse_page(changed)
        self.assertEqual(len(page['items']), 39)
        self.assertTrue(any('unparsed' in w for w in page['warnings']))

    def test_missing_structure_never_complete(self):
        page = parse_page('임의의 텍스트')
        self.assertIsNone(page['reported_total'])
        self.assertEqual(page['items'], [])
        self.assertEqual(reconcile([page])['status'], 'unverifiable')

    def test_unknown_page_numbers(self):
        result = reconcile([parse_page(self.text)])
        self.assertEqual(result['missing_count'], 69)
        self.assertIsNone(result['missing_pages'])
        self.assertEqual(result['status'], 'incomplete')

    def test_known_page_and_duplicate(self):
        page = parse_page(self.text, page_number=1)
        result = reconcile([page, copy.deepcopy(page)])
        self.assertEqual(result['unique_count'], 40)
        self.assertEqual(result['missing_count'], 69)
        self.assertEqual(result['missing_pages'], [2, 3])
        self.assertEqual(result['duplicate_count'], 40)

    def test_synthetic_complete_is_only_provisional(self):
        # Synthetic acceptance test, not evidence of real pages 2/3.
        pages = []
        for number, count in [(1, 40), (2, 40), (3, 29)]:
            page = parse_page(self.text)
            page['current_page'] = number
            page['current_page_evidence'] = 'synthetic checklist'
            page['warnings'] = [w for w in page['warnings'] if not w.startswith('unknown_current')]
            page['items'] = copy.deepcopy(page['items'][:count])
            for item in page['items']:
                item['title'] += f' synthetic-page-{number}'
            pages.append(page)
        result = reconcile(pages)
        self.assertEqual(result['unique_count'], 109)
        self.assertEqual(result['missing_pages'], [])
        self.assertEqual(result['status'], 'count_matches_provisionally')
        self.assertFalse(result['completeness_verified'])

    def test_conflicting_totals_and_filters(self):
        page = parse_page(self.text, page_number=1)
        other = copy.deepcopy(page)
        other['reported_total'] = 110
        other['applied_filters'] = ['다른 조건']
        result = reconcile([page, other])
        self.assertEqual(result['status'], 'unverifiable')
        self.assertTrue(result['warnings'])

    def test_out_of_range_and_short_copy(self):
        self.assertEqual(reconcile([parse_page(self.text, page_number=4)])['status'],
                         'unverifiable')
        short = self.text.replace('~10/28(수)\n 선택한', ' 선택한', 1)
        self.assertEqual(reconcile([parse_page(short, page_number=1)])['status'],
                         'unverifiable')
        with self.assertRaises(ValueError):
            parse_page(self.text, page_number=0)

    def test_unknown_metadata_layout_warns(self):
        changed = self.text.replace('신입·경력 초대졸↑ 서울 금천구 정규직',
                                    '신입·경력 학력미상 서울 금천구 정규직', 1)
        page = parse_page(changed, page_number=1)
        self.assertEqual(len(page['items']), 39)
        self.assertEqual(reconcile([page])['status'], 'unverifiable')

    def test_key_collision_detected(self):
        page = parse_page(self.text)
        changed = copy.deepcopy(page['items'][0])
        changed['location'] = '서울 다른구'
        page['items'].append(changed)
        result = reconcile([page])
        self.assertEqual(result['identity_conflicts'], 1)
        self.assertEqual(result['status'], 'unverifiable')


if __name__ == '__main__':
    unittest.main()
