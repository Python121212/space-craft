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
| 登録先 | `DeferredRegister<Block>` + `DeferredRegister<Item>`（BlockItem） |
| クリエイティブタブ | <タブ名／なし> |
| 状態 | 未実装 / 実装済み |
| 最終更新 | YYYY-MM-DD |

## 見た目（3D）

| 種類 | ファイル | 状態 |
| --- | --- | --- |
| **JSON から組み立てた 3D 画像** | `images/<id>_3d.png` | 未配置 |

画像を置いたら下のコメントを外してください。

<!-- ![<日本語名> の 3D モデル](images/<id>_3d.png) -->

### 元データ（必ずリンクする）

- モデル: [`models/<id>.json`](models/<id>.json)
- ブロックステート: [`blockstates/<id>.json`](blockstates/<id>.json)
- 見本: [`_example_model.json`](_example_model.json) / [`_example_blockstate.json`](_example_blockstate.json)

> `models/` と `blockstates/` は**説明用の写し**です。実際に読み込まれる JSON は
> `src/main/resources/assets/spacecraft/models/block/<id>.json` と
> `src/main/resources/assets/spacecraft/blockstates/<id>.json` に置きます。
> 3D 画像はこの JSON の `elements`（`from` / `to`）と各面の `texture` から等角投影などで組み立ててください。
> `python3 tools/catalog.py render block一覧 <id>` で `images/<id>_3d.svg` を自動生成できます（外部ライブラリ不要）。

## モデル・リソース

| 用途 | パス |
| --- | --- |
| ブロックステート | `src/main/resources/assets/spacecraft/blockstates/<id>.json` |
| ブロックモデル | `src/main/resources/assets/spacecraft/models/block/<id>.json` |
| アイテムモデル | `src/main/resources/assets/spacecraft/models/item/<id>.json` |
| テクスチャ | `src/main/resources/assets/spacecraft/textures/block/<id>.png` |
| 戦利品テーブル | `src/main/resources/data/spacecraft/loot_tables/blocks/<id>.json` |

## 使い方（すべて書く）

### 入手方法
- クリエイティブ: <タブ／検索名>
- サバイバル: <生成・クラフト・ドロップ・取引など全部>
- コマンド: `/give @s spacecraft:<id> <個数>`

### 設置
- 置ける面・向き: <条件>
- 向きの決まり方: <設置者の向き／ブロックステートのプロパティ>
- 隣接ブロックとの関係: <接続・支持・崩落>
- 置けない条件: <条件>

### 回収・破壊
- 適正ツール / 採掘レベル: <ツールと数値>
- 破壊時間・硬度・爆破耐性: <値>
- ドロップ: <アイテムと個数、シルクタッチの扱い>
- 回収できない場合: <条件>

### 右クリック・操作
- 右クリック: <GUI を開く／状態が変わる／何もしない など>
- レッドストーン入力: <反応>
- ホッパー / ピストン / 水 / 溶岩との相互作用: <挙動全部>

### 見た目・物理
- 光源レベル: <値>
- 透過・不透明・カリング: <設定>
- 当たり判定 / 衝突: <形状>
- レンダリングレイヤー（`RenderType`）: <solid / cutout / translucent>
- パーティクル・音・アニメーション: <内容>

### レシピ
| 種類 | 材料 | 結果 |
| --- | --- | --- |
| <クラフト／製錬／他> | <材料> | `<id>` × <個数> |

レシピ JSON: `src/main/resources/data/spacecraft/recipe/<id>.json`

### コマンド
```mcfunction
/setblock ~ ~ ~ spacecraft:<id>
/give @s spacecraft:<id>
```

### 設定・コンフィグ
- 有効/無効・生成頻度など: <キー名と既定値>

### 他要素との関係
- 対応アイテム（BlockItem）/ 装備 / エンティティ / UI: <一覧へのリンク>
- ブロックタグ: `data/spacecraft/tags/blocks/<...>.json`

### 制限・注意
- <ディメンション、座標、権限、互換性などの制限を全部>

### 既知の問題
- <なし／内容と回避策>

### トラブルシュート
| 症状 | 原因 | 対処 |
| --- | --- | --- |
| <症状> | <原因> | <対処> |

## 関連ファイル

- 実装: `src/main/java/io/github/python121212/spacecraft/...`
- 一覧: [`README.md`](README.md)

## 追加時チェックリスト

- [ ] `<...>` をすべて埋めた
- [ ] `models/<id>.json` と `blockstates/<id>.json` を作った
- [ ] JSON から `images/<id>_3d.png` を組み立てた
- [ ] md から JSON へリンクし、画像コメントを外した
- [ ] 「使い方」をすべて書いた
- [ ] [`README.md`](README.md) の表に 1 行追加した
- [ ] ビルドしていない（不要）
