# Fizgig 日本語化アドオン

[Fizgig](https://github.com/shootthesound/Fizgig)（LoRA / ファインチューニング用ワークベンチ）の画面を、**実行時に**日本語へ置き換えるアドオンです。
タブ、ボタン、設定項目、説明文、ツールチップ、警告・エラー、ドロップダウンの項目まで翻訳します。

> **非公式の有志による日本語化です。** Fizgig の作者（Peter Neill / shootthesound）とは無関係で、公式の配布物ではありません。
> Fizgig 本体はこのフォルダーに含まれません。Fizgig は[公式リポジトリ](https://github.com/shootthesound/Fizgig)から導入し、その上にこのアドオンを重ねます。

- **Fizgig の本体ファイルは 1 文字も変更しません。** `update_fizgig.bat`（= `git pull`）で Fizgig を更新しても衝突せず、日本語も英語へ戻りません。
- 対象は **Fizgig 8 以降の Web UI**（メイン画面）です。基準は 2026-11-02 時点の `main`。少し前の版（2026-10 下旬）の言い回しも辞書に入れてあるので、旧版でもほぼ日本語で表示されます。新しく増えた文言だけは英語のまま表示され、アプリの動作には影響しません。
- Windows 11 で動作確認しています（RTX 5090 の実機でも確認）。
- 辞書は約 3,700 件（レポートは [`REPORT.md`](REPORT.md)）。

## インストール

Fizgig を導入済み（`venv` フォルダーがある）の状態で、**Fizgig のフォルダーの中**にこのフォルダーを置きます。フォルダー名は何でも構いません（例: `ja`）。

```
cd <Fizgig のフォルダー>
git clone https://github.com/ramp-007/Fizgig-Japanese-Translated-Ver.git ja
ja\install_ja.bat
```

ZIP で入手した場合は、展開したフォルダーを Fizgig のフォルダーの中へ移し、`install_ja.bat` をダブルクリックします。
Fizgig のフォルダーの外に置いたときは、`install_ja.bat "C:\path\to\Fizgig"` のようにパスを渡します。

導入が終わったら、いつも通り `Launch Fizgig.bat`（アプリ窓）または `Launch Fizgig in browser.bat`（ブラウザー）で起動してください。
何度実行しても安全です。

## 使い方

- 起動すると画面は日本語です。**右下の小さな「EN」ボタン**で英語表示に切り替えられます（ブラウザーに記憶されます）。英語表示のときは同じ場所に「日本語にする」と出ます。
- 一度だけ英語で見たいときは、アドレスの末尾に `?ja=off` を付けます（`?ja=on` で日本語に戻ります）。
- サーバー側で完全に無効にするときは、環境変数 `FIZGIG_LANG=en` を付けて起動します。
- 翻訳は画面の文字を置き換えるだけです。入力欄の値、プロンプト、キャプション、パス、設定キー、ログ（`<pre>`）、保存されるデータは変更しません。

## 更新

| 更新するもの | 方法 |
|---|---|
| Fizgig 本体 | これまで通り `update_fizgig.bat`。日本語化は維持されます。 |
| このアドオン（辞書など） | このフォルダーで `git pull` して、Fizgig を再起動（ブラウザーは Ctrl+F5） |
| `venv` を作り直したとき（`install_fizgig.bat` を再実行したとき） | `install_ja.bat` をもう一度実行 |

## アンインストール

`uninstall_ja.bat` を実行します。venv に置いた `fizgig_ja.pth` を 1 つ消すだけで、Fizgig 側には何も残りません。
その後、このフォルダーを削除して構いません。

## しくみ

導入されるのは `venv\Lib\site-packages\fizgig_ja.pth` の 1 行だけです（`.git/info/exclude` へのフォルダー名の追記を除く）。Python の起動時にこの行が `fizgig_ja` を読み込み、
`fizgig.web.server` が import された瞬間にだけフックを掛けます。サーバーがメインページを返すときに、翻訳スクリプトと辞書をページの末尾へ差し込みます。
ブラウザー側で画面の文字・`title`・`placeholder`・`aria-label`・選択肢を辞書で置き換え、`MutationObserver` で後から描画される部分も追いかけます。
学習のサブプロセスなど、そのモジュールを使わないプロセスには何も起こりません。失敗してもアプリは動き続け、エラーは `ja_error.log` にだけ書かれます。

## 翻訳を直す・増やす

- 気になる訳は `lib/fizgig_ja/overrides.json` に `"英語の原文": "好きな日本語"` を足してください（最後に読まれるので他の辞書を上書きします）。Fizgig を再起動し、ブラウザーを再読み込みすれば反映されます。
- 辞書の本体は `lib/fizgig_ja/strings_web/`（`web.json` が主、`structure.json` は文の組み立て用テンプレート、`zz_manual.json` は手直し、`zz_compat.json` は古い Fizgig の言い回し用）です。
- 用語は [`GLOSSARY.md`](GLOSSARY.md) に揃えてあります（エポック、学習率、バッチサイズ、キャプション、学習 など）。LoRA / VRAM / CUDA / モデル名 / パラメーター名は英語のままです。

### Fizgig の更新で増えた文言を翻訳する（開発者向け）

Node.js と Playwright が必要です（`cd tools && npm install --ignore-scripts`、`pip install playwright`。Windows では Edge / Chrome を自動で使います）。

```
python tools/extract_web.py --fizgig <Fizgig のフォルダー>        # ソースから候補を集める → work/web_missing.json
python tools/harvest_web.py --fizgig <Fizgig のフォルダー>        # 全タブを実際に開いて画面の文言を集める → work/web_runtime.json
python tools/extract_web.py --fizgig <Fizgig のフォルダー>        # 画面の結果も合わせて再計算
python tools/chunks.py split 300                                  # work/chunks/*.json に分割
（work/out_web/*.json に {"英語": "日本語"} の形で翻訳を保存。訳さないものは ""）
python tools/chunks.py merge                                      # 検査して web.json に統合
python tools/harvest_web.py --fizgig <Fizgig のフォルダー> --check --shots work/shots   # 翻訳を有効にして、残った英語を点検
python tools/e2e.py --fizgig <Fizgig のフォルダー>                # 実機（venv 入りの Fizgig）での切り替え・無効化の検査
python tests/run_tests.py                                         # 単体テスト
```

訳さない文言（パス、キー、モデル名など）は `tools/web_keep_english.json` に書きます。`merge` は、プレースホルダー（`{0}`）の不一致、日本語の欠落、保護された文言（`Web UI` / `Show mask` / `Hide`）の翻訳を弾きます。

## 既知の問題

- **Gizmo（Tk 製の別ウィンドウ）と Fizgig 7 以前は対象外です。** 韓国語化版が持っていた Tk 側の翻訳層は取り込んでいません。
- Fizgig が文言を変えたり足したりすると、その文言だけが英語に戻ります（機能の不具合ではありません）。上の手順で追加できます。
- 次のものは**意図的に翻訳していません**: 音声録音用の英語の読み上げ文、キャプション・プロンプト入力欄の既定値（モデルへそのまま送られる文字列）、プロンプト用の単語リスト（`a woman` など）、プリセット・モデル・機能名（Studio / LoRA Royale / RefMod Toolkit など）、ComfyUI のノード名・設定値、ファイル名・パス・キー名、学習サブプロセスのログ、HTML ギャラリー。
- 長めの日本語でボタンやラベルが折り返す箇所があります。サイドバー上部の副題（「LoRA & ファインチューニング スタジオ」）が右端で切れて見えます。
- 翻訳は機械翻訳（Claude）を用語集で揃え、全タブを実際に開いて確認したものです。不自然な箇所が残っている可能性があります。
- 実際の LoRA 学習・Pod の起動・デプロイなど、費用や長時間のかかる操作は検証していません（検証では押していません）。

## 不具合を報告する前に

Fizgig 公式のリポジトリへ報告する前に、`uninstall_ja.bat` で日本語化を外して再現するか確認してください。外しても再現するなら
[Fizgig の Issue](https://github.com/shootthesound/Fizgig/issues) へ、外すと消えるならこのアドオンの Issue へお願いします。

## ライセンス

**Apache License 2.0** です。[`LICENSE`](LICENSE) と [`NOTICE`](NOTICE) を参照してください。
このアドオンは、同じく Apache-2.0 の [Fizgig 韓国語化アドオン](https://github.com/ssain3d-lgtm/Fizgig-Korean-Translated-Ver)（Copyright 2026 ssain3d-lgtm and contributors）の構造・フック・ツールを改変して再利用しています（派生ファイルの先頭に「Modified from」と明記しています）。韓国語の訳は使っていません。
辞書の英語キーは、Fizgig（Apache-2.0, Copyright 2026 Peter Neill）のソースから取り出した UI 文字列で、日本語の値はこのプロジェクトの翻訳です。Fizgig のソースファイルは含まれません。

無保証（AS IS）です。詳細はライセンス本文を参照してください。
