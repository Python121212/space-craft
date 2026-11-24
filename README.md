# space-craft

**Minecraft 1.20.1 / Forge 用の、中身が空の mod** です。まずは「ビルドが通って Forge に mod として認識される jar」を作るところまでを目的にしています。

ブロック・アイテム・イベント・設定ファイルなどは **一切登録していません**。`@Mod("spacecraft")` が付いた空のエントリポイントクラスが 1 つあるだけです。

## 成果物

| ファイル | 内容 |
| --- | --- |
| `dist/spacecraft-1.0.0.jar` | 生成済みの mod jar（Forge 1.20.1 の `mods/` にそのまま置けます） |

中身は 4 ファイルだけです:

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

## GitHub Actions での正式ビルド（JDK 17 + Gradle 8.1.1）

`.github/workflows/build.yml` が `main` と `arena/**` への push（および手動実行）で動きます。GitHub のランナー上で実際に `gradle build` を実行し、`build/libs/spacecraft-1.0.0.jar` を Artifact として保存します。ローカルに JDK / Gradle が無い環境でも、こちらが正式なビルドです。

```bash
gh workflow run build.yml          # 手動実行
gh run list --workflow build.yml    # 実行一覧
gh run download <run-id> -n spacecraft-1.20.1-forge
```

> このリポジトリでの応答・説明は **日本語** に統一しています（`AGENTS.md` 参照）。

## この環境で jar を生成する

このサンドボックスには JDK / Gradle が入っておらず、`maven.minecraftforge.net` にも接続できません。そのため `tools/make_jar.py` が **`gradle.properties` と `src/main/resources` の同じソースから直接 jar を組み立てます**（`@Mod` 付きの Java 17 class ファイルもバイト列から生成します）。

```bash
python3 tools/make_jar.py           # dist/spacecraft-1.0.0.jar を生成
python3 tools/make_jar.py --check   # 既存 jar を検証するだけ
python3 tools/make_jar.py --out /tmp/test.jar
```

生成後に以下を自動検証します: ZIP 整合性、エントリ一覧、`mods.toml` の必須項目と依存バージョン、`pack.mcmeta` の `pack_format`、MANIFEST、class ファイルの構造（class version 61 / public no-arg constructor / `@Mod` の RuntimeVisibleAnnotations）。

`SOURCE_DATE_EPOCH` を設定すると MANIFEST と ZIP エントリのタイムスタンプが固定され、バイト単位で再現可能な jar になります（Git に不要な差分が出ません）。

```bash
SOURCE_DATE_EPOCH=1795478400 python3 tools/make_jar.py
```

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

`gradle.properties` が mod ID・バージョン・Forge バージョンなどの唯一の設定元です。`mods.toml` と `pack.mcmeta` の `${...}` は `processResources` でここから展開されます（`make_jar.py` も同じく展開します）。

## 導入して確認する

1. Minecraft 1.20.1 に **Forge 47.x** をインストールする
2. `dist/spacecraft-1.0.0.jar` を `.minecraft/mods/`（サーバーなら `mods/`）へコピーする
3. 起動し、Mods 一覧に **Space Craft 1.0.0** が表示されれば成功

何も登録していないので、ゲーム内の挙動は変わりません。`latest.log` に `spacecraft` の読み込みが出ます。

## ファイル構成

```
gradle.properties                 設定値（ここだけ編集すればよい）
settings.gradle / build.gradle    ForgeGradle 6 ビルド定義
src/main/java/.../SpaceCraft.java 空の @Mod クラス
src/main/resources/META-INF/mods.toml
src/main/resources/pack.mcmeta
tools/make_jar.py                 JDK 不要の jar 生成 + 検証
dist/spacecraft-1.0.0.jar        生成済み jar（Git に含めています）
LICENSE                           MIT
```

## 次のステップ

ここから `DeferredRegister` でブロック / アイテムを登録したり、`FMLCommonSetupEvent` やレシピ・datagen を足していく想定です。`gradle runClient` が使える環境なら、まずは `SpaceCraft` のコンストラクタに `IEventBus` を渡すところから始めます。
