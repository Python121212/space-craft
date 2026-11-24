# <日本語名>（`spacecraft:<id>`）

> `_template.md` をコピーしたファイルです。`<...>` をすべて埋め、画像コメントを外してください。
> **スポーンエッグを持たないエンティティはこの一覧に登録しません。**
> 共通手順は [`一覧の使い方.md`](../一覧の使い方.md) を参照。

## 基本情報

| 項目 | 値 |
| --- | --- |
| 登録 id | `spacecraft:<id>` |
| スポーンエッグ id | `spacecraft:<id>_spawn_egg` |
| 日本語名 | <日本語名> |
| 英語名 | <English name> |
| 追加バージョン | <x.y.z> |
| 実装クラス | `<Entity クラス名>.java` |
| 登録先 | `DeferredRegister<EntityType<?>>` + `DeferredRegister<Item>`（スポーンエッグ） |
| 分類 | 友好 / 敵対 / 中立 / その他 |
| 状態 | 未実装 / 実装済み |
| 最終更新 | YYYY-MM-DD |

## 画像

| 種類 | ファイル | 状態 |
| --- | --- | --- |
| **スポーンエッグの画像** | `images/<id>_egg.png` | 未配置 |
| **その見た目の 3D 画像** | `images/<id>_3d.png` | 未配置 |
| **スポーンエッグを持った状態** | `images/<id>_egg_held.png` | 未配置 |

画像を `images/` に置いたら下のコメントを外してください。

<!-- ![<日本語名> のスポーンエッグ](images/<id>_egg.png) -->
<!-- ![<日本語名> の見た目（3D）](images/<id>_3d.png) -->
<!-- ![スポーンエッグを持った状態](images/<id>_egg_held.png) -->

## モデル・リソース

| 用途 | パス |
| --- | --- |
| エンティティモデル | `src/main/java/.../client/model/<id>Model.java` |
| レンダラー | `src/main/java/.../client/renderer/entity/<id>Renderer.java` |
| テクスチャ | `src/main/resources/assets/spacecraft/textures/entity/<id>.png` |
| 説明用モデル JSON | `models/<id>.json`（任意） |
| スポーンエッグのアイテムモデル | `src/main/resources/assets/spacecraft/models/item/<id>_spawn_egg.json` |

## 使い方（すべて書く）

### スポーンエッグの入手方法
- クリエイティブ: <タブ／検索名>
- サバイバル: <クラフト・ドロップ・取引・コマンドなど全部>
- コマンド: `/give @s spacecraft:<id>_spawn_egg 1`

### スポーンエッグの使い方
- 右クリックした対象: <ブロック／水面／エンティティ>
- 召喚されるもの: <エンティティ／幼体の確率／騎乗状態など>
- 失敗する条件: <条件>
- 使ったあと: <エッグは消費されるか、クリエイティブでの扱い>
- **スポーンエッグを持った状態**: 一人称の見た目（`..._egg_held.png` と対応）

### 見た目（3D）
- モデル・テクスチャ・当たり判定のサイズ: <内容>
- バリエーション（色・幼体・状態）: <内容>
- アニメーション・パーティクル: <内容>

### 挙動・AI
- 移動・攻撃・逃避・ターゲット: <内容全部>
- テイム / 繁殖 / リード / 乗れるか: <可否と手順>
- 音・鳴き声: <内容>

### ステータス・ドロップ
| 項目 | 値 |
| --- | --- |
| 最大体力 | <値> |
| 攻撃力 | <値> |
| ドロップアイテム | <一覧と個数、レア枠> |
| 経験値 | <値> |

### スポーン条件
- 自然スポーン: <バイオーム・時間・高さ・ Light level・グループサイズ>
- 構造物・スポナー: <内容>
- `/summon` での指定: <書式>

### レシピ
| 種類 | 材料 | 結果 |
| --- | --- | --- |
| <クラフト／他> | <材料> | `<id>_spawn_egg` × 1 |

レシピ JSON: `src/main/resources/data/spacecraft/recipe/<id>_spawn_egg.json`

### コマンド
```mcfunction
/summon spacecraft:<id> ~ ~ ~ {CustomName:'"<日本語名>"'}
/give @s spacecraft:<id>_spawn_egg
```

### 設定・コンフィグ
- スポーン率・有効無効・ステータス調整: <キー名と既定値>

### 他要素との関係
- 対応アイテム / ブロック / 装備 / UI: <一覧へのリンク>
- エンティティタグ: `data/spacecraft/tags/entity_types/<...>.json`

### 制限・注意
- <ディメンション、難易度、平和モード、他 mod との競合など全部>

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
- [ ] `..._egg.png` / `..._3d.png` / `..._egg_held.png` を置いた
- [ ] md の画像コメントを外した
- [ ] スポーンエッグの入手・使い方・`/summon` を書いた
- [ ] 「使い方」をすべて書いた
- [ ] [`README.md`](README.md) の表に 1 行追加した
- [ ] ビルドしていない（不要）
