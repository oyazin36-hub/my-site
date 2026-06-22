"""
見積書PDFから「品番」と「単価」を読み取るOCRパイプライン。

処理の流れ:
  1. PDFを高解像度で画像化         (PyMuPDF)
  2. 画像をくっきり加工            (傾き補正 + 罫線除去 + 適応的二値化 / OpenCV)
  3. 行を検出して品番を読み取る     (Tesseract)
  4. 単価列を複数回読んで多数決     (信頼度 ◎/○/△ を付与)

単価は10円きざみ（末尾0）を前提にノイズを除去する。
金額列(=単価×数量)は使わない。AIビジョンは使わない。
"""
import os
import re
import base64
import shutil
import subprocess
from collections import Counter

import cv2
import numpy as np
import fitz  # PyMuPDF


def _find_tesseract():
    """tesseract本体の場所を探す。環境変数 > PATH > Windows既定の場所 の順。"""
    env = os.environ.get('TESSERACT_CMD')
    if env and os.path.exists(env):
        return env
    found = shutil.which('tesseract')
    if found:
        return found
    for p in (r'C:\Program Files\Tesseract-OCR\tesseract.exe',
              r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe'):
        if os.path.exists(p):
            return p
    return 'tesseract'   # 見つからなければPATHに任せる


TESSERACT = _find_tesseract()

# --- 設定 -------------------------------------------------------------
RENDER_ZOOM = 3.5          # PDF→画像の拡大率
PRICE_UNIT = 10            # 単価は10円きざみ
PRICE_MIN, PRICE_MAX = 300, 200000

# 品番: 任意の接頭辞(WIDRY07-等) + 3桁 + M + 3桁
_PN = re.compile(r'(?:[A-Za-z]{2,6}\d{0,2}[-_ ]?)?([0-9oOlIzZeg]{3})[-_ ]?M[-_ ]?([0-9oOlIzZeBsSgt]{3})')
_PRICE = re.compile(r'\d{1,3}(?:[,.]\d{3})|\d{3,6}')
# OCRが数字を英字に誤読する分の補正表
_DIGIT = str.maketrans({'o': '0', 'O': '0', 'Q': '0', 'D': '0', 'l': '1', 'I': '1',
                        'i': '1', 'z': '2', 'Z': '2', 'S': '5', 's': '5', 'B': '8',
                        'e': '6', 'g': '9', 't': '1'})


# --- 1. PDF → 画像 ----------------------------------------------------
def render_pages(pdf_path, zoom=RENDER_ZOOM):
    """PDFの各ページをグレースケールのnumpy配列にして返す。"""
    doc = fitz.open(pdf_path)
    pages = []
    for page in doc:
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        if pix.n >= 3:
            gray = cv2.cvtColor(img[:, :, :3], cv2.COLOR_RGB2GRAY)
        else:
            gray = img[:, :, 0]
        pages.append(gray)
    return pages


# --- 2. 前処理(くっきり化) -------------------------------------------
def _deskew(gray):
    """スキャンの微妙な傾きをまっすぐに補正する。角度計算は縮小画像で行い高速化。"""
    small = cv2.resize(gray, (gray.shape[1] // 3, gray.shape[0] // 3))
    inv = cv2.bitwise_not(small)
    thr = cv2.threshold(inv, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    coords = np.column_stack(np.where(thr > 0))
    if len(coords) < 50:
        return gray
    ang = cv2.minAreaRect(coords)[-1]
    ang = -(90 + ang) if ang < -45 else -ang
    if abs(ang) < 0.2:
        return gray
    h, w = gray.shape
    m = cv2.getRotationMatrix2D((w // 2, h // 2), ang, 1.0)
    return cv2.warpAffine(gray, m, (w, h), flags=cv2.INTER_CUBIC, borderValue=255)


def preprocess(gray):
    """傾き補正 + 罫線除去 + 適応的二値化。読取り用のきれいな画像を返す。"""
    g = _deskew(gray)
    bw = cv2.adaptiveThreshold(g, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                               cv2.THRESH_BINARY, 31, 15)
    inv = cv2.bitwise_not(bw)
    hor = cv2.morphologyEx(inv, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1)))
    ver = cv2.morphologyEx(inv, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40)))
    lines = cv2.dilate(cv2.add(hor, ver), np.ones((3, 3), np.uint8), iterations=1)
    clean = cv2.bitwise_or(bw, lines)        # 罫線を白で塗りつぶす
    clean = cv2.medianBlur(clean, 3)
    return g, clean                          # (傾き補正済みグレー, くっきり画像)


# --- 3. Tesseractで行と列を検出 --------------------------------------
def _tsv_words(img_array):
    """画像をTesseractにかけ、単語ごとの位置リストを返す。"""
    ok, buf = cv2.imencode('.png', img_array)
    out = subprocess.run([TESSERACT, 'stdin', 'stdout', '-l', 'jpn+eng', 'tsv'],
                         input=buf.tobytes(), capture_output=True).stdout.decode('utf-8', 'ignore')
    words = []
    for line in out.splitlines()[1:]:
        c = line.split('\t')
        if len(c) < 12:
            continue
        try:
            float(c[10])
        except ValueError:
            continue
        text = c[11].strip()
        if not text:
            continue
        l, t, w, h = int(c[6]), int(c[7]), int(c[8]), int(c[9])
        words.append(dict(l=l, t=t, w=w, h=h, b=t + h, cy=t + h / 2, text=text))
    return words


def _group_bands(words, tol=16):
    """単語を縦位置でまとめて『行』を復元する。"""
    bands = []
    for wd in sorted(words, key=lambda x: x['cy']):
        for b in bands:
            if abs(wd['cy'] - b['cy']) <= tol:
                b['it'].append(wd)
                b['cy'] = (b['cy'] * b['n'] + wd['cy']) / (b['n'] + 1)
                b['n'] += 1
                break
        else:
            bands.append(dict(cy=wd['cy'], n=1, it=[wd]))
    for b in bands:
        b['it'].sort(key=lambda x: x['l'])
    return bands


def detect_columns(gray_img):
    """罫線(縦線)を検出して列の境界x座標(0..1の割合)を返す。罫線除去前の画像を渡すこと。"""
    h, w = gray_img.shape
    band = gray_img[int(h * 0.28):int(h * 0.96), :]
    band = cv2.adaptiveThreshold(band, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                 cv2.THRESH_BINARY, 31, 15)
    inv = cv2.bitwise_not(band)
    ver = cv2.morphologyEx(inv, cv2.MORPH_OPEN,
                           cv2.getStructuringElement(cv2.MORPH_RECT, (1, max(20, band.shape[0] // 30))))
    col_sum = ver.sum(axis=0).astype(float)
    if col_sum.max() <= 0:
        return []
    thr = col_sum.max() * 0.4
    peaks, i = [], 0
    while i < w:
        if col_sum[i] > thr:
            j = i
            while j < w and col_sum[j] > thr:
                j += 1
            peaks.append((i + j) / 2 / w)
            i = j
        else:
            i += 1
    # 近すぎる線をまとめる
    merged = []
    for p in peaks:
        if not merged or p - merged[-1] > 0.02:
            merged.append(p)
        else:
            merged[-1] = (merged[-1] + p) / 2
    return merged


# --- 4. 単価セルを複数回読んで多数決 ---------------------------------
def _parse_prices(text):
    out = []
    for m in _PRICE.finditer(text):
        v = int(m.group().replace(',', '').replace('.', ''))
        if PRICE_MIN <= v <= PRICE_MAX and v % PRICE_UNIT == 0:
            out.append(v)
    return out


def _autocontrast(gray_img):
    """コントラストを最大化したグレー画像（加工が軽い版）。"""
    return cv2.normalize(gray_img, None, 0, 255, cv2.NORM_MINMAX)


def _ocr_column_strip(img, x0, x1, scale=2):
    """列(縦長)をまとめて1回でOCRし、(縦中心y, 価格) のリストを返す。
    1行ずつ何度もtesseractを起動するより桁違いに速い。"""
    x0 = max(0, x0)
    if x1 - x0 < 4:
        return []
    strip = img[:, x0:x1]
    if strip.size == 0:
        return []
    strip = cv2.resize(strip, (strip.shape[1] * scale, strip.shape[0] * scale))
    ok, buf = cv2.imencode('.png', strip)
    out = subprocess.run([TESSERACT, 'stdin', 'stdout',
                          '-c', 'tessedit_char_whitelist=0123456789,.', '--psm', '6', 'tsv'],
                         input=buf.tobytes(), capture_output=True).stdout.decode('utf-8', 'ignore')
    results = []
    for line in out.splitlines()[1:]:
        c = line.split('\t')
        if len(c) < 12:
            continue
        text = c[11].strip()
        if not text:
            continue
        cy = (int(c[7]) + int(c[9]) / 2) / scale
        for v in _parse_prices(text):
            results.append((cy, v))
    return results


def _row_value(strip_gac, strip_clean, y0, y1, row_text=''):
    """1行の単価を、加工なし/あり(各2スケール)の列OCR結果から多数決で決める。
    ◎=両画像が一致 or 合計3票以上 / ○=2票 / △=1票(怪しい)。"""
    gac = [v for (cy, v) in strip_gac if y0 <= cy <= y1]
    cln = [v for (cy, v) in strip_clean if y0 <= cy <= y1]
    txt = _parse_prices(row_text)
    allv = gac + cln + txt
    if not allv:
        return None, ''
    votes = Counter(allv)
    value, n = votes.most_common(1)[0]
    cross = (value in set(gac)) and (value in set(cln))   # 加工なし/ありが一致
    if cross or n >= 3:
        conf = '◎'
    elif n == 2:
        conf = '○'
    else:
        conf = '△'
    return value, conf


def _crop_b64(gray_img, x0, x1, y0, y1):
    """単価セルの切り出し画像をbase64(PNG)で返す。人の目視確認用。"""
    crop = gray_img[max(0, y0):y1, max(0, x0):x1]
    if crop.size == 0:
        return ''
    ok, buf = cv2.imencode('.png', crop)
    return 'data:image/png;base64,' + base64.b64encode(buf.tobytes()).decode()


# --- 品番の正規化 -----------------------------------------------------
def normalize_key(text_joined):
    m = _PN.search(text_joined)
    if not m:
        return None
    grp = m.group(1).translate(_DIGIT)
    suf = m.group(2).translate(_DIGIT)
    if grp.isdigit() and suf.isdigit():
        return f'{grp}-M{suf}'
    return None


def _columns_to_gaps(columns):
    return [(columns[i], columns[i + 1]) for i in range(len(columns) - 1)]


def _auto_tanka_column(columns, img, data_bands, W):
    """検出した列の中から「単価列」を自動で選ぶ。
    各列を1回ずつまとめOCRし、価格が入っている列(単価/金額)を見つけ、
    その右から2番目(=単価。一番右は金額)を返す。"""
    gaps = _columns_to_gaps(columns)
    if not gaps:
        return None, None
    bands = data_bands[:20]
    hits = [0] * len(gaps)
    for gi, (a, b) in enumerate(gaps):
        x0, x1 = int(W * a), int(W * b)
        if x1 - x0 < W * 0.03:            # 細すぎる列は対象外
            continue
        strip = _ocr_column_strip(img, x0, x1)
        for (_key, _j, y0, y1) in bands:
            if any(y0 <= cy <= y1 for (cy, _v) in strip):
                hits[gi] += 1
    n = max(1, len(bands))
    numeric = [gi for gi, h in enumerate(hits) if h >= n * 0.4]
    if not numeric:
        return None, None
    tanka_gi = numeric[-2] if len(numeric) >= 2 else numeric[-1]
    return gaps[tanka_gi], tanka_gi


def _pick_tanka_column(columns, tanka_col_index):
    """単価列を手動指定する場合の(左,右)割合。"""
    gaps = _columns_to_gaps(columns)
    if tanka_col_index is not None and 0 <= tanka_col_index < len(gaps):
        return gaps[tanka_col_index]
    return None


# --- メイン: 1ファイルを処理 -----------------------------------------
def _page_to_gray(page, zoom=RENDER_ZOOM):
    """fitzのページ1枚をグレースケールnumpy配列にする。"""
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    if pix.n >= 3:
        return cv2.cvtColor(img[:, :, :3], cv2.COLOR_RGB2GRAY)
    return img[:, :, 0]


_NUMW = re.compile(r'^\d{1,3}(?:,\d{3})+$|^\d{3,7}$')


def _extract_text_rows(page):
    """文字データ(テキスト層)から品番と単価を直接読む。OCRより確実。
    返り値: [(key, price, jflag), ...] / テキスト層が無ければ None。"""
    if len(page.get_text().strip()) < 20:
        return None                       # テキスト層なし(スキャン画像) -> OCRへ
    words = page.get_text("words")        # (x0,y0,x1,y1, word, block, line, word_no)
    if not words:
        return None
    # 単語を縦位置(行)でまとめる
    bands = []
    for w in sorted(words, key=lambda w: (w[1] + w[3]) / 2):
        cy = (w[1] + w[3]) / 2
        for b in bands:
            if abs(cy - b['cy']) <= 3:
                b['it'].append(w)
                b['cy'] = (b['cy'] * b['n'] + cy) / (b['n'] + 1)
                b['n'] += 1
                break
        else:
            bands.append(dict(cy=cy, n=1, it=[w]))
    out = []
    for b in bands:
        items = sorted(b['it'], key=lambda w: w[0])
        joined = ''.join(w[4] for w in items)
        key = normalize_key(joined)
        if not key:
            continue
        jflag = '除外' in joined or '樹脂' in joined
        nums = []
        for w in items:
            t = w[4].replace(',', '')
            if _NUMW.match(w[4]) and t.isdigit():
                v = int(t)
                if 300 <= v <= 2000000:
                    nums.append((w[0], v))
        price = None
        if not jflag and nums:
            nums.sort()
            price = nums[-2][1] if len(nums) >= 2 else nums[-1][1]   # 右から2番目=単価(一番右は金額)
        out.append((key, price, jflag))
    return out


def extract_file(pdf_path, tanka_col_index=None):
    """
    PDF1ファイルを処理して部品リストを返す。
    文字データ(テキスト層)があれば直接読み取り(誤読なし)、無ければOCRする。
    返り値: { 'rows': [ {key, price, conf, cell_img}, ... ], 'columns': [...], 'pages': n }
    """
    doc = fitz.open(pdf_path)
    rows = {}
    order = []
    detected_columns = []

    def _add(key, price, conf, flag, cell):
        entry = dict(key=key, price=price, conf=conf, flag=flag, cell=cell)
        if key not in rows:
            rows[key] = entry
            order.append(key)
        elif rows[key]['price'] is None and price is not None:
            rows[key] = entry

    for page in doc:
        text_rows = _extract_text_rows(page)
        if text_rows is not None:
            # --- 文字データから直接(確実) ---
            for key, price, jflag in text_rows:
                _add(key, price, ('除' if jflag else ('文' if price is not None else '')),
                     '除外' if jflag else '', '')
            continue

        # --- スキャン画像 -> OCR ---
        gray = _page_to_gray(page)
        g, clean = preprocess(gray)
        gac = _autocontrast(g)
        columns = detect_columns(g)
        if not detected_columns:
            detected_columns = columns
        H, W = g.shape
        words = _tsv_words(clean)
        data_bands = []
        for band in _group_bands(words):
            joined = ''.join(x['text'] for x in band['it'])
            key = normalize_key(joined)
            if not key:
                continue
            y0 = int(min(x['t'] for x in band['it']) - 3)
            y1 = int(max(x['b'] for x in band['it']) + 3)
            data_bands.append((key, joined, y0, y1))

        col = _pick_tanka_column(columns, tanka_col_index)
        if col is None:
            col, _gi = _auto_tanka_column(columns, gac, data_bands, W)
        if col is not None:
            x0, x1 = int(W * col[0]), int(W * col[1])
        else:
            x0, x1 = int(W * 0.40), int(W * 0.90)

        strip_gac = _ocr_column_strip(gac, x0, x1, 2) + _ocr_column_strip(gac, x0, x1, 3)
        strip_clean = _ocr_column_strip(clean, x0, x1, 2) + _ocr_column_strip(clean, x0, x1, 3)

        for key, joined, y0, y1 in data_bands:
            jflag = '除外' in joined or '樹脂' in joined
            price, conf, cell = None, '', ''
            if not jflag:
                price, conf = _row_value(strip_gac, strip_clean, y0, y1, joined)
                cell = _crop_b64(gac, x0, x1, y0, y1)
            _add(key, price, ('除' if jflag else conf), '除外' if jflag else '', cell)

    return dict(rows=[rows[k] for k in order],
                columns=[round(c, 4) for c in detected_columns], pages=len(doc))


def render_preview(pdf_path, page_index=0, width=900):
    """列指定UI用に、1ページ目の画像(base64)と検出した列(0..1の割合)を返す。"""
    pages = render_pages(pdf_path)
    if not pages:
        return '', []
    gray = pages[min(page_index, len(pages) - 1)]
    g, _clean = preprocess(gray)
    columns = detect_columns(g)
    h, w = g.shape
    small = cv2.resize(g, (width, int(h * width / w)))
    ok, buf = cv2.imencode('.png', small)
    uri = 'data:image/png;base64,' + base64.b64encode(buf.tobytes()).decode()
    return uri, [round(c, 4) for c in columns]
