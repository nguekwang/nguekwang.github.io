# nguekwang.github.io

Yoshihiro (Yoshi) MATSUURA の研究者サイト。https://nguekwang.github.io/

## 文言の直し方

文言はすべて `data/` の TOML ファイルにあります。HTML は直接編集しません。

| ファイル | 中身 |
|---|---|
| `data/site.toml` | 名前、メール、卒論タイトル、言語の並び順など、言語によらない値 |
| `data/i18n/<言語コード>.toml` | その言語版の文言(研究の一文、研究関心、プロジェクトなど) |
| `data/keywords.toml` | キーワード。1語 = 1つの `[[keyword]]`、全言語ぶんの訳を持つ |
| `data/talks.toml` | 最新の発表。1件 = 1つの `[[talk]]` |

GitHub 上でこれらを編集して main にコミットすると、GitHub Actions(`.github/workflows/build.yml`)が `tools/build.py` を実行し、各言語の `index.html` と `sitemap.xml` を作り直してコミットします。

手元で作り直す場合: `python3 tools/build.py`(Python 3.11 以上、追加パッケージ不要)

## 構成

- `/` 言語の振り分けページ(ブラウザの言語に合う版へ移動)
- `/<言語コード>/` 各言語版(21言語)。`ar` と `fa` は右から左
- `tools/build.py` ページ生成、`tools/content.py` data/ の読み込み
