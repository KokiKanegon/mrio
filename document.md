はい、これまでの内容を Markdown で一枚にまとめた仕様書 として整理しました。
これを読めば Claude Code（Python 環境）で 3 地域 ×3 部門 Gravity-RAS 実装をゼロから構築可能か確認できます。

⸻

Gravity-RAS 実装仕様書（3 地域 ×3 部門・Claude Code 向け）

0. 目的
   • 小地域（3 地域 ×3 部門）の産業連関表を Gravity-RAS 手法で推計する。
   • 流れ
   1. 出荷合計・受取合計・距離行列を入力
   2. 重力モデルで地域間フローの初期値を作成
   3. **RAS 法（IPFP）**で行和・列和制約に整合
   4. 結果を部門別 3×3 行列および 9×9 地域 × 部門ブロックとして出力

⸻

1. データ仕様

1.1 地域・部門
• 地域: {A, B, C}
• 部門: {P1=一次, P2=二次, P3=三次}

1.2 入力データ
• 出荷合計 (T_row): shape=(3,3) 部門 × 地域
• 受取合計 (T_col): shape=(3,3) 部門 × 地域
• 距離行列 (L): shape=(3,3)、対称。対角は 1.0 など正値。

1.3 ダミーデータ例

data/T_row.csv

sector,A,B,C
P1,120,80,100
P2,200,160,140
P3,180,150,170

data/T_col.csv

sector,A,B,C
P1,110,90,100
P2,210,140,150
P3,170,160,170

data/L.csv

, A, B, C
A,1.0,30,60
B,30,1.0,40
C,60,40,1.0

data/config.json

{
"alpha": 1.0,
"beta": 1.0,
"gamma": 2.0,
"max_iter": 1000,
"tol": 1e-9,
"eps": 1e-12,
"min_distance": 1.0,
"intra_region_mode": null
}

⸻

2. アルゴリズム

2.1 重力モデル（初期値）

G_i[R,S] = \frac{(T_i^{R\cdot})^\alpha (T_i^{\cdot S})^\beta}{(L^{RS})^\gamma}
• 比率化:
t_i^{RS} = \frac{G_i[R,S]}{\sum_S G_i[R,S]}
• 初期値:
T^{(0)}\_i[R,S] = t_i^{RS} \cdot T_i^{R\cdot}
• 既定: \alpha=\beta=1, \gamma=2

2.2 RAS 法（双方向スケーリング）

反復で行和・列和を一致させる：

X = T0.copy()
for k in range(max_iter):
r = row_targets / X.sum(axis=1)
X = (r[:,None] _ X)
c = col_targets / X.sum(axis=0)
X = (X _ c[None,:])
if 誤差 < tol: break

2.3 出力
• 部門別 3×3 フロー行列 (P1, P2, P3)
• 地域 × 部門 9×9 ブロック行列 (A-P1, A-P2, …, C-P3)

⸻

3. ソフトウェア構成

gravity_ras/
**init**.py
config.py
dataio.py
gravity.py
ras.py
assemble.py
validate.py
scripts/
run_demo.py
data/
T_row.csv, T_col.csv, L.csv, config.json
outputs/
flows_by_sector/P1.csv, P2.csv, P3.csv
T_block.csv
metrics.json

依存: numpy, pandas, （任意で typer CLI）

⸻

4. 関数構成

config.py
• GravityRASConfig: 設定を保持（alpha, beta, gamma, tol, etc.）
• load_config(path) -> GravityRASConfig

dataio.py
• load_matrices(row_path, col_path, L_path) -> (T_row, T_col, L, regions, sectors)
• save_matrix(path, matrix, index_labels, col_labels)
• save_metrics(path, metrics)
• check_shapes(T_row, T_col, L)
• balance_check(T_row, T_col) -> dict

gravity.py
• sanitize_distance(L, cfg) -> np.ndarray
• apply_intra_region_rule(...) -> dict
• gravity_init(Trow, Tcol, L, cfg) -> np.ndarray
• gravity_with_intra(...) -> (T0_total, T0_residual)

ras.py
• ras_balance(T0, row_targets, col_targets, cfg) -> (X, info)

assemble.py
• stack_by_sector(T_hats, regions, sectors) -> (T_block, labels)

validate.py
• calc_discrepancy(X, row_targets, col_targets) -> dict
• sensitivity_gamma(T_row, T_col, L, gammas, cfg) -> list[dict]

scripts/run_demo.py
• main(): 1. 設定読込 2. 行列ロード → チェック 3. 部門ループ: gravity → RAS 4. 保存 5. 9×9 ブロック作成 → 保存 6. メトリクス保存

⸻

5. 出力例（P1）

,A,B,C
A,55.2,40.1,24.7
B,29.8,31.6,18.6
C,25.0,18.3,56.7

    •	行和: (A=120,B=80,C=100) 一致
    •	列和: (A=110,B=90,C=100) 一致

⸻

6. テスト・検証
   • 行和整合: X.sum(axis=1) == T_row
   • 列和整合: X.sum(axis=0) == T_col
   • γ 感度: γ 上昇で遠距離フローが縮小
   • 域内固定: 対角要素を先に確保できる

⸻

7. 不足点（注意すべき点）
   • 域内取引の扱い: 現仕様では L[r,r]=1.0 として処理。必要なら「固定比率」など拡張が必要。
   • 域外（ROW）処理: 現仕様は 3 地域内のみ。外部地域を追加する場合は拡張要。
   • I-O フル統合: 最終需要・付加価値・投入係数は未実装。今回は地域間フローブロック推計まで。
   • 推定パラメータ α,β,γ: 固定（1,1,2）。実データから推定する仕組みは別途要。

⸻

✅ 結論
この Markdown 仕様書を参照すれば、Claude Code 上で 3 地域 ×3 部門の Gravity-RAS 実装は構築可能です。
不足は「域内処理の高度化」「域外追加」「推定パラメータ導入」「フル I-O 表拡張」で、必要なら後から追加すれば OK です。

⸻

ご確認ですが、この仕様は「まず 3 地域 ×3 部門で動かす」目的に十分でしょうか？
それとも「域外（ROW）も含めた 4 地域構造」まで先に組み込みたいですか？
