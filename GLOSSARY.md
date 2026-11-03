# Fizgig 日本語化 翻訳指針（翻訳担当用）

対象は LoRA / ファインチューニング用ワークベンチ「Fizgig」の Web UI。利用者は日本の画像・動画生成ユーザー。
翻訳は**英語原文を基準**にする（他言語の訳は参照しない）。

## 出力形式（厳守）
- 入力 JSON の**キー（英語原文）は一字も変えず**、値だけを日本語にした純粋な JSON を出力する。説明・コードフェンス禁止。
- 翻訳してはいけないもの（コード識別子、ファイルパス、設定キー、CLI フラグ、モデルのリポジトリ ID、意味不明の断片、
  ハッシュ値、プロンプト例・読み上げ用の英文サンプル）は値を空文字 `""` にする。
- `{0}` `{1}` などのプレースホルダーは**個数も番号も保つ**（順序は日本語の語順に合わせて変えてよい）。
  英語の複数形接尾辞（`clip{1}` の `{1}` = `s` か空）は日本語に不要なので、日本語側に**残さなくてよい**（取り込み時の検査が許可する）。
- 改行 `\n`、前後の空白、末尾の `:` `…` `.`、絵文字・記号（⚠ ✓ ✗ ● ▶ — · ×）は保つ。
  末尾のコロンは半角 `:` のまま。ラベルの `Seed:` → `シード:`。
- 数値・単位（GB, MB, px, fps, s）はそのまま。全角数字にしない。

## 文体
- ボタン・タブ・ラベル・見出し: 短い体言止め（`Start Training` → `学習を開始`）。
- 説明・ツールチップ・警告・エラー: です・ます調。「〜してください」「〜できません」。冗長にしない。
- 直訳調（「〜することができます」の連発など）を避け、自然な日本語にする。
- 他の UI 要素を引用符で指す文は、下の用語集の訳名に合わせる。

## 用語集（必ず統一）
| 英語 | 日本語 |
|---|---|
| Fizgig, Klein, Krea 2, MiniMax H3, Flux, Qwen, Z-Image, SDXL, Anima, MOSS-Image, RunPod, ComfyUI, HuggingFace, Whisper, Florence, LoRA, LoKr, DiT, VAE, CUDA, GPU, VRAM, RAM, fp8, bf16, int8, nf4, ffmpeg, safetensors, JSON, PNG, MP4, WAV, CFG, LLM, API | そのまま（英字） |
| Repair Studio, LoRA the Explorer, LoRA Royale, RefMod Studio, RefMod, ReFLoRA, Lucky, Workbench | 機能名は英字のまま（説明文中の一般名詞の用法だけ訳す） |
| Start (tab) | スタート |
| Image Prep / Prep | 画像準備 |
| Caption(s) / captioning | キャプション |
| Sample(s) | サンプル |
| Training / train | 学習 / 学習する |
| Fine-tune / fine-tuning | ファインチューニング |
| Profiler / profile | プロファイラー / プロファイル |
| Extract / extraction | 抽出 |
| Metadata | メタデータ |
| Preferences | 環境設定 |
| About | 情報 |
| Queue / queued | キュー / キューに追加済み |
| Browse… | 参照… |
| Cancel / Stop / Close | キャンセル / 停止 / 閉じる |
| Save / Load | 保存 / 読み込み |
| Update | アップデート |
| Refresh | 再読み込み |
| Reset / Remove / Delete / Clear | リセット / 外す / 削除 / クリア |
| Open / Export / Import | 開く / エクスポート / インポート |
| Preset | プリセット |
| Dataset | データセット |
| Trigger word | トリガーワード |
| Prompt / Negative prompt | プロンプト / ネガティブプロンプト |
| Seed | シード |
| Epoch(s) | エポック |
| Step(s) | ステップ |
| Batch size | バッチサイズ |
| Learning rate (LR) | 学習率（LR） |
| Rank / Network Dim / Alpha | ランク / ネットワーク次元 / アルファ |
| Timestep(s) | タイムステップ |
| Noise / low-noise / high-noise | ノイズ / 低ノイズ / 高ノイズ |
| Resolution | 解像度 |
| Checkpoint | チェックポイント |
| Resume / Pause | 再開 / 一時停止 |
| Gradient checkpointing / accumulation | 勾配チェックポイント / 勾配蓄積 |
| Block(s) / Block swap / Blocks to Train | ブロック / ブロックスワップ / 学習するブロック |
| Offload(ing) | オフロード |
| Text encoder | テキストエンコーダー |
| Cache / caching | キャッシュ / キャッシュ作成 |
| Face crop / face detection | 顔クロップ / 顔検出 |
| Likeness | 類似度 |
| Identity | アイデンティティ |
| Style / Composition | スタイル / 構図 |
| Reference | リファレンス |
| Donor LoRA / Primary LoRA | ドナーLoRA / メインLoRA |
| Strength | 強度 |
| Variant(s) | バリエーション |
| Waypoint(s) / Keyframe | ウェイポイント / キーフレーム |
| Frame(s) / clip(s) / take(s) | フレーム / クリップ / テイク |
| Transcribe / transcription | 文字起こし |
| Preview | プレビュー |
| Console / log | コンソール / ログ |
| Pod | Pod |
| Regularisation images | 正則化画像 |
| Baseline / Tweaked | ベースライン / 調整後 |
| Slider / Edit / Standard LoRA | スライダー / 編集 / 標準 LoRA |
| Rotation / window (fine-tune) | ローテーション / ウィンドウ |
| Ready. / Done. / Busy | 準備完了。 / 完了。 / 処理中 |
| Off / On / Auto / None / All / Custom | オフ / オン / 自動 / なし / すべて / カスタム |
| Yes / No / OK | はい / いいえ / OK |

## 注意
- ComfyUI のノード名・ウィジェット名・設定値（`Apply`, `Step Curve`, `Scramble seed`, `refmod_retention`, `models/refmods` など）は
  利用者が ComfyUI でそのまま探す名前なので**英字のまま**にし、周囲の説明だけ日本語にする。
- アプリのコードが画面文字と比較する `Web UI` / `Show mask` / `Hide` は翻訳禁止（値 `""`）。
- 同じ英語は全体で同じ訳にする。上の用語集が最優先。
