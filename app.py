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
import re
import uuid
import tempfile

from flask import Flask, request, render_template, jsonify

from ocr.pipeline import extract_file, render_preview

_HEX = re.compile(r'^[0-9a-f]{32}$')


def _pdf_path(file_id):
    """file_id(16進32文字)から保存済みPDFのパスを安全に組み立てる。"""
    if not _HEX.match(file_id or ''):
        return None
    path = os.path.join(UPLOAD_DIR, f'{file_id}.pdf')
    return path if os.path.exists(path) else None

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
        file_id = uuid.uuid4().hex
        path = os.path.join(UPLOAD_DIR, f'{file_id}.pdf')
        f.save(path)                      # 列の指定UIで再利用するため保持する
        try:
            result = extract_file(path)
        except Exception as e:  # noqa: BLE001
            return jsonify(error=f'{f.filename} の読取りに失敗: {e}'), 500
        # 既定の社名は A社/B社/C社…
        default_name = f'{chr(ord("A") + idx)}社'
        companies.append(dict(
            id=idx,
            file_id=file_id,
            filename=f.filename,
            name=default_name,
            multiplier=1.0,
            columns=result['columns'],
            rows=result['rows'],
        ))

    return jsonify(companies=companies)


@app.route('/preview/<file_id>')
def preview(file_id):
    """列指定UI用に、ページ画像と検出した列を返す。"""
    path = _pdf_path(file_id)
    if not path:
        return jsonify(error='ファイルが見つかりません'), 404
    image, columns = render_preview(path)
    return jsonify(image=image, columns=columns)


@app.route('/recolumn', methods=['POST'])
def recolumn():
    """指定された列を単価列として、そのPDFだけ読み直す。"""
    data = request.get_json(silent=True) or {}
    path = _pdf_path(data.get('file_id'))
    if not path:
        return jsonify(error='ファイルが見つかりません'), 404
    try:
        col_index = int(data.get('col_index'))
    except (TypeError, ValueError):
        return jsonify(error='列番号が不正です'), 400
    result = extract_file(path, tanka_col_index=col_index)
    return jsonify(rows=result['rows'], columns=result['columns'])


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
