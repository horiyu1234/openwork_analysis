import pandas as pd
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from transformers import pipeline
import torch

# Hugging Faceのトークナイザーとモデルをロード
tokenizer = AutoTokenizer.from_pretrained('jarvisx17/japanese-sentiment-analysis')
model = AutoModelForSequenceClassification.from_pretrained('jarvisx17/japanese-sentiment-analysis')

# デバイス設定 (GPUが利用可能な場合はGPUを使う)
device = 0 if torch.cuda.is_available() else -1

# 感情分析のパイプラインを設定 (デバイスオプションを指定)
nlp = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer, device=device)

# CSVファイルを読み込む
worklife_nd_Df = pd.read_csv('openwork_reviews_with_attributes_nri.csv')

# 感情分析を行いスコアを付与する関数
def analyze_sentiment(text):
    # 感情分析を実行
    result = nlp(text)
    #print(result) 

    # 結果に応じてポジティブ度合いのスコアを返す
    if result[0]['label'] == 'positive':
        return result[0]['score'] * 100  # ポジティブの確信度をスコアに変換
    elif result[0]['label'] == 'negative':
        return -(result[0]['score'] * 100)  # ネガティブの場合は負のスコア
    else:
        return 0  # 中立の場合

# 各口コミに対して感情分析を実行し、スコアを付与
worklife_nd_Df['score'] = worklife_nd_Df['reputation'].apply(analyze_sentiment)

#print('printing worklife_nd_Df')
#print(worklife_nd_Df)

# スコアに基づいて分類を行う関数
def classify_score(score):
    if abs(score) < 30:  # スコアの絶対値が0.3未満
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

worklife_nd_Df.to_csv('worklife_nri_score_Df_chBASA.csv')


worklife_nd_Df = worklife_nd_Df.loc[:, ~worklife_nd_Df.columns.duplicated()]

print(worklife_nd_Df.head())
print(worklife_nd_Df['classification'].dtypes)


# 分類ごとの行数をカウントして表示
classification_counts = worklife_nd_Df['classification'].value_counts()
print("Classification counts:")
print(classification_counts)
