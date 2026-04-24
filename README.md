# アンドロイド・レクイエム 漫画生成セット

`ストーリー.md`と`漫画制作仕様書.md`をもとに、OpenAI Images APIで漫画ページを生成するための準備一式です。

## 構成

- `manga_config.json`: モデル、品質、サイズ、出力先の設定
- `scripts/prepare_manga.py`: 24ページ分の生成プロンプト、台詞台本、チェックリストを作成
- `scripts/generate_images.py`: OpenAI Images APIで任意の表紙・ページを生成。`images/reference`を参照画像として送信
- `scripts/letter_pages.py`: 生成済みページへ日本語台詞を縦書き写植
- `production/`: 生成プロンプト類の出力先
- `images/`: 画像出力先

## 初期準備

```powershell
python scripts/prepare_manga.py
```

## 疎通確認

APIを呼ばずに、送信予定のpayloadだけ確認します。

```powershell
python scripts/generate_images.py --cover --dry-run
python scripts/generate_images.py --characters mai --dry-run
python scripts/generate_images.py --pages 1 --dry-run
```

## 画像生成

まずは表紙か1ページだけで確認してください。ページ生成では`images/reference`の設定資料画像を参照画像としてAPIに渡します。

```powershell
python scripts/generate_images.py --characters mai
python scripts/generate_images.py --cover
python scripts/generate_images.py --pages 1
python scripts/letter_pages.py --pages 1
```

キャラクター固定用の三面図をまとめて生成する場合:

```powershell
python scripts/generate_images.py --characters all
```

複数ページを生成する場合:

```powershell
python scripts/generate_images.py --pages 1-3
python scripts/generate_images.py --pages 1,5,20
```

生成後に写植する場合:

```powershell
python scripts/letter_pages.py --pages 1-24
```

## モデル名について

`manga_config.json`の既定値は`gpt-image-2`、品質は`medium`にしています。

公式ドキュメント上で利用可能なモデル名が環境と異なる場合は、コマンドで一時的に上書きできます。

```powershell
python scripts/generate_images.py --pages 1 --model gpt-image-1.5
```

または`manga_config.json`の`model`を書き換えてください。

## 制作上の注意

生成画像には台詞文字を描き込ませず、白い吹き出し余白を作らせます。日本語台詞は`production/lettering.json`をもとに`scripts/letter_pages.py`で後工程として正確に入れます。

P20の「必ず、生きて戻ってきます」は作品の最重要コマです。マアイを大きく笑わせず、微笑未満の表情にしてください。
