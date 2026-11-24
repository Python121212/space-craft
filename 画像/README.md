# 画像

**ここはユーザーが「こんなテクスチャにして」「この色・模様に近づけて」という見本・要望画像を置く場所**です。
エージェントは勝手に削除・改名・整理せず、置かれた PNG を **テクスチャの正式な source** として扱います。

## 置いてあるもの

| ファイル | 内容 |
| --- | --- |
| `ここに追加` | ユーザー作成のプレースホルダ（**残す**） |
| `自分が追加` | ユーザー作成のプレースホルダ（**残す**） |
| `IMG_809df39f-4a58-433f-b6f5-0b58e51e80d2.png` | 現在のレンチの見本。256×256 のインデックスカラー PNG＝**16×16 ドット絵を 16 倍に拡大**したもの。白背景・黒アウトライン・銀のグラデーション、斜めの柄と U 字の開口 |

## 見本がどう使われるか

```bash
python3 tools/itemart.py wrench
```

1. [`tools/model3d.py`](../tools/model3d.py) の `read_png` が見本を読みます
   （インデックスカラー / RGB / RGBA / 透過 / 全 PNG filter / tRNS に対応。標準ライブラリのみ）
2. **16×16 にダウンサンプル**し、真っ白 `#ffffff` の背景だけを透過に変換して
   [`../src/main/resources/assets/spacecraft/textures/item/wrench.png`](../src/main/resources/assets/spacecraft/textures/item/wrench.png) へ書き出します
3. 3D モデル [`../src/main/resources/assets/spacecraft/models/item/wrench.json`](../src/main/resources/assets/spacecraft/models/item/wrench.json) の
   各面 `faces.<面>.uv` が、**その 16×16 テクスチャ上の実ピクセル**を指します
4. `model3d.py` が同じ `uv` の色で 3D SVG の面を塗るため、
   **ゲーム内のテクスチャ・3D モデル・一覧の 3 枚の画像はすべて同じ見本画像由来の配色**になります

現在の `uv` は見本から抽出した実色です:

| 役割 | uv | 色 |
| --- | --- | --- |
| 上面（ハイライト） | `(9,4)` | `#f6f6f6` |
| 側面（中間） | `(9,6)` | `#c5c5c5` |
| 下面（影） | `(10,6)` | `#9f9f9f` |
| アウトライン | `(8,5)` | `#282828` |
| グリップの別階調 | `(9,7)` | `#a8a8a8` |

## 見本を差し替えたいとき

1. このフォルダに PNG を置く（または既存ファイルを上書きする）
2. [`../tools/itemart.py`](../tools/itemart.py) の `SOURCE_FILES` に `<id>: ファイル名` を登録する
3. 必要なら同ファイルの `UV_*` を、新しい見本の**不透明ピクセル**に合わせて調整する
   （透明ピクセルを指すと 3D 画像が既定色にフォールバックします）
4. `python3 tools/itemart.py <id>` を実行し、`python3 tools/catalog.py check --strict` で確認する

> `UV_*` の調整を省略しても生成は動きますが、面の色が見本とずれます。
> 見本の実ピクセルは `python3 -c "import sys; sys.path.insert(0,'tools'); from model3d import read_png; ..."` で確認できます。

## ビルドとの関係

- このフォルダ自体はドキュメント扱いで、**一覧と同じく `paths-ignore` により CI は起動しません**。
- ただし生成先の `src/main/resources/assets/spacecraft/textures/item/` と `models/item/` は**実装**なので、`itemart.py` の実行結果を commit すると JDK 17 + Gradle 8.1.1 のビルドが走ります。

## 関連

- アイテムの詳細: [`../アイテム一覧/wrench.md`](../アイテム一覧/wrench.md)
- 全手順: [`../一覧の使い方.md`](../一覧の使い方.md)
- エージェントへの指示: [`../AGENTS.md`](../AGENTS.md)
