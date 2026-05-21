# SC 午後問題まとめ

情報処理安全確保支援士試験の午後問題を閲覧するための静的サイトです。

## 構成

```
sc-pm-problem/
├── data/exams/          # 試験データ（JSON）
├── docs/                # 生成された静的HTML（GitHub Pages公開先）
│   ├── assets/          # CSS
│   ├── exams/           # 各試験のHTMLページ
│   └── images/          # 試験に差し込む図・表の画像
├── pdf/                 # OCR処理前のPDF置き場（処理後は削除）
└── scripts/
    ├── ocr_pdf.py       # PDF → JSON（macOS Vision OCR）
    ├── restructure_json.py  # 旧フラット形式 → ブロック形式へ移行
    └── build_html.py    # JSON → 静的HTML
```

## セットアップ

macOS + Python 3.11以上が必要です。

```bash
pip install pyobjc-framework-Vision pyobjc-framework-Foundation Pillow
brew install poppler   # pdftoppm コマンド
```

## 使い方

### 1. OCR（PDF → JSON）

```bash
# 1ファイル
python3 scripts/ocr_pdf.py pdf/2024r06a_sc_pm_qs.pdf

# まとめて全部
python3 scripts/ocr_pdf.py --all

# 上書き再実行
python3 scripts/ocr_pdf.py --force pdf/2024r06a_sc_pm_qs.pdf
```

PDFのファイル名形式: `{year}{era}{period}_sc_pm{split}_{qs|ans}.pdf`

例: `2024r06a_sc_pm_qs.pdf`（令和6年度秋期 午後）、`2022r04h_sc_pm1_qs.pdf`（令和4年度春期 午後I）

処理が終わったPDFは削除してください（リポジトリには含めません）。

### 2. HTMLビルド

```bash
python3 scripts/build_html.py
```

`docs/` 以下に静的HTMLが生成されます。`docs/index.html` をブラウザで開くと確認できます。

## JSONスキーマ

`data/exams/*.json` を直接編集して内容を修正できます。

### ブロック種別

| type | 説明 |
|------|------|
| `text` | 本文テキスト（`content` フィールド） |
| `image` | 図・表の画像（`src`, `caption` フィールド） |
| `figure` | 枠線付きテキストボックス（`content`, `caption` フィールド） |
| `table` | 表（`caption`, `headers`, `rows` フィールド） |
| `dialogue` | 会話形式（`lines: [{speaker, text}]` フィールド） |

### インラインマークアップ

`content` や `text` フィールド内で使用できます。

| 記法 | 表示 |
|------|------|
| `[[u:テキスト]]` | <u>テキスト</u>（下線） |

### 例

```json
{
  "id": "2024r06a_sc_pm",
  "year": 2024,
  "era_label": "令和6年度",
  "period": "秋",
  "split": null,
  "exam_label": "午後",
  "label": "令和6年度秋試験 午後",
  "problems": [
    {
      "page": 1,
      "items": []
    },
    {
      "page": 2,
      "items": [
        { "type": "text", "content": "問1　..." },
        { "type": "image", "src": "images/2024r06a_sc_pm/01.png", "caption": "図1" },
        {
          "type": "table",
          "caption": "表1　一覧",
          "headers": ["番号", "名称", "説明"],
          "rows": [
            ["1", "foo", "説明文"]
          ]
        }
      ]
    }
  ],
  "answer_pages": []
}
```

## 画像の追加

`docs/images/{exam_id}/` に画像を置き、JSONの `src` フィールドに `images/{exam_id}/01.png` のように記述します（先頭の `/` は不要）。
