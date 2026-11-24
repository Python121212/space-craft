# space-craft

**Minecraft 1.20.1 / Forge 用の、中身が空の mod** です。「ビルドが通って Forge に mod として認識される jar」を用意する段階です。

ブロック・アイテム・イベント・設定ファイルなどは **一切登録していません**。`@Mod("spacecraft")` が付いた空のエントリポイントクラスが 1 つあるだけです。

## 配布物

**配布物は GitHub Release に一本化しています。リポジトリ内に jar は置いていません。**

| 場所 | 内容 |
| --- | --- |
| [Release `v1.0.0`](https://github.com/Python121212/space-craft/releases/tag/v1.0.0) | `spacecraft-1.0.0.jar`（GitHub Actions が JDK 17 + Gradle 8.1.1 でビルドしたもの） |

```bash
gh release view v1.0.0                 # リリースの確認
gh release download v1.0.0 -p '*.jar'  # jar を取得
```

直接ダウンロード: https://github.com/Python121212/space-craft/releases/download/v1.0.0/spacecraft-1.0.0.jar

jar の中身は 4 ファイルだけです:

```
META-INF/MANIFEST.MF
META-INF/mods.toml          modId / バージョン / 依存関係
pack.mcmeta                 pack_format 15 (1.20.1)
io/github/python121212/spacecraft/SpaceCraft.class   @Mod エントリポイント (Java 17)
```

`mods.toml` の主な設定:

- `modLoader = "javafml"`、`loaderVersion = "[47,)"`
- 依存: `forge [47,)`、`minecraft [1.20.1,1.20.2)`
- `modId = "spacecraft"`、`version = "1.0.0"`、`license = "MIT"`

## GitHub Actions でのビルドとリリース

`.github/workflows/build.yml` が `main` と `arena/**` への push（および手動実行）で動きます。

1. JDK 17 (temurin) と Gradle 8.1.1 を用意
2. `gradle build` で `build/libs/spacecraft-1.0.0.jar` を生成
3. `jar tf` / `mods.toml` / `pack.mcmeta` を検査
4. Artifact `spacecraft-1.20.1-forge` として保存
5. **`main` のときだけ**、タグ `v1.0.0` の Release に jar を添付（既存リリースならアセットを差し替え）

```bash
gh workflow run build.yml                          # 手動実行
gh run list --workflow build.yml                    # 実行一覧
gh run download <run-id> -n spacecraft-1.20.1-forge
```

> ネットワーク制限のあるサンドボックスからは Artifact / ログの実体（GitHub の blob ストレージ）をダウンロードできませんが、ビルドと Release への添付は GitHub 側で完結します。

> 使用するアクションは **Node.js 24 対応のメジャー**（`checkout@v7` / `setup-java@v6` / `setup-gradle@v5` / `upload-artifact@v7`）に統一しています。`gradle/actions` は v6 でキャッシュのライセンスが変わるため、MIT のままの v5 を採用しています。

> **Python は一覧ドキュメントの補助に使っています**（[`tools/catalog.py`](tools/catalog.py)、標準ライブラリのみ）。ビルド本体は Java / Gradle、jar の検査は `jar`・`unzip`・`grep` で、Python はビルドに必須ではありません。`Python121212` は GitHub アカウント名由来のパッケージ名・著者名です。

> このリポジトリでの応答・説明は **日本語** に統一しています（`AGENTS.md` 参照）。

## 普通の開発マシンでビルドする

`build.gradle` / `settings.gradle` は ForgeGradle 6 系（MDK 準拠）です。

必要なもの: **JDK 17** と **Gradle 8.1.1**（と Forge の Maven へのネットワーク）

```bash
gradle wrapper --gradle-version 8.1.1   # gradlew / gradle-wrapper.jar を生成（任意）
gradle build                            # -> build/libs/spacecraft-1.0.0.jar
gradle runClient                        # 開発用クライアント起動
gradle runServer                        # 開発用サーバー起動
```

> `gradlew` / `gradle-wrapper.jar` はバイナリ配布物のため、このリポジトリには含めていません。上の `gradle wrapper` を一度実行すれば追加されます。

`gradle.properties` が mod ID・バージョン・Forge バージョンなどの唯一の設定元です。`mods.toml` と `pack.mcmeta` のプレースホルダは `processResources` でここから展開されます。

## 導入して確認する

1. Minecraft 1.20.1 に **Forge 47.x** をインストールする
2. Release から取得した `spacecraft-1.0.0.jar` を `.minecraft/mods/`（サーバーなら `mods/`）へコピーする
3. 起動し、Mods 一覧に **Space Craft 1.0.0** が表示されれば成功

何も登録していないので、ゲーム内の挙動は変わりません。`latest.log` に `spacecraft` の読み込みが出ます。

## ファイル構成

```
gradle.properties                 設定値（ここだけ編集すればよい）
settings.gradle / build.gradle    ForgeGradle 6 ビルド定義
.github/workflows/build.yml      ビルド + Release への添付
tools/catalog.py                 一覧ドキュメントの管理（Python・ビルド不要）
一覧の使い方.md                  5 つの一覧の運用ルール
アイテム一覧/ block一覧/ Ui一覧/
装備一覧/ エンティティ一覧（スポーンエッグに限る）/
                                 要素ごとの md・画像・モデル JSON
src/main/java/.../SpaceCraft.java 空の @Mod クラス
src/main/resources/META-INF/mods.toml
src/main/resources/pack.mcmeta
LICENSE                           MIT
AGENTS.md                         エージェントへの指示（日本語応答など）
```

## 次のステップ

ここから `DeferredRegister` でブロック / アイテムを登録したり、`FMLCommonSetupEvent` やレシピ・datagen を足していく想定です。`gradle runClient` が使える環境なら、まずは `SpaceCraft` のコンストラクタに `IEventBus` を渡すところから始めます。
