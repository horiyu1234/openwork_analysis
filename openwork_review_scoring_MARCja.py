from transformers import AutoTokenizer, AutoModelForSequenceClassification
from transformers import pipeline
import torch
import pandas as pd

# トークナイザーとモデルのロード
tokenizer = AutoTokenizer.from_pretrained('llm-book/bert-base-japanese-v3-marc_ja')
model = AutoModelForSequenceClassification.from_pretrained('llm-book/bert-base-japanese-v3-marc_ja')

# デバイス設定
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model.to(device)

# 感情分析パイプラインの設定
nlp = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer, device=0 if torch.cuda.is_available() else -1)

# CSVファイルの読み込み
worklife_nd_Df = pd.read_csv('openwork_reviews_with_attributes_nd.csv')

# 感情分析を行いスコアを付与する関数
def analyze_sentiment(text):
    result = nlp(text)
    if result[0]['label'] == 'positive':
        return result[0]['score'] * 100
    elif result[0]['label'] == 'negative':
        return -(result[0]['score'] * 100)
    else:
        return 0

# 各口コミに対して感情分析を実行し、スコアを付与
worklife_nd_Df['score'] = worklife_nd_Df['reputation'].apply(analyze_sentiment)

# スコアに基づいて分類を行う関数
def classify_score(score):
    if abs(score) < 30:
        return '中立'
    elif score > 0:
        return '良い'
    else:
        return '悪い'

# 分類結果を新たに "classification" 列に追加
worklife_nd_Df['classification'] = worklife_nd_Df['score'].apply(classify_score)

# "reputation" の隣に "score" と "classification" を配置
cols = worklife_nd_Df.columns.tolist()
reputation_idx = cols.index('reputation')
cols.insert(reputation_idx + 1, 'score')
cols.insert(reputation_idx + 2, 'classification')
worklife_nd_Df = worklife_nd_Df[cols]

# classification列を文字列に変換
worklife_nd_Df['classification'] = worklife_nd_Df['classification'].astype(str)
worklife_nd_Df = worklife_nd_Df.dropna(subset=['classification'])

# 重複列の削除
worklife_nd_Df = worklife_nd_Df.loc[:, ~worklife_nd_Df.columns.duplicated()]

# 結果の表示
print(worklife_nd_Df.head())
print(worklife_nd_Df['classification'].dtypes)

# 分類ごとの行数をカウントして表示
classification_counts = worklife_nd_Df['classification'].value_counts()
print("Classification counts:")
print(classification_counts)

# 結果をCSVファイルに保存
worklife_nd_Df.to_csv('worklife_nd_score_Df_jglue.csv', index=False)
