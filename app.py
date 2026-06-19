"""
相見積もり比較アプリ (Flask)

使い方:
  pip install -r requirements.txt
  # tesseract本体が必要: apt-get install tesseract-ocr tesseract-ocr-jpn
  python app.py
  → ブラウザで http://127.0.0.1:5000

人が入力するのは「社名」と「倍率」だけ。
PDFから品番・単価を自動読取りし、単価×倍率(100円切上)で各社を比較する。
"""
import os
import uuid
import tempfile

from flask import Flask, request, render_template, jsonify

from ocr.pipeline import extract_file

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB
UPLOAD_DIR = os.path.join(tempfile.gettempdir(), 'aimitsu_uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze():
    """アップロードされたPDFを処理して、各社の品番・単価を返す。"""
    files = request.files.getlist('pdfs')
    if not files or all(not f.filename for f in files):
        return jsonify(error='PDFを選択してください'), 400

    companies = []
    for idx, f in enumerate(files):
        if not f.filename:
            continue
        path = os.path.join(UPLOAD_DIR, f'{uuid.uuid4().hex}.pdf')
        f.save(path)
        try:
            result = extract_file(path)
        except Exception as e:  # noqa: BLE001
            return jsonify(error=f'{f.filename} の読取りに失敗: {e}'), 500
        finally:
            try:
                os.remove(path)
            except OSError:
                pass
        # 既定の社名は A社/B社/C社…
        default_name = f'{chr(ord("A") + idx)}社'
        companies.append(dict(
            id=idx,
            filename=f.filename,
            name=default_name,
            multiplier=1.0,
            columns=[round(c, 3) for c in result['columns']],
            rows=result['rows'],
        ))

    return jsonify(companies=companies)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
