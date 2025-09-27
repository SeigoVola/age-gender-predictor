import pandas as pd
from sudachipy import tokenizer, dictionary
import neologdn
import os # osモジュールをインポート

# --- スクリプトのディレクトリを基準にパスを設定 ---
# このスクリプト自身の絶対パスを取得
script_dir = os.path.dirname(os.path.abspath(__file__))
# 作業ディレクトリをこのスクリプトがあるディレクトリに変更
os.chdir(script_dir)

def load_preprocessed_data():
    """
    DataSet.xlsxを読み込み、前処理（欠損値除去、ラベルエンコーディング、形態素解析）を行い、
    処理済みのDataFrameと元のデータ数を返します。
    """
    # --- Step 1: データ読み込み ---
    df = pd.read_excel("DataSet.xlsx")
    initial_count = len(df)

    # --- Step 2: 欠損除去 ---
    df = df.dropna(subset=["コメント", "性別", "年代"]).reset_index(drop=True)

    # --- Step 2.5: 表記揺れ正規化 ---
    df["コメント"] = df["コメント"].astype(str).apply(neologdn.normalize)

    # --- Step 3: 年代と性別を統合したラベル作成（スペースあり）---
    df["年代性別"] = df["年代"] + " " + df["性別"]

    # ラベルのマッピング
    categories = [
        "10代 male", "10代 female",
        "20代 male", "20代 female",
        "30代 male", "30代 female",
        "40代 male", "40代 female",
        "50代 male", "50代 female",
        "60代 male", "60代 female"
    ]
    label_map = {cat: idx for idx, cat in enumerate(categories)}

    df["年代性別_label"] = df["年代性別"].map(label_map)

    # --- Step 4: Sudachipyによる形態素解析（表層 + 品詞）---
    tokenizer_obj = dictionary.Dictionary().create()
    mode = tokenizer.Tokenizer.SplitMode.C

    def sudachi_tokenize_with_pos(text):
        tokens = tokenizer_obj.tokenize(text, mode)
        return [
            f"{m.surface()}/{m.part_of_speech()[0]}"
            for m in tokens if m.surface().strip()
        ]

    df["tokens"] = df["コメント"].apply(sudachi_tokenize_with_pos)
    df["text"] = df["tokens"].apply(lambda x: " ".join(x))

    return df, initial_count

if __name__ == '__main__':
    df, initial_count = load_preprocessed_data()

    # --- 表示 ---
    print(f"✅ Excel内の全データ数: {initial_count} 件")
    print(f"\n✅ 前処理後のデータ数: {len(df)} 件")
    print("==== Sudachipyによる処理結果の一部 ====")

    for i in range(min(10, len(df))):  # 先頭10件まで表示
        print(f"\n【{i+1}件目】")
        print(f"[原文(正規化後)] {df.loc[i, 'コメント']}")
        print(f"[形態素+品詞] {df.loc[i, 'tokens']}")
        print(f"[テキスト形式] {df.loc[i, 'text']}")
        print(f"[年代性別] {df.loc[i, '年代性別']}")
        print(f"[年代性別_label] {df.loc[i, '年代性別_label']}")
