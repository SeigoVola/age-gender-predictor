import torch
from torch import nn
from torch.utils.data import Dataset, DataLoader, RandomSampler
from torch.optim import AdamW
from transformers import BertJapaneseTokenizer, BertModel
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import pandas as pd
from tqdm import tqdm
import os # osモジュールをインポート

from DataNLP import load_preprocessed_data

# --- スクリプトのディレクトリを基準にパスを設定 ---
# このスクリプト自身の絶対パスを取得
script_dir = os.path.dirname(os.path.abspath(__file__))
# 作業ディレクトリをこのスクリプトがあるディレクトリに変更
os.chdir(script_dir)


# 設定
PRE_TRAINED_MODEL_NAME = 'cl-tohoku/bert-large-japanese'
MAX_LEN = 128
BATCH_SIZE = 16
EPOCHS = 7  # 小規模データに合わせて短縮
DEVICE = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
NUM_LABELS = 12  # 10代 male ~ 60代 female

# --- データセットクラス ---
class CustomDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_len):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_len = max_len

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, item):
        text = str(self.texts[item])
        label = self.labels[item]

        encoding = self.tokenizer.encode_plus(
            text,
            add_special_tokens=True,
            max_length=self.max_len,
            return_token_type_ids=False,
            padding='max_length',
            truncation=True,
            return_attention_mask=True,
            return_tensors='pt',
        )

        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': torch.tensor(int(label), dtype=torch.long)
        }

# --- モデル定義 ---
class BertForClassification(nn.Module):
    def __init__(self, model_name, num_labels):
        super().__init__()
        self.bert = BertModel.from_pretrained(model_name, use_safetensors=True)
        self.dropout = nn.Dropout(self.bert.config.hidden_dropout_prob)
        self.classifier = nn.Linear(self.bert.config.hidden_size, num_labels)

    def forward(self, input_ids, attention_mask, labels=None):
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        pooled_output = outputs.pooler_output
        pooled_output = self.dropout(pooled_output)

        logits = self.classifier(pooled_output)

        loss = None
        if labels is not None:
            loss_fct = nn.CrossEntropyLoss()
            loss = loss_fct(logits.view(-1, NUM_LABELS), labels.view(-1))

        return loss, logits

# --- 学習関数 ---
def train_epoch(model, data_loader, optimizer, device):
    model.train()
    total_loss = 0
    for batch in tqdm(data_loader, desc="Training"):
        input_ids = batch['input_ids'].to(device)
        attention_mask = batch['attention_mask'].to(device)
        labels = batch['labels'].to(device)

        optimizer.zero_grad()
        loss, _ = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
        
        if isinstance(loss, torch.Tensor):
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
    
    return total_loss / len(data_loader)

# --- 評価関数 ---
def eval_model(model, data_loader, device):
    model.eval()
    preds, true_labels = [], []
    
    with torch.no_grad():
        for batch in tqdm(data_loader, desc="Evaluating"):
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            
            _, logits = model(input_ids=input_ids, attention_mask=attention_mask)
            preds.extend(torch.argmax(logits, dim=1).cpu().numpy())
            true_labels.extend(batch['labels'].cpu().numpy())

    return accuracy_score(true_labels, preds)

# --- データサンプリング関数（年代性別ごとに最大件数制限） ---
def sample_balanced_data(df, max_per_class=5000):
    sampled_dfs = []
    for label in df['年代性別_label'].unique():
        subset = df[df['年代性別_label'] == label]
        if len(subset) > max_per_class:
            subset = subset.sample(max_per_class, random_state=42)
        sampled_dfs.append(subset)
    return pd.concat(sampled_dfs).sample(frac=1, random_state=42).reset_index(drop=True)

# --- メイン処理 ---
def main():
    print("--- 1. データ読み込み ---")
    df, _ = load_preprocessed_data()

    # --- データを年代性別ごとにサンプリングして軽量化 ---
    df = sample_balanced_data(df, max_per_class=5000)

    # ラベルの分布を確認
    print("年代性別ラベルの分布:\n", df['年代性別_label'].value_counts())
    
    # 訓練用と検証用に分割
    train_df, val_df = train_test_split(df, test_size=0.2, random_state=42)

    print(f"\n--- 2. トークナイザとデータローダーの準備 ---")
    tokenizer = BertJapaneseTokenizer.from_pretrained(PRE_TRAINED_MODEL_NAME)
    
    train_dataset = CustomDataset(
        train_df['text'].values,
        train_df['年代性別_label'].values,
        tokenizer,
        MAX_LEN
    )
    train_sampler = RandomSampler(train_dataset)
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, sampler=train_sampler)

    val_dataset = CustomDataset(
        val_df['text'].values,
        val_df['年代性別_label'].values,
        tokenizer,
        MAX_LEN
    )
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE)

    print("\n--- 3. モデルのセットアップ ---")
    model = BertForClassification(PRE_TRAINED_MODEL_NAME, NUM_LABELS)
    model.to(DEVICE)
    optimizer = AdamW(model.parameters(), lr=2e-5)

    print("\n--- 4. 学習開始 ---")
    for epoch in range(EPOCHS):
        print(f"\nEpoch {epoch + 1}/{EPOCHS}")
        train_loss = train_epoch(model, train_loader, optimizer, DEVICE)
        print(f"Train Loss: {train_loss:.4f}")

        val_acc = eval_model(model, val_loader, DEVICE)
        print(f"Validation Accuracy: {val_acc:.4f}")

    print("\n--- 5. 学習完了 ---")
    torch.save(model.state_dict(), 'bert_classification_model.bin')
    print("モデルを 'bert_classification_model.bin' に保存しました。")


if __name__ == '__main__':
    main()
