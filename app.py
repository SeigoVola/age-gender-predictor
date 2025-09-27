import os
import sys
from flask import Flask, render_template, request, session # session をインポート
from predictor import predict_text, load_model

app = Flask(__name__)
# セッションを利用するために、環境変数からsecret_keyを読み込みます
# 環境変数が設定されていない場合は、開発用の仮のキーを使用します
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev_secret_key_for_local_test')

# アプリケーション起動時にモデルを読み込む
try:
    load_model()
except FileNotFoundError as e:
    print(e, file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f"モデル読み込み中に予期せぬエラーが発生しました: {e}", file=sys.stderr)
    sys.exit(1)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        # ページがリロード（GETリクエスト）されたら、セッションの履歴をクリア
        session.pop('history', None)

    # セッションから履歴を取得（なければ空のリスト）
    history = session.get('history', [])

    # POSTリクエスト（判別ボタンが押された）の場合
    if request.method == 'POST':
        input_text = request.form.get('text', '')
        
        # テキストが空でなければ予測を実行
        if input_text.strip():
            try:
                # predict_textから上位3件の結果リストを受け取る
                results = predict_text(input_text)
                
                # 現在の予測を履歴の先頭に追加
                current_prediction = {
                    "input_text": input_text,
                    "results": results
                }
                history.insert(0, current_prediction)

                # 更新した履歴をセッションに保存
                session['history'] = history
                
            except Exception as e:
                print(f"予測中にエラーが発生しました: {e}", file=sys.stderr)
                # エラーが発生した場合も履歴はそのまま表示
                pass

    # 履歴をテンプレートに渡して表示
    return render_template('index.html', history=history)

# Gunicornから実行されるため、この部分はデプロイ時には不要になります。
# ローカルでテストする場合は、`flask run`コマンドを使用してください。
if __name__ == '__main__':
    # ポート5001で開発サーバーを起動
    app.run(port=5001, debug=False)
