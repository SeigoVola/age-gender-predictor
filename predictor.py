import torch
import torch.nn.functional as F # Softmaxをインポート
import os
from transformers import BertJapaneseTokenizer

# SupervisedLearning.pyからモデル定義と設定をインポート
from SupervisedLearning import BertForClassification, PRE_TRAINED_MODEL_NAME, DEVICE, NUM_LABELS

# モデルファイルのパス
MODEL_PATH = 'bert_classification_model.bin'

# ラベルとカテゴリのマッピング
CATEGORIES = [
    "10代 male", "10代 female",
    "20代 male", "20代 female",
    "30代 male", "30代 female",
    "40代 male", "40代 female",
    "50代 male", "50代 female",
    "60代 male", "60代 female"
]

# --- グローバル変数としてモデルとトークナイザを一度だけロード ---
TOKENIZER = None
MODEL = None

def load_model():
    """アプリケーション起動時にモデルを一度だけ読み込む"""
    global TOKENIZER, MODEL
    
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"エラー: 学習済みモデル '{MODEL_PATH}' が見つかりません。先にモデルを学習してください。")

    print("--- モデルの読み込みを開始します ---")
    TOKENIZER = BertJapaneseTokenizer.from_pretrained(PRE_TRAINED_MODEL_NAME)
    MODEL = BertForClassification(PRE_TRAINED_MODEL_NAME, NUM_LABELS)
    
    try:
        # PyTorch 2.xでのセキュリティ警告を避けるため weights_only=True を推奨
        if torch.__version__.startswith('1.'):
             MODEL.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
        else:
             MODEL.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE, weights_only=True))

    except Exception as e:
        print(f"モデルの読み込み中にエラーが発生しました: {e}")
        raise
        
    MODEL.to(DEVICE)
    MODEL.eval()
    print("--- モデルの読み込みが完了しました ---")


def predict_text(text: str):
    """
    入力されたテキストから「年代」と「性別」の予測確率上位3つを返す関数
    """
    if MODEL is None or TOKENIZER is None:
        load_model()

    # 2. テキストの前処理
    encoding = TOKENIZER.encode_plus(
        text,
        add_special_tokens=True,
        max_length=128,
        return_token_type_ids=False,
        padding='max_length',
        truncation=True,
        return_attention_mask=True,
        return_tensors='pt',
    )
    input_ids = encoding['input_ids'].to(DEVICE)
    attention_mask = encoding['attention_mask'].to(DEVICE)

    # 3. 予測の実行
    with torch.no_grad():
        _, logits = MODEL(input_ids=input_ids, attention_mask=attention_mask)

    # 4. 上位3つの予測結果を取得
    # Softmaxを適用して確率に変換
    probs = F.softmax(logits, dim=1)
    
    # 上位3つの確率とインデックスを取得
    top_probs, top_indices = torch.topk(probs, 3)

    # 5. 結果を整形
    results = []
    for prob, idx in zip(top_probs[0], top_indices[0]):
        predicted_category = CATEGORIES[idx.item()]
        
        # "30代 female" -> ["30代", "female"]
        parts = predicted_category.split()
        age = parts[0]
        gender_en = parts[1]
        
        # 性別を日本語に変換
        gender_jp = "男性" if gender_en == "male" else "女性"

        results.append({
            "age": age,
            "gender": gender_jp,
            "probability": int(prob.item() * 100)  # パーセンテージを整数に変換
        })
        
    return results
