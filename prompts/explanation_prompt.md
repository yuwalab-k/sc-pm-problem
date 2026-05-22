# 解説生成プロンプト

ユーザーが「**[年度表記]解説作って**」と言ったときの作業手順と品質基準。

---

## ステップ0: ファイル名の特定

年度表記とJSONファイル名の対応:

| ユーザー表記の例 | JSONファイル名 |
|---|---|
| 令和7年度春 / 2025春 | `2025r07h_sc_pm.json` |
| 令和7年度秋 / 2025秋 | `2025r07a_sc_pm.json` |
| 令和6年度春 / 2024春 | `2024r06h_sc_pm.json` |
| 令和6年度秋 / 2024秋 | `2024r06a_sc_pm.json` |
| 令和5年度秋 / 2023秋 | `2023r05a_sc_pm.json` |
| 令和5年度春午後I | `2023r05h_sc_pm1.json` |
| 令和5年度春午後II | `2023r05h_sc_pm2.json` |
| 令和4年度春午後I | `2022r04h_sc_pm1.json` |
| 令和4年度秋午後I | `2022r04a_sc_pm1.json` |
| 令和4年度春午後II | `2022r04h_sc_pm2.json` |
| 令和4年度秋午後II | `2022r04a_sc_pm2.json` |
| （以降同パターン） | |

ファイルは `data/exams/` 以下にある。

---

## ステップ1: 対象年度の確認

### 令和7年度（2025r07h / 2025r07a）
- 問題文・解答ともに人手で確認済み → **解説のみ更新すればよい**

### 令和6年度以前（2024r06h〜）
- OCRで取り込んだまま → **問題文・解答自体に誤りがある可能性がある**
- 解説を書く前に、まず下記を確認・修正する:
  1. 解答の明らかな誤字・脱字・文字化け
  2. 問題文（`pages`の`text`ブロック）の誤認識（句読点・括弧・数字の混入等）
  3. 修正した箇所をユーザーに報告してから解説作成に進む

---

## ステップ2: 問題内容の把握

1. `data/exams/[ファイル名].json` を読み込む
2. 対応する `docs/exams/[ファイル名].html` も参照して問題文の文脈を把握する
3. 各設問（`items[].label`）が何を問うているかを整理する

---

## ステップ3: 解説の作成

### 品質基準（最重要）

各解説は **250文字以上** を目安に書く（現状の約2倍以上）。

| 要素 | 内容 |
|---|---|
| なぜその答えか | 「○○だから正解はXX」という論拠を明示 |
| 問題文への紐付け | 「本文の△行目」「表1の項番◯」「図◯のシーケンス」など |
| 背景知識 | 使われているセキュリティ概念・標準・フレームワークの説明 |
| 誤答トラップ | 紛らわしい選択肢・間違えやすいポイントへの言及 |
| 実世界での意味 | 実際の現場でどう使われる概念かの一言補足 |

### 禁止事項
- 「答えはXXです。」だけの1文解説
- 問題文をそのまま引用して終わり
- 抽象的な説明のみ（「セキュリティ上問題があります」等）

---

## ステップ4: JSONへの適用

1. 新しい解説を `/tmp/expls_[ファイル名のベース].json` に書き出す

   フォーマット:
   ```json
   {
     "問1": {
       "設問1(1)": "解説テキスト...",
       "設問1(2)": "解説テキスト...",
       ...
     },
     "問2": { ... },
     ...
   }
   ```

2. 下記Pythonスクリプトで適用する:
   ```python
   import json
   
   with open('data/exams/[ファイル名].json') as f:
       data = json.load(f)
   with open('/tmp/expls_[ベース名].json') as f:
       new_expls = json.load(f)
   
   matched = 0
   for prob in data['explanations']:
       pkey = prob['problem']
       if pkey not in new_expls:
           continue
       for item in prob['items']:
           if item['label'] in new_expls[pkey]:
               item['explanation'] = new_expls[pkey][item['label']]
               matched += 1
   
   print(f"Matched: {matched}")
   with open('data/exams/[ファイル名].json', 'w', encoding='utf-8') as f:
       json.dump(data, f, ensure_ascii=False, indent=2)
   ```

3. `python3 scripts/build_html.py` を実行してHTMLを再ビルドする

---

## ステップ5: 完了確認

- 全items数と matched数が一致すること
- 解説の平均文字数が250字以上であること（以下コマンドで確認）:
  ```bash
  python3 -c "
  import json
  with open('data/exams/[ファイル名].json') as f:
      data = json.load(f)
  lengths = [len(item.get('explanation','')) for p in data['explanations'] for item in p['items']]
  print(f'items: {len(lengths)}, avg: {sum(lengths)/len(lengths):.0f}, min: {min(lengths)}')
  "
  ```

---

## 注意事項

- JSONファイルを直接テキスト編集するのではなく、必ずWriteツールかPythonスクリプト経由で更新する（エンコーディング事故防止）
- backtick文字（`` ` ``）を解説テキストに含める場合、JSONのエスケープは不要だが、Pythonヒアドキュメントには入れないこと
- HTMLファイルは `scripts/build_html.py` のビルドで自動生成されるため直接編集しない
