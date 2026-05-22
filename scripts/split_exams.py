#!/usr/bin/env python3
import json
import os

BASE_DIR = '/Users/miyazakikana/yuwalab/sc-pm-problem/data/exams'

def load_json(year, filename):
    path = os.path.join(BASE_DIR, str(year), f"{filename}.json")
    with open(path, encoding='utf-8') as f:
        return json.load(f)

def write_json(year, file_num, era_label, problem_obj, explanation_obj):
    year_str = str(year)
    file_num_str = f"{file_num:02d}"
    data = {
        "id": f"{year_str}-{file_num_str}",
        "era_label": era_label,
        "problems": [problem_obj],
        "explanations": [explanation_obj] if explanation_obj else []
    }
    path = os.path.join(BASE_DIR, year_str, f"{file_num_str}.json")
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  Wrote {year}/{file_num_str}.json: {era_label}")

def get_item(arr, problem_label):
    return next((x for x in arr if x.get('problem') == problem_label), None)

configs = {
    2017: {
        'sources': ['01', '04', '05', '08'],
        'targets': [
            {'src': '01', 'prob': '問1', 'num': 1,  'era': '平成29年度 春 問1'},
            {'src': '01', 'prob': '問2', 'num': 2,  'era': '平成29年度 春 問2'},
            {'src': '01', 'prob': '問3', 'num': 3,  'era': '平成29年度 春 問3'},
            {'src': '04', 'prob': '問1', 'num': 4,  'era': '平成29年度 春 問4'},
            {'src': '04', 'prob': '問2', 'num': 5,  'era': '平成29年度 春 問5'},
            {'src': '05', 'prob': '問1', 'num': 6,  'era': '平成29年度 秋 問1'},
            {'src': '05', 'prob': '問2', 'num': 7,  'era': '平成29年度 秋 問2'},
            {'src': '05', 'prob': '問3', 'num': 8,  'era': '平成29年度 秋 問3'},
            {'src': '08', 'prob': '問1', 'num': 9,  'era': '平成29年度 秋 問4'},
            {'src': '08', 'prob': '問2', 'num': 10, 'era': '平成29年度 秋 問5'},
        ],
        'delete': []
    },
    2018: {
        'sources': ['01', '04', '05', '08'],
        'targets': [
            {'src': '01', 'prob': '問1', 'num': 1,  'era': '平成30年度 春 問1'},
            # 問2 not in data → no file 02
            {'src': '01', 'prob': '問3', 'num': 3,  'era': '平成30年度 春 問3'},
            {'src': '04', 'prob': '問1', 'num': 4,  'era': '平成30年度 春 問4'},
            {'src': '04', 'prob': '問2', 'num': 5,  'era': '平成30年度 春 問5'},
            {'src': '05', 'prob': '問1', 'num': 6,  'era': '平成30年度 秋 問1'},
            {'src': '05', 'prob': '問2', 'num': 7,  'era': '平成30年度 秋 問2'},
            # 問3 not in data → no file 08
            {'src': '08', 'prob': '問1', 'num': 9,  'era': '平成30年度 秋 問4'},
            {'src': '08', 'prob': '問2', 'num': 10, 'era': '平成30年度 秋 問5'},
        ],
        'delete': ['08']  # old 08 (秋pm2) → content moved to 09,10; no target at 08
    },
    2019: {
        'sources': ['01', '04', '05', '06'],
        'targets': [
            {'src': '01', 'prob': '問1', 'num': 1,  'era': '平成31年度 春 問1'},
            {'src': '01', 'prob': '問2', 'num': 2,  'era': '平成31年度 春 問2'},
            {'src': '01', 'prob': '問3', 'num': 3,  'era': '平成31年度 春 問3'},
            {'src': '04', 'prob': '問1', 'num': 4,  'era': '平成31年度 春 問4'},
            {'src': '04', 'prob': '問2', 'num': 5,  'era': '平成31年度 春 問5'},
            {'src': '05', 'prob': '問1', 'num': 6,  'era': '令和元年度 秋 問1'},
            {'src': '05', 'prob': '問2', 'num': 7,  'era': '令和元年度 秋 問2'},
            {'src': '05', 'prob': '問3', 'num': 8,  'era': '令和元年度 秋 問3'},
            {'src': '06', 'prob': '問1', 'num': 9,  'era': '令和元年度 秋 問4'},
            # 問2 not in problems → no file 10
        ],
        'delete': []
    },
    2020: {
        'sources': ['01', '04'],
        'targets': [
            {'src': '01', 'prob': '問1', 'num': 1,  'era': '令和2年度 特別 問1'},
            {'src': '01', 'prob': '問2', 'num': 2,  'era': '令和2年度 特別 問2'},
            {'src': '01', 'prob': '問3', 'num': 3,  'era': '令和2年度 特別 問3'},
            {'src': '04', 'prob': '問1', 'num': 4,  'era': '令和2年度 特別 問4'},
            {'src': '04', 'prob': '問2', 'num': 5,  'era': '令和2年度 特別 問5'},
        ],
        'delete': []
    },
    2021: {
        'sources': ['01', '04', '05', '08'],
        'targets': [
            {'src': '01', 'prob': '問1', 'num': 1,  'era': '令和3年度 春 問1'},
            {'src': '01', 'prob': '問2', 'num': 2,  'era': '令和3年度 春 問2'},
            {'src': '01', 'prob': '問3', 'num': 3,  'era': '令和3年度 春 問3'},
            {'src': '04', 'prob': '問1', 'num': 4,  'era': '令和3年度 春 問4'},
            {'src': '04', 'prob': '問2', 'num': 5,  'era': '令和3年度 春 問5'},
            {'src': '05', 'prob': '問1', 'num': 6,  'era': '令和3年度 秋 問1'},
            {'src': '05', 'prob': '問2', 'num': 7,  'era': '令和3年度 秋 問2'},
            {'src': '05', 'prob': '問3', 'num': 8,  'era': '令和3年度 秋 問3'},
            {'src': '08', 'prob': '問1', 'num': 9,  'era': '令和3年度 秋 問4'},
            {'src': '08', 'prob': '問2', 'num': 10, 'era': '令和3年度 秋 問5'},
        ],
        'delete': []
    },
    2022: {
        'sources': ['01', '04', '05', '08'],
        'targets': [
            {'src': '01', 'prob': '問1', 'num': 1,  'era': '令和4年度 春 問1'},
            {'src': '01', 'prob': '問2', 'num': 2,  'era': '令和4年度 春 問2'},
            {'src': '01', 'prob': '問3', 'num': 3,  'era': '令和4年度 春 問3'},
            {'src': '04', 'prob': '問1', 'num': 4,  'era': '令和4年度 春 問4'},
            {'src': '05', 'prob': '問1', 'num': 5,  'era': '令和4年度 秋 問1'},
            # 秋pm1 問2,問3 not in data → no files 06,07
            {'src': '08', 'prob': '問1', 'num': 8,  'era': '令和4年度 秋 問4'},
        ],
        'delete': []
    },
}

def process_year(year):
    config = configs[year]
    year_dir = os.path.join(BASE_DIR, str(year))
    print(f"\n=== {year} ===")

    # Read all sources first before any writes
    source_data = {}
    for src in config['sources']:
        try:
            source_data[src] = load_json(year, src)
            print(f"  Loaded {src}.json")
        except FileNotFoundError:
            print(f"  WARNING: {src}.json not found!")
            source_data[src] = None

    # Write target files
    for t in config['targets']:
        src, prob, num, era = t['src'], t['prob'], t['num'], t['era']
        if source_data.get(src) is None:
            print(f"  SKIP {num:02d}.json: source {src}.json not available")
            continue
        problem = get_item(source_data[src].get('problems', []), prob)
        if problem is None:
            print(f"  SKIP {num:02d}.json ({era}): {prob} not found in problems")
            continue
        explanation = get_item(source_data[src].get('explanations', []), prob)
        write_json(year, num, era, problem, explanation)

    # Delete files that should no longer exist
    for fname in config['delete']:
        path = os.path.join(year_dir, f"{fname}.json")
        if os.path.exists(path):
            os.remove(path)
            print(f"  Deleted {year}/{fname}.json")

if __name__ == '__main__':
    for year in [2017, 2018, 2019, 2020, 2021, 2022]:
        process_year(year)
    print("\nDone!")
