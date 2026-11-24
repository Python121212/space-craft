# <日本語名>（`spacecraft:<id>`）

> `_template.md` をコピーしたファイルです。`<...>` をすべて埋め、画像コメントを外してください。
> 共通手順は [`一覧の使い方.md`](../一覧の使い方.md) を参照。

## 基本情報

| 項目 | 値 |
| --- | --- |
| 登録 id | `spacecraft:<id>` |
| 日本語名 | <日本語名> |
| 英語名 | <English name> |
| 追加バージョン | <x.y.z> |
| 実装クラス | `<クラス名>.java` |
| 登録先 | `DeferredRegister<Item>` |
| クリエイティブタブ | <タブ名／なし> |
| 状態 | 未実装 / 実装済み |
| 最終更新 | YYYY-MM-DD |

## 画像

| 種類 | ファイル | 状態 |
| --- | --- | --- |
| **3D モデル全体図**（`elements` 由来） | `images/<id>_3d.svg` | 未配置 |
| **インベントリ内の状態**（3D） | `images/<id>_inventory.svg` | 未配置 |
| **手に持った状態**（3D） | `images/<id>_held.svg` | 未配置 |

> **アイテムは必ず 3D です。** `item/generated` の 2D スプライトには戻さないでください。
> 3 枚とも `models/<id>.json` の `elements` と実テクスチャの `uv` から `tools/model3d.py` が組み立てます。
> `python3 tools/itemart.py <id>` でゲーム内モデル・テクスチャ・3 枚の画像を一括生成できます。

画像を `images/` に置いたら、下のコメントを外してください（相対パスで参照します）。

<!-- ![<日本語名> の 3D モデル](images/<id>_3d.svg) -->
<!-- ![インベントリ内の <日本語名>](images/<id>_inventory.svg) -->
<!-- ![手に持った <日本語名>](images/<id>_held.svg) -->

## モデル・リソース

| 用途 | パス |
| --- | --- |
| アイテムモデル（`elements` 必須） | `src/main/resources/assets/spacecraft/models/item/<id>.json` |
| テクスチャ（`画像/` の見本を 16×16 に） | `src/main/resources/assets/spacecraft/textures/item/<id>.png` |
| **見本テクスチャ（source）** | [`../画像/`](../画像/README.md) に置いた PNG |
| **説明用の写し（必須）** | [`models/<id>.json`](models/<id>.json) |

## 使い方（すべて書く）

### 入手方法
- クリエイティブ: <タブ／検索名>
- サバイバル: <ドロップ・クラフト・取引・戦利品テーブルなど全部>
- コマンド: `/give @s spacecraft:<id> <個数>`

### 基本的な操作
- 右クリック: <挙動、成功/失敗条件、消費の有無>
- 左クリック: <挙動>
- ブロックに対して使ったとき: <挙動>
- エンティティに対して使ったとき: <挙動>
- 使用時間・クールダウン・消費: <値と単位>

### インベントリ内での扱い
- 最大スタック数: <数>
- 耐久値: <数／なし>
- 修理可能か / 材料: <有無と内容>
- エンチャント可否: <可否と対象>
- NBT / Capability / Data Component: <保持するデータ全部>
- 捨てた・燃やした・爆発したとき: <挙動>

### 手に持った状態の挙動
- 一人称 / 三人称の見た目: <説明。画像 `..._held.svg` と対応>
- 持ち替え・オフハンド: <可否と挙動>

### レシピ
| 種類 | 材料 | 結果 |
| --- | --- | --- |
| <クラフト／製錬／他> | <材料> | `<id>` × <個数> |

レシピ JSON: `src/main/resources/data/spacecraft/recipe/<id>.json`

### コマンド
```mcfunction
/give @s spacecraft:<id>
/clear @s spacecraft:<id>
```

### 設定・コンフィグ
- 有効/無効の切り替え: <キー名と既定値>
- 難易度による差: <内容>

### 他要素との関係
- 対応ブロック / 装備 / エンティティ / UI: <一覧へのリンク>
- タグ: `data/spacecraft/tags/item/<...>.json` / Minecraft 側タグ

### 制限・注意
- <ディメンション、ゲームモード、権限、互換性などの制限を全部>

### 既知の問題
- <なし／内容と回避策>

### トラブルシュート
| 症状 | 原因 | 対処 |
| --- | --- | --- |
| <症状> | <原因> | <対処> |

## 関連ファイル

- 実装: `src/main/java/io/github/python121212/spacecraft/...`
- 一覧: [`README.md`](README.md)
- 装備としても使う場合: [`../装備一覧/README.md`](../装備一覧/README.md)

## 追加時チェックリスト

- [ ] `<...>` をすべて埋めた
- [ ] `models/<id>.json` に 3D の `elements` を作った
- [ ] `images/<id>_3d.svg` / `<id>_inventory.svg` / `<id>_held.svg` を置いた（すべて 3D）
- [ ] md の画像コメントを外した
- [ ] 「使い方」をすべて書いた
- [ ] [`README.md`](README.md) の表に 1 行追加した
- [ ] ビルドしていない（不要）
