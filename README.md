# space-craft

**Minecraft 1.20.1 / Forge 用の宇宙クラフト mod** です。まずは道具から組み立てていきます。
**立体を持つ要素はすべて 3D モデル**で登録します（アイテム・ブロック・装備・エンティティ）。

## 現在の内容

| 要素 | id | 内容 |
| --- | --- | --- |
| **レンチ** | `spacecraft:wrench` | ブロックを右クリックすると `BlockState` を時計回りに 90 度回転。スタック 1・耐久なし |

- **3D モデル**: `block/block` 継承の `elements` 5 個（柄・グリップ・U 字の開口）で構成。インベントリ内・手持ち・三人称・地面に落ちた状態のすべてで立体として表示されます。
- **テクスチャ**: [`画像/`](画像/README.md) に置かれた見本（16×16 ドット絵の拡大 PNG）を source にしています。`itemart.py` が 16×16 へ落として白背景のみ透過し、各面の `uv` がその実ピクセル色を指すため、3D 画像の配色も見本と一致します。
- クリエイティブタブ「**宇宙クラフト**」（`spacecraft:spacecraft`）に登録済み。タブのアイコンもレンチです。
- 英語名 `Wrench` / 日本語名 `レンチ`（`lang/en_us.json` / `lang/ja_jp.json`）。
- アイテムの詳細・3 枚の 3D 画像は [`アイテム一覧/wrench.md`](アイテム一覧/wrench.md) にあります。

## 配布物

**配布物は GitHub Release に一本化しています。リポジトリ内に jar は置いていません。**

| 場所 | 内容 |
| --- | --- |
| [Release `v1.0.0`](https://github.com/Python121212/space-craft/releases/tag/v1.0.0) | `spacecraft-1.0.0.jar`（GitHub Actions が JDK 17 + Gradle 8.1.1 でビルドしたもの） |

```bash
gh release view v1.0.0
gh release download v1.0.0 -p '*.jar'
```

直接ダウンロード: https://github.com/Python121212/space-craft/releases/download/v1.0.0/spacecraft-1.0.0.jar

## GitHub Actions でのビルドとリリース

`.github/workflows/build.yml` が `main` と `arena/**` への push（および手動実行）で動きます。

1. JDK 17 (temurin) と Gradle 8.1.1 を用意
2. `gradle build` で `build/libs/spacecraft-1.0.0.jar` を生成
3. `jar tf` / `mods.toml` / `pack.mcmeta` を検査
4. Artifact `spacecraft-1.20.1-forge` として保存
5. **`main` のときだけ**、タグ `v1.0.0` の Release に jar を添付（既存なら差し替え）

```bash
gh workflow run build.yml
gh run list --workflow build.yml
```

> 一覧ドキュメント（`アイテム一覧/` など 5 つ・`一覧の使い方.md`・`tools/**`・`画像/**`）だけを更新した場合、`paths-ignore` により **CI は起動しません**。実装コードや `src/main/resources/` のモデルを触ったときだけビルドされます。
> ビルドが失敗したときはエラー要約がアノテーションに出ます（sandbox からログの実体を取得できないため）。
> サンドボックスからは Artifact / ログの実体（GitHub の blob ストレージ）をダウンロードできませんが、ビルドと Release への添付は GitHub 側で完結します。
> 使用するアクションは **Node.js 24 対応のメジャー**（`checkout@v7` / `setup-java@v6` / `setup-gradle@v5` / `upload-artifact@v7`）に統一しています。

## 一覧ドキュメント

アイテム / ブロック / UI / 装備 / エンティティを追加したときは、ルート直下の 5 つの一覧に画像付き md を追加します。全手順は [`一覧の使い方.md`](一覧の使い方.md)。

> **立体を持つ要素はすべて 3D**
>
> アイテム・ブロック・装備・エンティティは **3D モデル（`elements`）＋ 3D 画像** が必須です。
> 画像はモデル JSON と実テクスチャの `faces.uv` から等角投影で生成します。
> **例外は UI だけ**（GUI は画面そのものを写すため 2D スクリーンショットのまま）。
> `catalog.py check --strict` が `_3d.svg` と `elements` の欠落を検知します。

| ツール | 内容 |
| --- | --- |
| [`tools/catalog.py`](tools/catalog.py) | `list` / `check` / `new` / `render`（一覧管理・3D 画像の生成入口） |
| [`tools/model3d.py`](tools/model3d.py) | モデル JSON → 3D SVG の共通レンダラ（カメラ・背面カリング・`uv` による配色） |
| [`tools/itemart.py`](tools/itemart.py) | `画像/` の見本を source に、3D モデル・16×16 実テクスチャ・3 枚の 3D 画像を一元生成 |

どちらも **Python 標準ライブラリのみ**で、ビルドには組み込まれていません。

```bash
python3 tools/catalog.py check --strict
python3 tools/catalog.py new アイテム一覧 <id>
python3 tools/itemart.py wrench
python3 tools/catalog.py render アイテム一覧 wrench
```

> **Python は一覧ドキュメントの補助に使っています**。ビルド本体は Java / Gradle、jar の検査は `jar`・`unzip`・`grep` で、Python はビルドに必須ではありません。`Python121212` は GitHub アカウント名由来のパッケージ名・著者名です。
> このリポジトリでの応答・説明は **日本語** に統一しています（`AGENTS.md` 参照）。

## 普通の開発マシンでビルドする

`build.gradle` / `settings.gradle` は ForgeGradle 6 系です。必要なもの: **JDK 17** と **Gradle 8.1.1**。

```bash
gradle wrapper --gradle-version 8.1.1   # gradlew / gradle-wrapper.jar を生成（任意）
gradle build                            # -> build/libs/spacecraft-1.0.0.jar
gradle runClient                        # 開発用クライアント（3D 表示の確認）
gradle runServer                        # 開発用サーバー
```

`gradle.properties` が mod ID・バージョン・Forge バージョンなどの唯一の設定元です。

## 導入して確認する

1. Minecraft 1.20.1 に **Forge 47.x** をインストール
2. Release から取得した `spacecraft-1.0.0.jar` を `.minecraft/mods/`（サーバーなら `mods/`）へコピー
3. 起動し、クリエイティブタブ「**宇宙クラフト**」に **立体のレンチ** が表示されれば成功
   （インベントリ内は斜めから見た 3D、手に持つと柄・開口・グリップの厚みが見えます）
4. 階段やかまどなど `facing` を持つブロックに右クリック → **90 度回転**します（向きを持たないブロックには何も起きません）

サバイバルでの入手手段はまだ無いため、必要なら `/give @s spacecraft:wrench` を使ってください。

## ファイル構成

```
gradle.properties                 設定値（ここだけ編集すればよい）
settings.gradle / build.gradle    ForgeGradle 6 ビルド定義
.github/workflows/build.yml      ビルド + Release への添付
src/main/java/.../SpaceCraft.java        エントリポイント・登録
src/main/java/.../item/WrenchItem.java   レンチの挙動
src/main/resources/assets/spacecraft/
    models/item/wrench.json      3D モデル（elements）
    textures/item/wrench.png     16x16 実テクスチャ（画像/ の見本由来）
    lang/{en_us,ja_jp}.json     名前
src/main/resources/META-INF/mods.toml
src/main/resources/pack.mcmeta
tools/catalog.py                 一覧管理（Python）
tools/model3d.py                 3D レンダラ（Python・catalog / itemart 共用）
tools/itemart.py                 3D モデル・テクスチャ・画像生成（Python）
画像/                            ユーザーが置くテクスチャ見本（source）
    IMG_809df39f-...png          現在のレンチの見本
    ここに追加 / 自分が追加      プレースホルダ（残す）
一覧の使い方.md                  5 一覧の運用ルール（3D 必須）
アイテム一覧/
    wrench.md                    使い方をすべて記載
    models/wrench.json           3D モデルの写し
    images/wrench_3d.svg         3D 全体図
    images/wrench_inventory.svg  インベントリ内（3D）
    images/wrench_held.svg       手持ち（3D）
block一覧/ Ui一覧/ 装備一覧/
エンティティ一覧（スポーンエッグに限る）/
                                 要素ごとの md・3D 画像・モデル JSON
AGENTS.md                        エージェントへの指示（日本語応答など）
LICENSE                          MIT
```

## 次のステップ

レンチのレシピ追加、回転対象となる独自ブロック、装備・UI・スポーンエッグ付きエンティティの実装を想定しています。
**追加する要素もすべて 3D** です。`tools/itemart.py` の `MODEL_DEFS` に `elements` を足すか、`catalog.py render` でモデル JSON から画像を組み立て、`catalog.py new` で一覧の md を作ってください。
