# ラスト・ライ 漫画生成プロジェクト

`ストーリー.md`と`漫画制作仕様書.md`をもとに、OpenAI Images APIの`gpt-image-2`で表紙と24ページ漫画を生成するためのプロジェクトです。

生成済み画像は`images/`にあり、`index.html`でブラウザ確認できます。

## 現在の成果物

- 表紙: `images/cover.png`
- キャラクター相関図: `images/character_relationship.png`
- 本文24ページ: `images/pages/page_01.png`から`images/pages/page_24.png`
- キャラクター参照画像: `images/reference/*.png`
- 漫画ビューア: `index.html`
- ページ生成プロンプト: `production/page_prompts/*.md`
- 相関図生成プロンプト: `production/relationship_prompt.md`
- キャラクター設定資料: `production/character_sheets/*.md`

## 表示方法

ローカルで`index.html`を開くと、表紙と本文24ページを確認できます。

```powershell
start index.html
```

`index.html`には、1ページ表示と見開き表示の切り替え、ページジャンプを入れています。

## 重要な制作方針

- モデルは`gpt-image-2`を使用します。
- 品質は`medium`です。
- キャラクターは`production/character_sheets`と`images/reference`を基準にします。
- 各ページ生成時は、登場キャラに必要な参照画像だけをAPIへ渡します。
- セリフは後処理ではなく、`gpt-image-2`へ指示して画像内の吹き出しに直接入れます。
- セリフは`「」`の中身だけを入れ、話者名やキャラ名は入れません。
- コマ割りは均等グリッドを避け、日本漫画らしい大ゴマ、斜め割り、破断コマ、速度線、黒ベタ、余白を使う方針です。

## ディレクトリ構成

```text
.
├── index.html
├── manga_config.json
├── README.md
├── scripts/
│   ├── prepare_manga.py
│   ├── generate_images.py
│   └── letter_pages.py
├── production/
│   ├── character_sheets/
│   ├── page_prompts/
│   ├── manifest.json
│   ├── cover_prompt.md
│   ├── dialogue_script.md
│   └── style_bible.md
├── images/
│   ├── cover.png
│   ├── pages/
│   └── reference/
├── ストーリー.md
└── 漫画制作仕様書.md
```

## 設定

主要設定は`manga_config.json`にあります。

```json
{
  "model": "gpt-image-2",
  "quality": "medium",
  "size": "1024x1536",
  "output_format": "png",
  "use_reference_images": true
}
```

APIキーは`.env`の`OPENAI_API_KEY`から読み込まれます。`.env`は`.gitignore`で除外しています。

## プロンプト再生成

`ストーリー.md`や`漫画制作仕様書.md`、または`scripts/prepare_manga.py`を変更した場合は、まず制作プロンプトを再生成します。

```powershell
python scripts/prepare_manga.py
```

生成される主なファイル:

- `production/cover_prompt.md`
- `production/page_prompts/page_01.md`から`page_24.md`
- `production/character_sheets/*.md`
- `production/dialogue_script.md`
- `production/manifest.json`

## 画像生成

APIを呼ばずにpayloadだけ確認する場合:

```powershell
python scripts/generate_images.py --cover --dry-run
python scripts/generate_images.py --pages 1 --dry-run
```

表紙だけ再生成:

```powershell
python scripts/generate_images.py --cover
```

1ページだけ再生成:

```powershell
python scripts/generate_images.py --pages 1
```

複数ページを再生成:

```powershell
python scripts/generate_images.py --pages 1-3
python scripts/generate_images.py --pages 1,5,20
```

表紙と24ページをまとめて再生成:

```powershell
python scripts/generate_images.py --cover --pages 1-24 --sleep 1
```

通信断が起きた場合は、最後に失敗したページから再開してください。

```powershell
python scripts/generate_images.py --pages 11-24 --sleep 2
```

## キャラクター参照画像

参照画像は以下です。

- `images/reference/mai.png`
- `images/reference/akari.png`
- `images/reference/toya.png`
- `images/reference/grave.png`
- `images/reference/echo.png`

設定資料Markdownには、それぞれ対応する参照画像へのリンクが入っています。

- `production/character_sheets/mai.md`
- `production/character_sheets/akari.md`
- `production/character_sheets/toya.md`
- `production/character_sheets/grave.md`
- `production/character_sheets/echo.md`

キャラクターが入れ替わらないよう、`production/manifest.json`では各ページごとに`reference_keys`を持たせています。`scripts/generate_images.py`はこの`reference_keys`に従い、登場キャラに必要な参照画像だけをAPIへ送ります。

## セリフの扱い

ページプロンプトでは、吹き出しに入れる文字を`「」`の中身だけにしています。

例:

```text
透也
「目を見たから」
```

画像に入れる文字:

```text
目を見たから
```

話者名、`Panel`、`place in`、ページ番号、メタ情報は画像内に入れないように指示しています。

## 既存の写植スクリプトについて

`scripts/letter_pages.py`は、以前の後処理写植用スクリプトとして残しています。現在の制作方針では、セリフは`gpt-image-2`に画像内へ直接入れさせるため、通常は使いません。

## 注意点

- `.env`にはAPIキーが入るため共有しないでください。
- `images/pages`の画像を再生成すると既存ページは上書きされます。
- `gpt-image-2`による日本語文字は生成品質に揺れがあります。誤字が目立つページは、そのページだけ再生成してください。
- キャラが混同されたページは、該当ページの`production/page_prompts/page_XX.md`と`reference_keys`を確認してから再生成してください。
