# エージェントへの指示（このリポジトリ専用）

## 言語（最優先）

- **必ず日本語で応答・説明してください。** チャットの回答、README やドキュメントの説明文、PR の本文、レビューコメント、コミットメッセージの本文はすべて日本語です。
- このルールはセッションをまたいでも有効です。コンテキストがリセットされて英語に戻らないよう、作業を始める前にこのファイルを読んで従ってください。
- 例外: コードの識別子、Gradle / TOML / YAML のキー、ライブラリ名、コマンド、ファイルパスなどの技術用語は英語のままで構いません。

## プロジェクト概要

- Minecraft **1.20.1 / Forge 47.x** の mod。Java 17、ForgeGradle 6、Gradle 8.1.1。
- 設定値の唯一の来源は `gradle.properties`（mod ID・バージョン・Forge バージョン・pack_format など）。
- 現状は「何も登録しない空の mod」。`@Mod("spacecraft")` が付いたエントリポイントクラスが 1 つだけです。
- **正式なビルドは GitHub Actions**（`.github/workflows/build.yml`）で JDK 17 + Gradle 8.1.1 を使って行います。
- Actions のアクションは **Node.js 24 対応メジャーを維持**してください（`checkout@v7` / `setup-java@v6` / `setup-gradle@v5` / `upload-artifact@v7`）。Node 20 系へ戻すと非推奨警告が再発します。`gradle/actions` は v6 でキャッシュのライセンスが変わるため、MIT の v5 で固定しています。
- **配布用の jar は GitHub Release のみ**（タグ `v1.0.0`）。`main` への push で Actions がビルド結果を自動で添付／差し替えます。**リポジトリ内には jar を置きません**（`dist/` は削除済み、`.gitignore` にも登録）。
- **Python は使用しません。** ビルドは Java / Gradle、検査は `jar`・`unzip`・`grep` のみです。Python スクリプトを追加・復活させないでください。
- なお `Python121212` は GitHub アカウント名であり、パッケージ名や著者名に含まれる文字列です。これは削除対象ではありません。

## ブランチ運用

- 作業ブランチは Arena が割り当てた現在のブランチ固定です。ブランチ名の変更・別ブランチへの直接 push は行いません。
- `main` への取り込みは、現在のブランチから PR を作成してマージします。
