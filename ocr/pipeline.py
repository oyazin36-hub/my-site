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
PRICE_MIN, PRICE_MAX = 300, 999999

# 品番: 任意の接頭辞(WIDRY07-等) + 3桁 + M + 3桁
# 品番の形式 (2種類に対応)
#  ① M形式:   WIDRY07-107-M001 / 107-M001  (末尾が M+3桁)
#  ② 図番形式: 26041-20-001                (5桁-2桁-3桁, Mなし)
_PN_M = re.compile(r'(?:[A-Za-z]{2,6}\d{0,2}[-_ ]?)?([0-9oOlIzZeg]{3})[-_ ]?M[-_ ]?([0-9oOlIzZeBsSgt]{3})(?![A-Za-z0-9])')
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
    # 罫線とみなす線の最短長。数字の縦棒(高さ≒文字サイズ)より十分長くしないと
    # 「1」や「4」の縦棒が罫線として消され、18,800→8,800 のような誤読になる
    line_len = max(60, min(g.shape[0], g.shape[1]) // 25)
    hor = cv2.morphologyEx(inv, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (line_len, 1)))
    ver = cv2.morphologyEx(inv, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, line_len)))
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
def _parse_prices(text, unit=PRICE_UNIT):
    out = []
    for m in _PRICE.finditer(text):
        v = int(m.group().replace(',', '').replace('.', ''))
        if PRICE_MIN <= v <= PRICE_MAX and v % unit == 0:
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
                          '-c', 'tessedit_char_whitelist=0123456789,.¥', '--psm', '6', 'tsv'],
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
        xw = x0 + int(c[6]) / scale
        for v in _parse_prices(text, 1):
            results.append((cy, v, xw))
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


def _row_value(strip_gac, strip_clean, y0, y1, row_text='', ban=''):
    """1行の単価を、加工なし/あり(各2スケール)の列OCR結果から多数決で決める。
    ◎=両画像が一致 or 合計3票以上 / ○=2票 / △=1票(怪しい)。
    ヒットは (cy, 値, x)。10円きざみの候補を優先し、無い時だけ1円単位を
    採用(信頼度1段下げ)。同数の時は左側(単価列は金額列の左)を選ぶ。
    ban: その行の品番の数字列。品番の先頭数字を価格と誤認した票を弾く。"""
    def _ok(v):
        s = str(v)
        return not (ban and len(s) >= 4 and ban.startswith(s))
    gac = [h for h in strip_gac if y0 <= h[0] <= y1 and _ok(h[1])]
    cln = [h for h in strip_clean if y0 <= h[0] <= y1 and _ok(h[1])]
    txt = [(y0, v, 10 ** 9) for v in _parse_prices(row_text, 1) if _ok(v)]
    allh = gac + cln + txt
    if not allh:
        return None, ''
    votes = Counter(h[1] for h in allh)
    gset = {h[1] for h in gac}
    cset = {h[1] for h in cln}

    def _minx(v):
        return min(h[2] for h in allh if h[1] == v)

    tset = {h[1] for h in txt}

    def _lead_d1(a, b):
        # 先頭の桁だけ違う値か(例: 18000と28000)。金額の桁が大きく狂う危険な誤読ペア
        s, t = str(a), str(b)
        return len(s) == len(t) and s[0] != t[0] and s[1:] == t[1:]

    def _pick(cands):
        mx = max(votes[v] for v in cands)
        best = [v for v in cands if votes[v] == mx]
        if len(best) > 1:                      # 同数なら左の列(単価)を優先
            best.sort(key=_minx)
        v = best[0]
        # vが「他候補の整数倍(2〜9倍)」なら、それは金額(=単価×数量)の可能性が高い。
        # 票が拮抗(差1以内)していれば左にある方(単価)へ切り替える。
        for w in cands:
            if (w != v and votes[w] >= votes[v] - 1 and _minx(w) < _minx(v)
                    and w > 0 and v % w == 0 and 2 <= v // w <= 9):
                v = w
                break
        n = votes[v]
        cross = v in gset and v in cset
        conf = '◎' if (cross or n >= 3) else ('○' if n == 2 else '△')
        # 値は多数決のまま変えない。ただし採用値が両画像一致(cross)でなく、
        # 「先頭の桁だけ違う値」を別の読み元(もう一方の画像や行テキスト)が
        # 出している時だけは、1↔2癒着誤読の疑いがあるので要確認(△)にする。
        if not cross:
            def _other_src(w):
                return ((w in gset and v not in gset) or (w in cset and v not in cset)
                        or (w in tset and v not in tset))
            if any(w != v and _lead_d1(w, v) and _other_src(w) for w in cands):
                conf = '△'
        return v, conf

    tens = [v for v in votes if v % PRICE_UNIT == 0]
    if tens:
        return _pick(tens)
    value, conf = _pick(list(votes))           # 1円単位しか無い見積(例: ¥96,016)
    return value, {'◎': '○', '○': '△'}.get(conf, conf)


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
_CAND_HYPHEN = re.compile(r'[A-Za-z0-9]{2,8}(?:-[A-Za-z0-9]{1,10}){1,3}')
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


_CONTACT = re.compile(r'TEL|FAX|ＴＥＬ|ＦＡＸ|電話|携帯|〒', re.I)


def _candidates(text, allow_space, min_digits=4):
    pats = [_CAND_HYPHEN] + ([_CAND_SPACE] if allow_space else [])
    contact = bool(_CONTACT.search(text))
    found = []
    for p in pats:
        for m in p.finditer(text):
            t = m.group()
            if not (sum(c.isdigit() for c in t) >= min_digits and 5 <= len(t) <= 24):
                continue
            # 電話/FAX/郵便番号の行にある数字だけのトークンは品番候補にしない
            if contact and not any(c.isalpha() for c in t):
                continue
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


def _anchored_key(text):
    """型式アンカー方式: 形の学習ができない見積(型番が行ごとに違う形)向け。
    『英字を含む・数字2つ以上・ハイフン入り』のトークンを品番として拾う。
    例: HG-SR152B / AF3SZ45-60L2000F33。電話番号や日付(数字のみ)は対象外。"""
    for t in _candidates(text, False, min_digits=2):
        k = _clean_key(t)
        if ('-' in k and sum(c.isdigit() for c in k) >= 2
                and any(c.isalpha() for c in k) and 5 <= len(k) <= 24):
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


def _auto_tanka_column(columns, imgs, data_bands, W, key_x=None):
    """検出した列の中から「単価列」を自動で選ぶ。
    価格が入っている列が2つ以上 → 右から2番目が単価(一番右は金額)。
    1つだけ(単価列がほぼ空欄で金額列だけの見積) → その左隣を単価、
    その列を金額としてフォールバック用に返す。
    imgs: 判定に使う画像のリスト(加工なし/あり両方を渡すと薄いFAXでも安定)。
    key_x=(kx0,kx1): 品番列の範囲。品番の数字を価格と誤認しないよう候補から除外。
    返り値: (単価gap or None, フォールバック用の金額gap or None)"""
    if not isinstance(imgs, (list, tuple)):
        imgs = [imgs]
    gaps = _columns_to_gaps(columns)
    if not gaps:
        return None, None
    bands = data_bands[:20]
    hits = [0] * len(gaps)
    for gi, (a, b) in enumerate(gaps):
        x0, x1 = int(W * a), int(W * b)
        if x1 - x0 < W * 0.03:            # 細すぎる列は対象外
            continue
        if key_x is not None:             # 品番列と3割以上重なる列は対象外
            ov = min(x1, key_x[1]) - max(x0, key_x[0])
            if ov > (x1 - x0) * 0.3:
                continue
        best = 0
        for img in imgs:                  # 画像ごとにヒット数を数え、良い方を採用
            strip = _ocr_column_strip(img, x0, x1)
            h = 0
            for band in bands:
                y0, y1 = band[2], band[3]
                if any(y0 <= hit[0] <= y1 for hit in strip):
                    h += 1
            best = max(best, h)
        hits[gi] = best
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
    # joinedは行の全単語を無空白で連結したもの。品番の直後に数量などの数字が
    # 癒着して既知形式の判定が落ちることがあるので、左半分(空白区切り)でも試す
    def _known_key(left, joined):
        return normalize_key(joined) or normalize_key(left or '')
    known_count = 0
    for a in arts:
        src = a['lines'] if a['kind'] == 'text' else a['raw']
        known_count += sum(1 for x in src if _known_key(x.get('left'), x['joined']))
    generic = None                              # (shape, allow_space)
    anchored = False                            # 型式アンカー方式(形がバラバラな型番向け)
    if known_count < 3:
        corpus = []
        for a in arts:
            src = a['lines'] if a['kind'] == 'text' else a['raw']
            corpus += [x['left'] for x in src]
        generic = _learn_shape(corpus)
        if generic is None:
            anchored = True

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
            # 学習した形に合わなくても、既知形式ならば拾う(検出が減る事故の保険)
            return _known_key(left, joined)
        if anchored:
            k = _anchored_key(left)
            if k:
                return k
        return _known_key(left, joined)

    # ---- 第3段a: 各ページの品番行と列選択を決める ----
    for a in arts:
        if a['kind'] == 'text':
            a['rows2'] = []
            for ln in a['lines']:
                key = _key_of(ln['left'], ln['joined'])
                if key:
                    a['rows2'].append((key, ln))
            continue
        W, raw_bands = a['W'], a['raw']
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
            kx = (max(0, min(kxs) - 12), min(W, max(kxs) + 12))
        else:
            kx = (int(W * 0.02), int(W * 0.30))
        col = _pick_tanka_column(a['columns'], tanka_col_index)
        kcol = None                             # 単価が空欄の見積用: 金額列フォールバック
        if col is None:
            col, kcol = _auto_tanka_column(a['columns'], [a['gac'], a['clean']],
                                           data_bands, W, kx)
        a['bands2'], a['kx'], a['col'], a['kcol'] = data_bands, kx, col, kcol

    # 列のコンセンサス: 同じ書類はレイアウトが同じなので、
    # 列選択に失敗したページには成功したページの選択(最頻値)を使う
    picked = [(a['col'], a['kcol']) for a in arts
              if a['kind'] == 'ocr' and a['col'] is not None]
    if picked:
        rounded = Counter((tuple(round(v, 3) for v in c),
                           tuple(round(v, 3) for v in k) if k else None)
                          for c, k in picked)
        (bc, bk), _n = rounded.most_common(1)[0]
        for a in arts:
            if a['kind'] == 'ocr' and a['col'] is None:
                a['col'] = list(bc)
                a['kcol'] = list(bk) if bk else None

    # ---- 第3段b: ページごとに読み取り ----
    for a in arts:
        if a['kind'] == 'text':                 # 文字データから直接(確実)
            for key, ln in a['rows2']:
                jflag = '除外' in ln['joined'] or '樹脂' in ln['joined']
                price = None
                if not jflag and ln['nums']:
                    nums = ln['nums']
                    price = nums[-2][1] if len(nums) >= 2 else nums[-1][1]
                if anchored and price is None and not jflag:
                    continue    # 型式アンカー方式では単価の無い行は出さない
                _add(key, price, ('除' if jflag else ('文' if price is not None else '')),
                     '除外' if jflag else '', '')
            continue

        # --- スキャン画像ページ ---
        g, clean, gac = a['g'], a['clean'], a['gac']
        W, data_bands = a['W'], a['bands2']
        (kx0, kx1), col, kcol = a['kx'], a['col'], a['kcol']
        if col is None and kcol is not None:    # 金額列しか無い場合はそれを単価扱い
            col, kcol = kcol, None
        if col is not None:
            x0, x1 = int(W * col[0]), int(W * col[1])
        else:
            x0, x1 = int(W * 0.40), int(W * 0.90)

        strip_gac = _ocr_column_strip(gac, x0, x1, 2) + _ocr_column_strip(gac, x0, x1, 3)
        strip_clean = _ocr_column_strip(clean, x0, x1, 2) + _ocr_column_strip(clean, x0, x1, 3)
        # 品番・品名領域(kx1より左)の数字は型番の断片なので単価票に使わない
        strip_gac = [h for h in strip_gac if h[2] > kx1 + 6]
        strip_clean = [h for h in strip_clean if h[2] > kx1 + 6]
        kstrip_gac = kstrip_clean = []
        cx1 = x1
        if kcol is not None:
            kxx0, kxx1 = int(W * kcol[0]), int(W * kcol[1])
            kstrip_gac = _ocr_column_strip(gac, kxx0, kxx1, 2) + _ocr_column_strip(gac, kxx0, kxx1, 3)
            kstrip_clean = _ocr_column_strip(clean, kxx0, kxx1, 2) + _ocr_column_strip(clean, kxx0, kxx1, 3)
            cx1 = kxx1                          # 確認用画像は金額列まで含めて切り出す

        def _read_price(y0, y1, row_text, ban=''):
            # 金額フォールバックがある時は、行テキストの票(数量が癒着しやすい)は使わず
            # 列の読みだけで判定する
            price, conf = _row_value(strip_gac, strip_clean, y0, y1,
                                     '' if kcol is not None else row_text, ban)
            if price is None and kcol is not None:
                # 単価欄が空欄 → 金額欄を読む(数量1なら金額=単価)。信頼度は1段下げる
                price, conf = _row_value(kstrip_gac, kstrip_clean, y0, y1, '', ban)
                conf = {'◎': '○', '○': '△'}.get(conf, conf)
            return price, conf

        # 品番列も単価と同じく、加工なし/あり×2スケールで読んで多数決に使う
        if generic:
            shape, asp = generic
            letters = ''.join(sorted({c for k, *_ in data_bands for c in k if c.isalpha()}))
            wl = '0123456789-' + letters
            parser = lambda t: _generic_key(t, shape, asp)   # noqa: E731
        elif anchored:
            letters = ''.join(sorted({c for k, *_ in data_bands for c in k if c.isalpha()}))
            wl = '0123456789-' + letters
            parser = _anchored_key
        else:
            wl, parser = '0123456789-M', None
        keys_g = (_ocr_key_strip(gac, kx0, kx1, 2, wl, parser)
                  + _ocr_key_strip(gac, kx0, kx1, 3, wl, parser))
        keys_c = (_ocr_key_strip(clean, kx0, kx1, 2, wl, parser)
                  + _ocr_key_strip(clean, kx0, kx1, 3, wl, parser))

        # 列読みの各ヒットは「最も近い行」1つだけに割り当てる。
        # (行の縦範囲が広がった時に隣の行の値を取り込む誤りを防ぐ)
        row_hs = [y1 - y0 for _, _, y0, y1, _i in data_bands]
        row_h = int(np.median(row_hs)) if row_hs else 40

        # 同じセルに品番が2行書かれ、OCRの揺れで別品番に見える行を統合する。
        # 例: 「KC-KR43B」「KG-KR43B」(C↔G) / 「…BG1H」「…8GIH」。
        # 紛らわしい文字(1≡I, B≡8, C≡G, O≡0, 5≡S, 2≡Z)を同一視して比較する。
        # 数字同士の違い(003 vs 004 等=本当に別の品番)は同一視しないので統合されない。
        _CONF_NORM = str.maketrans({'I': '1', 'l': '1', 'O': '0', 'Q': '0',
                                    'B': '8', 'S': '5', 'Z': '2', 'C': 'G'})
        def _same_cell_variant(k1, k2):
            n1, n2 = k1.translate(_CONF_NORM), k2.translate(_CONF_NORM)
            if abs(len(n1) - len(n2)) == 1:            # 末尾1文字の有無
                return n1.startswith(n2) or n2.startswith(n1)
            return n1 == n2
        merged = []
        for b in data_bands:
            if merged:
                p = merged[-1]
                if ((b[2] + b[3]) / 2 - (p[2] + p[3]) / 2 <= row_h * 2.2
                        and _same_cell_variant(p[0], b[0])):
                    merged[-1] = (p[0], p[1] + b[1], p[2], max(p[3], b[3]), p[4] + b[4])
                    continue
            merged.append(b)
        data_bands = merged
        centers = [((y0 + y1) / 2) for _, _, y0, y1, _i in data_bands]
        def _assign(hits):
            per = [[] for _ in data_bands]
            for h in hits:
                cy = h[0]
                best, bd = None, 1e18
                for idx, c in enumerate(centers):
                    d = abs(cy - c)
                    if d < bd:
                        bd, best = d, idx
                if best is not None and bd <= row_h * 0.7:
                    per[best].append((centers[best],) + tuple(h[1:]))
                # どの行にも近くないヒットは行帰属なし(拾い直しの候補になる)
            return per
        per_sg = _assign(strip_gac)
        per_sc = _assign(strip_clean)
        per_ksg = _assign(kstrip_gac)
        per_ksc = _assign(kstrip_clean)
        per_kg = _assign(keys_g)
        per_kc = _assign(keys_c)

        for bi, (key, joined, y0, y1, _items) in enumerate(data_bands):
            jflag = '除外' in joined or '樹脂' in joined
            # 品番の多数決: 本文の読み1票 + 品番列の読み(最大4票)
            votes = Counter([key])
            for _cy, k in per_kg[bi] + per_kc[bi]:
                votes[k] += 1
            top, n = votes.most_common(1)[0]
            if votes[key] == n:                 # 同数なら本文の読みを優先
                top = key
            kconf = '◎' if n >= 3 else ('○' if n == 2 else '△')
            key = top
            price, conf, cell = None, '', ''
            cell_y = (y0, y1)
            if not jflag:
                ban = re.sub(r'\D', '', key)
                cy0, cy1 = centers[bi] - 1, centers[bi] + 1
                row_txt = '' if (kcol is not None or anchored) else joined
                price, conf = _row_value(per_sg[bi], per_sc[bi], cy0, cy1, row_txt, ban)
                if price is None and kcol is not None:
                    price, conf = _row_value(per_ksg[bi], per_ksc[bi], cy0, cy1, '', ban)
                    conf = {'◎': '○', '○': '△'}.get(conf, conf)
                if price is None:
                    # 自分の行に単価が無い → 品番の下の行を探す
                    # (型式と単価が別の行にあるブロック様式の見積に対応)
                    nxt = min((c for c in centers if c > centers[bi] + row_h * 0.5),
                              default=None)
                    lo = centers[bi] + row_h * 0.5
                    hi = centers[bi] + row_h * 3.0
                    if nxt is not None:
                        hi = min(hi, nxt - row_h * 0.4)
                    if hi > lo:
                        price, conf = _row_value(strip_gac, strip_clean, lo, hi, '', ban)
                        if price is None and kcol is not None:
                            price, conf = _row_value(kstrip_gac, kstrip_clean, lo, hi, '', ban)
                        conf = {'◎': '○'}.get(conf, conf)   # 行の対応が推定なので上限○
                        if price is not None:
                            cell_y = (y0, int(hi))
                cell = _crop_b64(gac, x0, cx1, cell_y[0], cell_y[1])
            if anchored and price is None and not jflag:
                continue    # 型式アンカー方式では単価の無い行は表に出さない(見積番号等の誤検出防止)
            _add(key, price, ('除' if jflag else conf), '除外' if jflag else '', cell,
                 '' if jflag else kconf)

        # 本文OCRが行ごと見落とした品番を、品番列の読みから拾い直す
        # (加工なし/あり両方の読みで同じ品番・同じ高さに出た時だけ = 保守的)
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
                price, conf = _read_price(ry0, ry1, '', re.sub(r'\D', '', k))
                if anchored and price is None:
                    continue
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
