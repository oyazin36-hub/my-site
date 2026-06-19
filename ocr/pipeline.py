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
import io
import re
import base64
import subprocess
from collections import Counter

import cv2
import numpy as np
import fitz  # PyMuPDF
from PIL import Image, ImageOps

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
    """スキャンの微妙な傾きをまっすぐに補正する。"""
    inv = cv2.bitwise_not(gray)
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
    out = subprocess.run(['tesseract', 'stdin', 'stdout', '-l', 'jpn+eng', 'tsv'],
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


def _read_cell(crop_img, psm, scale, thresh=None):
    """切り出した単価セルを数字だけ認識して読む。"""
    pil = Image.fromarray(crop_img)
    if thresh is not None:
        pil = pil.point(lambda x: 255 if x > thresh else 0)
    pil = ImageOps.expand(pil, border=18, fill=255)
    pil = pil.resize((pil.width * scale, pil.height * scale))
    bio = io.BytesIO()
    pil.save(bio, 'PNG')
    out = subprocess.run(['tesseract', 'stdin', 'stdout', '--psm', str(psm),
                          '-c', 'tessedit_char_whitelist=0123456789,.'],
                         input=bio.getvalue(), capture_output=True).stdout.decode('utf-8', 'ignore')
    return _parse_prices(out)


_PASSES = [(7, 3, None), (8, 4, None), (7, 3, 150), (8, 4, 170)]


def _vote_price(crops, row_text=''):
    """複数の画像(加工あり/なし)×4通りで読み、行テキストも加えて多数決。
    crops: 同じセルを別々の画像から切り出したもののリスト。
    加工が合う画像の読みが票を集めるので、社ごとに自動で最適化される。"""
    votes = Counter()
    for crop in crops:
        if crop is None or crop.size == 0:
            continue
        for psm, scale, th in _PASSES:
            for v in set(_read_cell(crop, psm, scale, th)):
                votes[v] += 1
    for v in set(_parse_prices(row_text)):   # 行全体の読みも1票
        votes[v] += 1
    if not votes:
        return None, ''
    value, n = votes.most_common(1)[0]
    conf = '◎' if n >= 4 else ('○' if n >= 2 else '△')
    return value, conf


def _autocontrast(gray_img):
    """コントラストを最大化したグレー画像（加工が軽い版）。"""
    return cv2.normalize(gray_img, None, 0, 255, cv2.NORM_MINMAX)


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


def _auto_tanka_column(columns, sample_imgs, sample_bands, W):
    """検出した列の中から「単価列」を自動で選ぶ。
    数字が入っている列(単価/金額)を見つけ、その右から2番目(=単価。一番右は金額)を返す。
    数量や金額しか無い場合の保険も込み。"""
    gaps = _columns_to_gaps(columns)
    if not gaps:
        return None
    # 各列について、サンプル行で価格が読めた回数を数える
    hits = [0] * len(gaps)
    for gi, (a, b) in enumerate(gaps):
        x0, x1 = int(W * a), int(W * b)
        if x1 - x0 < W * 0.03:        # 細すぎる列は対象外
            continue
        for img in sample_imgs:
            for (y0, y1) in sample_bands:
                crop = img[max(0, y0):y1, x0:x1]
                if crop.size and _read_cell(crop, 7, 3):
                    hits[gi] += 1
                    break
    n_samples = max(1, len(sample_bands))
    numeric = [gi for gi, h in enumerate(hits) if h >= n_samples * 0.4]
    if not numeric:
        return None
    # 一番右が金額、その左が単価
    tanka_gi = numeric[-2] if len(numeric) >= 2 else numeric[-1]
    return gaps[tanka_gi]


def _pick_tanka_column(columns, tanka_col_index):
    """単価列を手動指定する場合の(左,右)割合。"""
    gaps = _columns_to_gaps(columns)
    if tanka_col_index is not None and 0 <= tanka_col_index < len(gaps):
        return gaps[tanka_col_index]
    return None


# --- メイン: 1ファイルを処理 -----------------------------------------
def extract_file(pdf_path, tanka_col_index=None):
    """
    PDF1ファイルを処理して部品リストを返す。
    返り値: { 'rows': [ {key, price, conf, cell_img}, ... ],
              'columns': [...], 'pages': n }
    tanka_col_index: 単価列を手動指定する場合の列番号(0始まり)。Noneなら自動推定。
    """
    pages = render_pages(pdf_path)
    rows = {}
    order = []
    detected_columns = []
    for gray in pages:
        g, clean = preprocess(gray)            # g=傾き補正グレー, clean=罫線除去+二値化
        gac = _autocontrast(g)                 # 加工が軽いコントラスト強調版
        columns = detect_columns(g)            # 罫線除去前(g)で列を検出
        if not detected_columns:               # 列指定UI用に1ページ目の列を保持
            detected_columns = columns
        H, W = g.shape
        words = _tsv_words(clean)
        # 行(品番のある行)を先に拾う
        data_bands = []
        for band in _group_bands(words):
            joined = ''.join(x['text'] for x in band['it'])
            key = normalize_key(joined)
            if not key:
                continue
            y0 = int(min(x['t'] for x in band['it']) - 3)
            y1 = int(max(x['b'] for x in band['it']) + 3)
            data_bands.append((key, joined, y0, y1))

        # 単価列を決める（手動指定 > 自動推定）
        col = _pick_tanka_column(columns, tanka_col_index)
        if col is None:
            sample = [(y0, y1) for (_, _, y0, y1) in data_bands[:6]]
            col = _auto_tanka_column(columns, [gac, clean], sample, W)

        for key, joined, y0, y1 in data_bands:
            jflag = '除外' in joined or '樹脂' in joined
            price, conf, cell = None, '', ''
            if not jflag:
                if col is not None:
                    x0, x1 = int(W * col[0]), int(W * col[1])
                else:                          # 列が取れない時は右側を広めに
                    x0, x1 = int(W * 0.40), int(W * 0.90)
                # 加工なし(gac)と加工あり(clean)の両方で読んで多数決
                crops = [gac[max(0, y0):y1, x0:x1], clean[max(0, y0):y1, x0:x1]]
                price, conf = _vote_price(crops, joined)
                cell = _crop_b64(gac, x0, x1, y0, y1)
            entry = dict(key=key, price=price, conf=('除' if jflag else conf),
                         flag='除外' if jflag else '', cell=cell)
            if key not in rows:
                rows[key] = entry
                order.append(key)
            elif rows[key]['price'] is None and price is not None:
                rows[key] = entry
    return dict(rows=[rows[k] for k in order],
                columns=[round(c, 4) for c in detected_columns], pages=len(pages))


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
