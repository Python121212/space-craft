# <日本語名>（`spacecraft:<id>`）

> `_template.md` をコピーしたファイルです。`<...>` をすべて埋め、画像コメントを外してください。
> 共通手順は [`一覧の使い方.md`](../一覧の使い方.md) を参照。

## 基本情報

| 項目 | 値 |
| --- | --- |
| 登録 id | `spacecraft:<id>` |
| 日本語名 | <日本語名> |
| 英語名 | <English name> |
| 種別 | 防具 / 武器 / ツール / アクセサリ / その他 |
| 追加バージョン | <x.y.z> |
| 実装クラス | `<クラス名>.java` |
| 装備スロット | 頭 / 胸 / 脚 / 足 / メインハンド / オフハンド / Curios |
| クリエイティブタブ | <タブ名／なし> |
| 状態 | 未実装 / 実装済み |
| 最終更新 | YYYY-MM-DD |

## 画像

| 種類 | ファイル | 状態 |
| --- | --- | --- |
| **手に持った状態**（JSON から組み立て） | `images/<id>_held.png` | 未配置 |
| **インベントリ内の状態** | `images/<id>_inventory.png` | 未配置 |
| **装備した状態** | `images/<id>_equipped.png` | 未配置 |
| 3D モデル（任意） | `images/<id>_3d.png` | 未配置 |

画像を `images/` に置いたら下のコメントを外してください。

<!-- ![手に持った <日本語名>](images/<id>_held.png) -->
<!-- ![インベントリ内の <日本語名>](images/<id>_inventory.png) -->
<!-- ![装備した <日本語名>](images/<id>_equipped.png) -->
<!-- ![<日本語名> の 3D モデル](images/<id>_3d.png) -->

## モデル（JSON から組み立てる）

- [`models/<id>.json`](models/<id>.json) … `display` の `firstperson_righthand` / `thirdperson_righthand` / `gui` が手持ち・三人称・インベントリ内の見た目を決めます
- 見本: [`_example_model.json`](_example_model.json)
- 3D 画像は `python3 tools/catalog.py render 装備 <id>` で `models/<id>.json` から SVG を生成できます（依存なし）

> `models/` は説明用の写しです。実際の JSON は `src/main/resources/assets/spacecraft/models/item/<id>.json` に置きます。

## 使い方（すべて書く）

### 入手方法
- クリエイティブ: <タブ／検索名>
- サバイバル: <クラフト・ドロップ・取引・戦利品テーブルなど全部>
- コマンド: `/give @s spacecraft:<id> 1`

### 装備の方法
- スロット: <頭／胸／脚／足／手／Curios>
- 装備する操作: <インベントリでドラッグ／右クリック／ディスペンサー／コマンド>
- 外す操作: <操作>
- 自動で装備される条件: <条件>

### 効果・性能
| 項目 | 値 |
| --- | --- |
| 防御力 / 防御強度 | <値> |
| 攻撃力 / 攻撃速度 | <値> |
| 耐久値 | <値> |
| 属性修飾 | <属性・量・スロット> |
| 特殊効果 | <内容と発動条件> |
| エンチャント可否 | <可否と対象> |

### 修理・強化
- 修理材料: <材料>
- 金床・砥石・経験値コスト: <内容>
- 修繕・耐久エンチャント: <挙動>

### 手に持った状態 / インベントリ内 / 装備時
- **手持ち**: `display.firstperson_*` の見た目（`..._held.png` と対応）
- **インベントリ内**: アイコン・ツールチップ・耐久ゲージ（`..._inventory.png` と対応）
- **装備時**: プレイヤーモデル上の見た目、腕・防具レイヤー、発光・パーティクル（`..._equipped.png` と対応）

### 使用・右クリック
- 右クリック: <挙動>
- 左クリック / 長押し: <挙動>
- 消費・クールダウン: <値と単位>

### レシピ
| 種類 | 材料 | 結果 |
| --- | --- | --- |
| <クラフト／製錬／他> | <材料> | `<id>` × 1 |

レシピ JSON: `src/main/resources/data/spacecraft/recipe/<id>.json`

### コマンド
```mcfunction
/give @s spacecraft:<id>
/replaceitem entity @s armor.head spacecraft:<id>
```

### 設定・コンフィグ
- 性能の調整キーと既定値: <内容>
- 難易度による差: <内容>

### 他要素との関係
- 対応アイテム / ブロック / UI / エンティティ: <一覧へのリンク>
- 装備時に開く UI、付与されるポーション効果、連動するエンティティ: <内容>

### 制限・注意
- <スロット競合、他 mod との互換、ディメンション制限など全部>

### 既知の問題
- <なし／内容と回避策>

### トラブルシュート
| 症状 | 原因 | 対処 |
| --- | --- | --- |
| <症状> | <原因> | <対処> |

## 関連ファイル

- 実装: `src/main/java/io/github/python121212/spacecraft/...`
- テクスチャ: `src/main/resources/assets/spacecraft/textures/item/<id>.png`
- 防具レイヤー: `src/main/resources/assets/spacecraft/textures/models/armor/<id>_layer_1.png`
- 一覧: [`README.md`](README.md) / [`../アイテム一覧/README.md`](../アイテム一覧/README.md)

## 追加時チェックリスト

- [ ] `<...>` をすべて埋めた
- [ ] `models/<id>.json` を作った
- [ ] `..._held.png` / `..._inventory.png` / `..._equipped.png` を置いた
- [ ] md から JSON へリンクし、画像コメントを外した
- [ ] 「使い方」をすべて書いた
- [ ] [`README.md`](README.md) と `アイテム一覧/README.md` に 1 行追加した
- [ ] ビルドしていない（不要）
