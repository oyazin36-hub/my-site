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
# 品番の形式 (2種類に対応)
#  ① M形式:   WIDRY07-107-M001 / 107-M001  (末尾が M+3桁)
#  ② 図番形式: 26041-20-001                (5桁-2桁-3桁, Mなし)
_PN_M = re.compile(r'(?:[A-Za-z]{2,6}\d{0,2}[-_ ]?)?([0-9oOlIzZeg]{3})[-_ ]?M[-_ ]?([0-9oOlIzZeBsSgt]{3})')
_PN_FIG = re.compile(r'([0-9oOlIzZeg]{5})[-_ ]([0-9oOlIzZeg]{2})[-_ ]([0-9oOlIzZeg]{3})')
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


def _ocr_key_strip(img, x0, x1, scale=2, whitelist='0123456789-M', parser=None):
    """品番列(縦1本)をまとめてOCRし、(縦中心y, 正規化済み品番) のリストを返す。
    品番に使われる文字だけを認識させて誤読を減らす。単価と同じ多数決方式に使う。"""
    parser = parser or normalize_key
    x0 = max(0, x0)
    if x1 - x0 < 4:
        return []
    strip = img[:, x0:x1]
    if strip.size == 0:
        return []
    strip = cv2.resize(strip, (strip.shape[1] * scale, strip.shape[0] * scale))
    ok, buf = cv2.imencode('.png', strip)
    out = subprocess.run([TESSERACT, 'stdin', 'stdout',
                          '-c', 'tessedit_char_whitelist=' + whitelist, '--psm', '6', 'tsv'],
                         input=buf.tobytes(), capture_output=True).stdout.decode('utf-8', 'ignore')
    lines = {}
    for line in out.splitlines()[1:]:
        c = line.split('\t')
        if len(c) < 12:
            continue
        t = c[11].strip()
        if not t:
            continue
        lk = (c[2], c[3], c[4])          # (block, par, line) で行ごとにまとめる
        cy = (int(c[7]) + int(c[9]) / 2) / scale
        lines.setdefault(lk, {'cy': [], 'txt': []})
        lines[lk]['cy'].append(cy)
        lines[lk]['txt'].append(t)
    res = []
    for v in lines.values():
        k = parser(''.join(v['txt'])) or parser(' '.join(v['txt']))
        if k:
            res.append((sum(v['cy']) / len(v['cy']), k))
    return res


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
    m = _PN_M.search(text_joined)              # ① M形式を優先
    if m:
        grp = m.group(1).translate(_DIGIT)
        suf = m.group(2).translate(_DIGIT)
        if grp.isdigit() and suf.isdigit():
            return f'{grp}-M{suf}'
    m = _PN_FIG.search(text_joined)            # ② 図番形式 26041-20-001
    if m:
        a = m.group(1).translate(_DIGIT)
        b = m.group(2).translate(_DIGIT)
        c = m.group(3).translate(_DIGIT)
        if a.isdigit() and b.isdigit() and c.isdigit():
            return f'{a}-{b}-{c}'
    return None


# ---- 汎用品番検出(形状学習) ------------------------------------------
# 会社ごとに品番の形式が違うため、既知の2形式に当てはまらない時は
# 「この見積書の品番はどんな形か」を書面内から学習する。
# 例: OM6283-08-001 (英2+数4-数2-数3) / OM6283 07 002 (空白区切り) など。
_CAND_HYPHEN = re.compile(r'[A-Za-z0-9]{2,8}(?:-[A-Za-z0-9]{1,4}){1,3}')
_CAND_SPACE = re.compile(r'[A-Za-z0-9]{4,8}(?: [A-Za-z0-9]{1,4}){1,3}')
_DITTO = re.compile(r'^[^A-Za-z0-9]{0,4}(\d{3})$')   # 「〃 007」のような同上行


def _clean_key(tok):
    tok = re.sub(r'[ _/]+', '-', tok.strip().upper())
    return tok.strip('-')


def _shape_of(tok):
    """品番の「形」: 数字(とO等の紛らわしい字)をD、英字をAに置換。学習・照合用。"""
    out = []
    for ch in tok:
        if ch in '-_ ':
            out.append('-')
        elif ch in '0123456789oO':
            out.append('D')
        elif ch.isalpha():
            out.append('A')
        else:
            out.append('?')
    return ''.join(out)


def _candidates(text, allow_space):
    pats = [_CAND_HYPHEN] + ([_CAND_SPACE] if allow_space else [])
    found = []
    for p in pats:
        for m in p.finditer(text):
            t = m.group()
            if sum(c.isdigit() for c in t) >= 4 and 6 <= len(t) <= 20:
                found.append(t)
    return found


def _learn_shape(texts):
    """行テキスト群から品番の形を学習。(shape, allow_space) か None。
    同じ形が3行以上出てくれば品番とみなす(電話番号や日付は形が揃わない)。"""
    for allow_space in (False, True):
        shapes = Counter()
        for t in texts:
            cands = _candidates(t, allow_space)
            if cands:
                shapes[_shape_of(_clean_key(cands[0]))] += 1
        if shapes:
            top, n = shapes.most_common(1)[0]
            if n >= 3:
                return top, allow_space
    return None


def _generic_key(text, shape, allow_space):
    for t in _candidates(text, allow_space):
        k = _clean_key(t)
        if _shape_of(k) == shape:
            return k
    return None


_FIG_KEY = re.compile(r'^\d{5}-\d{2}-\d{3}$')


def _fix_prefix_outliers(rows, order):
    """品番の先頭グループ(例: 26041 / OM6283)を同一見積内で照合し、
    浮いた1件を自動補正する。例: 他が全て 26041-… で1件だけ 06041-… → 26041 に補正。
    条件を保守的に: 先頭グループ5文字以上・多数派3件以上・外れ値1件のみ・
    差は1文字のみ・補正先と衝突しない。(107-M001等の短い先頭は対象外)"""
    elig = [k for k in order if '-' in k and len(k.split('-', 1)[0]) >= 5]
    if len(elig) < 4:
        return
    pref = Counter(k.split('-', 1)[0] for k in elig)
    dom, n = pref.most_common(1)[0]
    if n < 3:
        return
    for k in list(order):
        if '-' not in k:
            continue
        p = k.split('-', 1)[0]
        if len(p) < 5 or p == dom or pref.get(p, 0) != 1 or len(p) != len(dom):
            continue
        if sum(a != b for a, b in zip(p, dom)) != 1:
            continue
        nk = dom + k[len(p):]
        if nk in rows:
            continue
        entry = rows.pop(k)
        entry['key'] = nk
        entry['key_fixed'] = k          # 元の読み値を保持
        rows[nk] = entry
        order[order.index(k)] = nk


def _columns_to_gaps(columns):
    return [(columns[i], columns[i + 1]) for i in range(len(columns) - 1)]


def _auto_tanka_column(columns, img, data_bands, W, key_x=None):
    """検出した列の中から「単価列」を自動で選ぶ。
    価格が入っている列が2つ以上 → 右から2番目が単価(一番右は金額)。
    1つだけ(単価列がほぼ空欄で金額列だけの見積) → その左隣を単価、
    その列を金額としてフォールバック用に返す。
    key_x=(kx0,kx1): 品番列の範囲。品番の数字を価格と誤認しないよう候補から除外。
    返り値: (単価gap or None, フォールバック用の金額gap or None)"""
    gaps = _columns_to_gaps(columns)
    if not gaps:
        return None, None
    bands = data_bands[:20]
    hits = [0] * len(gaps)
    for gi, (a, b) in enumerate(gaps):
        x0, x1 = int(W * a), int(W * b)
        if x1 - x0 < W * 0.03:            # 細すぎる列は対象外
            continue
        if key_x is not None:             # 品番列と半分以上重なる列は対象外
            ov = min(x1, key_x[1]) - max(x0, key_x[0])
            if ov > (x1 - x0) * 0.5:
                continue
        strip = _ocr_column_strip(img, x0, x1)
        for band in bands:
            y0, y1 = band[2], band[3]
            if any(y0 <= cy <= y1 for (cy, _v) in strip):
                hits[gi] += 1
    n = max(1, len(bands))
    numeric = [gi for gi, h in enumerate(hits) if h >= n * 0.4]
    if not numeric:
        return None, None
    if len(numeric) >= 2:
        return gaps[numeric[-2]], None
    gi = numeric[0]
    tanka = gaps[gi - 1] if gi >= 1 else None
    return tanka, gaps[gi]


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


def _extract_text_lines(page):
    """文字データ(テキスト層)を行ごとに取り出す。OCRより確実。
    返り値: [{'joined','left','nums'}, ...] / テキスト層が無ければ None。"""
    if len(page.get_text().strip()) < 20:
        return None                       # テキスト層なし(スキャン画像) -> OCRへ
    words = page.get_text("words")        # (x0,y0,x1,y1, word, block, line, word_no)
    if not words:
        return None
    wp = page.rect.width
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
        left = ' '.join(w[4] for w in items if w[0] < wp * 0.5)
        nums = []
        for w in items:
            t = w[4].replace(',', '')
            if _NUMW.match(w[4]) and t.isdigit():
                v = int(t)
                if 300 <= v <= 2000000:
                    nums.append((w[0], v))
        nums.sort()
        out.append(dict(joined=joined, left=left, nums=nums))
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

    def _add(key, price, conf, flag, cell, kconf=''):
        entry = dict(key=key, price=price, conf=conf, flag=flag, cell=cell, kconf=kconf)
        if key not in rows:
            rows[key] = entry
            order.append(key)
        elif rows[key]['price'] is None and price is not None:
            rows[key] = entry

    # ---- 第1段: 各ページの下ごしらえ(テキスト層 or OCR素材) ----
    arts = []
    for page in doc:
        lines = _extract_text_lines(page)
        if lines is not None:
            arts.append(dict(kind='text', lines=lines))
            continue
        gray = _page_to_gray(page)
        g, clean = preprocess(gray)
        gac = _autocontrast(g)
        columns = detect_columns(g)
        if not detected_columns:
            detected_columns = columns
        H, W = g.shape
        words = _tsv_words(clean)
        raw_bands = []
        for band in _group_bands(words):
            raw_bands.append(dict(
                joined=''.join(x['text'] for x in band['it']),
                left=' '.join(x['text'] for x in band['it'] if x['l'] < W * 0.5),
                y0=int(min(x['t'] for x in band['it']) - 3),
                y1=int(max(x['b'] for x in band['it']) + 3),
                items=band['it']))
        arts.append(dict(kind='ocr', g=g, clean=clean, gac=gac,
                         columns=columns, W=W, raw=raw_bands))

    # ---- 第2段: 品番の方式を決める(既知形式 or 書類全体から形を学習) ----
    known_count = 0
    for a in arts:
        src = a['lines'] if a['kind'] == 'text' else a['raw']
        known_count += sum(1 for x in src if normalize_key(x['joined']))
    generic = None                              # (shape, allow_space)
    if known_count < 3:
        corpus = []
        for a in arts:
            src = a['lines'] if a['kind'] == 'text' else a['raw']
            corpus += [x['left'] for x in src]
        generic = _learn_shape(corpus)

    last_full = [None]                          # 「〃(同上)」行はページをまたいで直前の品番を継承
    def _key_of(left, joined):
        if generic:
            shape, asp = generic
            k = _generic_key(left, shape, asp)
            if k:
                last_full[0] = k
                return k
            m = _DITTO.match(left.strip())
            if m and last_full[0] and '-' in last_full[0]:
                return last_full[0].rsplit('-', 1)[0] + '-' + m.group(1)
            return None
        return normalize_key(joined)

    # ---- 第3段: ページごとに読み取り ----
    for a in arts:
        if a['kind'] == 'text':                 # 文字データから直接(確実)
            for ln in a['lines']:
                key = _key_of(ln['left'], ln['joined'])
                if not key:
                    continue
                jflag = '除外' in ln['joined'] or '樹脂' in ln['joined']
                price = None
                if not jflag and ln['nums']:
                    nums = ln['nums']
                    price = nums[-2][1] if len(nums) >= 2 else nums[-1][1]
                _add(key, price, ('除' if jflag else ('文' if price is not None else '')),
                     '除外' if jflag else '', '')
            continue

        # --- スキャン画像ページ ---
        g, clean, gac = a['g'], a['clean'], a['gac']
        columns, W, raw_bands = a['columns'], a['W'], a['raw']
        data_bands = []
        for rb in raw_bands:
            key = _key_of(rb['left'], rb['joined'])
            if key:
                data_bands.append((key, rb['joined'], rb['y0'], rb['y1'], rb['items']))

        # 品番列のx範囲を推定
        kxs = []
        for _key, _j, _y0, _y1, items in data_bands:
            for x in items:
                if x['l'] < W * 0.45 and sum(ch.isdigit() for ch in x['text']) >= 3:
                    kxs += [x['l'], x['l'] + x['w']]
        if kxs:
            kx0, kx1 = max(0, min(kxs) - 12), min(W, max(kxs) + 12)
        else:
            kx0, kx1 = int(W * 0.02), int(W * 0.30)

        col = _pick_tanka_column(columns, tanka_col_index)
        kcol = None                             # 単価が空欄の見積用: 金額列フォールバック
        if col is None:
            col, kcol = _auto_tanka_column(columns, gac, data_bands, W, (kx0, kx1))
        if col is None and kcol is not None:    # 金額列しか無い場合はそれを単価扱い
            col, kcol = kcol, None
        if col is not None:
            x0, x1 = int(W * col[0]), int(W * col[1])
        else:
            x0, x1 = int(W * 0.40), int(W * 0.90)

        strip_gac = _ocr_column_strip(gac, x0, x1, 2) + _ocr_column_strip(gac, x0, x1, 3)
        strip_clean = _ocr_column_strip(clean, x0, x1, 2) + _ocr_column_strip(clean, x0, x1, 3)
        kstrip_gac = kstrip_clean = []
        cx1 = x1
        if kcol is not None:
            kxx0, kxx1 = int(W * kcol[0]), int(W * kcol[1])
            kstrip_gac = _ocr_column_strip(gac, kxx0, kxx1, 2) + _ocr_column_strip(gac, kxx0, kxx1, 3)
            kstrip_clean = _ocr_column_strip(clean, kxx0, kxx1, 2) + _ocr_column_strip(clean, kxx0, kxx1, 3)
            cx1 = kxx1                          # 確認用画像は金額列まで含めて切り出す

        def _read_price(y0, y1, row_text):
            price, conf = _row_value(strip_gac, strip_clean, y0, y1, row_text)
            if price is None and kcol is not None:
                # 単価欄が空欄 → 金額欄を読む(数量1なら金額=単価)。信頼度は1段下げる
                price, conf = _row_value(kstrip_gac, kstrip_clean, y0, y1, '')
                conf = {'◎': '○', '○': '△'}.get(conf, conf)
            return price, conf

        # 品番列も単価と同じく、加工なし/あり×2スケールで読んで多数決に使う
        if generic:
            shape, asp = generic
            letters = ''.join(sorted({c for k, *_ in data_bands for c in k if c.isalpha()}))
            wl = '0123456789-' + letters
            parser = lambda t: _generic_key(t, shape, asp)   # noqa: E731
        else:
            wl, parser = '0123456789-M', None
        keys_g = (_ocr_key_strip(gac, kx0, kx1, 2, wl, parser)
                  + _ocr_key_strip(gac, kx0, kx1, 3, wl, parser))
        keys_c = (_ocr_key_strip(clean, kx0, kx1, 2, wl, parser)
                  + _ocr_key_strip(clean, kx0, kx1, 3, wl, parser))

        for key, joined, y0, y1, _items in data_bands:
            jflag = '除外' in joined or '樹脂' in joined
            # 品番の多数決: 本文の読み1票 + 品番列の読み(最大4票)
            votes = Counter([key])
            for cy, k in keys_g + keys_c:
                if y0 <= cy <= y1:
                    votes[k] += 1
            top, n = votes.most_common(1)[0]
            if votes[key] == n:                 # 同数なら本文の読みを優先
                top = key
            kconf = '◎' if n >= 3 else ('○' if n == 2 else '△')
            key = top
            price, conf, cell = None, '', ''
            if not jflag:
                price, conf = _read_price(y0, y1, joined)
                cell = _crop_b64(gac, x0, cx1, y0, y1)
            _add(key, price, ('除' if jflag else conf), '除外' if jflag else '', cell,
                 '' if jflag else kconf)

        # 本文OCRが行ごと見落とした品番を、品番列の読みから拾い直す
        # (加工なし/あり両方の読みで同じ品番・同じ高さに出た時だけ = 保守的)
        row_hs = [y1 - y0 for _, _, y0, y1, _i in data_bands]
        row_h = int(np.median(row_hs)) if row_hs else 40
        def _covered(cy):
            return any(by0 - 4 <= cy <= by1 + 4 for _, _, by0, by1, _i in data_bands)
        pend = {}
        for src, hits in (('g', keys_g), ('c', keys_c)):
            for cy, k in hits:
                if not _covered(cy):
                    pend.setdefault(k, []).append((src, cy))
        for k, hs in pend.items():
            srcs = {s for s, _ in hs}
            cys = [cy for _, cy in hs]
            if len(hs) >= 2 and {'g', 'c'} <= srcs and max(cys) - min(cys) <= row_h:
                cy = sum(cys) / len(cys)
                ry0, ry1 = int(cy - row_h / 2), int(cy + row_h / 2)
                price, conf = _read_price(ry0, ry1, '')
                cell = _crop_b64(gac, x0, cx1, ry0, ry1)
                _add(k, price, conf, '', cell, '○')

    _fix_prefix_outliers(rows, order)      # 品番の自動照合・補正
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
