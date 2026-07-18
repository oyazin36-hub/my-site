// ============================================================
// 帳票定義: 購入依頼表
// 帳票を追加するときはこのファイルをコピーして新しい帳票を作る
// ============================================================
const FORM_PURCHASE = {
  id:   'purchase',
  name: '購入依頼表',
  icon: '📋',
  desc: '備品・消耗品の購入申請',
  sheetName: '購入依頼',

  // スプレッドシートの列定義
  columns: [
    'id', '申請日', '申請者名', '先行発注済',
    // 明細(最大10行分)
    ...[...Array(10)].flatMap((_, i) => [
      `品名${i+1}`, `数量${i+1}`, `単位${i+1}`,
      `単価${i+1}`, `希望納期${i+1}`, `科目番号${i+1}`, `購入理由${i+1}`
    ]),
    '進捗', '総務承認日', '課長承認日', '副社長承認日', '社長承認日', '差戻しコメント',
  ],

  // フォームのレンダリング関数
  render(container) {
    const employees = CONFIG.EMPLOYEES.map(e => `<option value="${e}">${e}</option>`).join('');
    // 品名の入力候補(履歴から)
    const candidates = (typeof getHinmeiCandidates === 'function' ? getHinmeiCandidates() : []);
    const datalist = candidates.map(c => `<option value="${escAttr(c)}"></option>`).join('');

    container.innerHTML = `
      <!-- 品名の入力候補リスト(全明細行で共有) -->
      <datalist id="hinmeiList">${datalist}</datalist>

      <!-- 下書き復元バナー(必要時に表示) -->
      <div id="draftBanner" class="draft-banner hidden">
        <span>前回入力途中の下書きを復元しました。</span>
        <button onclick="discardDraft()">破棄して新規</button>
      </div>

      <!-- 先行発注済トグル -->
      <div class="toggle-row">
        <span class="toggle-label">先行発注済(レ点)</span>
        <label class="toggle-switch">
          <input type="checkbox" id="f_preorder">
          <span class="toggle-slider"></span>
        </label>
      </div>

      <!-- 基本情報 -->
      <div class="form-section">
        <div class="form-section-title">基本情報</div>
        <div class="field">
          <label>申請日</label>
          <input type="date" id="f_date" value="${todayISO()}">
        </div>
        <div class="field" id="field_employee">
          <label>申請者名 <span class="req">*</span></label>
          <select id="f_employee">
            <option value="">選択してください</option>
            ${employees}
          </select>
        </div>
      </div>

      <!-- 明細 -->
      <div id="purchaseRows"></div>
      <button class="btn-add-row" onclick="FORM_PURCHASE.addRow()">＋ 明細行を追加</button>
    `;

    // 最初の1行を追加
    this.addRow();
  },

  addRow(values) {
    const container = document.getElementById('purchaseRows');
    const idx = container.children.length + 1;
    const div = document.createElement('div');
    div.className = 'detail-card';
    div.dataset.rowIdx = idx;
    div.innerHTML = `
      <div class="detail-card-header">
        <span>明細 ${idx}</span>
        ${idx > 1 ? `<button class="btn-remove-row" onclick="FORM_PURCHASE.removeRow(this)">削除</button>` : ''}
      </div>
      <div class="detail-card-body">
        <div class="field">
          <label>メーカー・名称・型式(入り数) <span class="req">*</span></label>
          <input type="text" name="品名" list="hinmeiList" autocomplete="off"
                 placeholder="例:栄工舎 タップリムーバー TR-P5">
        </div>
        <div class="field-grid-2">
          <div class="field">
            <label>数量</label>
            <input type="number" name="数量" min="0" placeholder="0">
          </div>
          <div class="field">
            <label>単位</label>
            <select name="単位">
              <option value="">選択</option>
              <option>本</option><option>個</option><option>箱</option>
              <option>袋</option><option>缶</option><option>セット</option>
              <option>枚</option><option>冊</option><option>足</option>
              <option>kg</option><option>L</option><option>m</option>
              <option>その他</option>
            </select>
          </div>
        </div>
        <div class="field-grid-2">
          <div class="field">
            <label>単価(円)</label>
            <div class="price-row">
              <input type="number" name="単価" min="0" placeholder="0">
              <button type="button" class="btn-unknown" onclick="toggleUnknown(this)">不明</button>
            </div>
          </div>
          <div class="field">
            <label>希望納期</label>
            <input type="date" name="希望納期">
          </div>
        </div>
        <div class="field">
          <label>科目番号</label>
          <select name="科目番号">
            <option value="">わからなければ空欄</option>
            <option value="①">①工場消耗品</option>
            <option value="②">②工場外消耗品</option>
            <option value="③">③修繕用品</option>
            <option value="④">④事務用品</option>
            <option value="⑤">⑤備品</option>
            <option value="⑥">⑥その他</option>
          </select>
        </div>
        <div class="field">
          <label>購入理由</label>
          <textarea name="購入理由" placeholder="例:在庫ゼロになった為"></textarea>
        </div>
      </div>
    `;
    container.appendChild(div);

    // 値の復元(下書き用)
    if (values) {
      div.querySelector('[name="品名"]').value    = values.品名 || '';
      div.querySelector('[name="数量"]').value    = values.数量 || '';
      div.querySelector('[name="単位"]').value    = values.単位 || '';
      div.querySelector('[name="希望納期"]').value = values.希望納期 || '';
      div.querySelector('[name="科目番号"]').value = values.科目番号 || '';
      div.querySelector('[name="購入理由"]').value = values.購入理由 || '';
      const priceInput = div.querySelector('[name="単価"]');
      if (values.単価 === '不明') {
        const btn = div.querySelector('.btn-unknown');
        btn.classList.add('active');
        btn.textContent = '不明 ✓';
        priceInput.disabled = true;
      } else {
        priceInput.value = values.単価 || '';
      }
    }
    return div;
  },

  removeRow(btn) {
    const card = btn.closest('.detail-card');
    card.remove();
    // 行番号を振り直す
    document.querySelectorAll('.detail-card').forEach((c, i) => {
      c.querySelector('.detail-card-header span').textContent = `明細 ${i + 1}`;
    });
    if (typeof saveDraft === 'function') saveDraft();
  },

  // 検証なしで現在の入力値をそのまま取得(下書き保存用)
  snapshot() {
    const val = (row, name) => { const el = row.querySelector(`[name="${name}"]`); return el ? el.value : ''; };
    const rows = [...document.querySelectorAll('.detail-card')].map(row => {
      const unknown = row.querySelector('.btn-unknown')?.classList.contains('active');
      return {
        品名: val(row, '品名'), 数量: val(row, '数量'), 単位: val(row, '単位'),
        単価: unknown ? '不明' : val(row, '単価'),
        希望納期: val(row, '希望納期'), 科目番号: val(row, '科目番号'), 購入理由: val(row, '購入理由'),
      };
    });
    return {
      preorder: document.getElementById('f_preorder')?.checked || false,
      date:     document.getElementById('f_date')?.value || '',
      employee: document.getElementById('f_employee')?.value || '',
      rows,
    };
  },

  // 下書きを画面に復元
  restore(snap) {
    if (!snap) return;
    const pre = document.getElementById('f_preorder');
    const dt  = document.getElementById('f_date');
    const emp = document.getElementById('f_employee');
    if (pre) pre.checked = !!snap.preorder;
    if (dt && snap.date) dt.value = snap.date;
    if (emp) emp.value = snap.employee || '';
    const container = document.getElementById('purchaseRows');
    container.innerHTML = '';
    const rows = (snap.rows && snap.rows.length) ? snap.rows : [null];
    rows.forEach(r => this.addRow(r));
  },

  // フォームの値を収集(親切な必須チェック付き)。エラー時は null
  collect() {
    clearAllErrors();
    const invalids = [];

    const empSel = document.getElementById('f_employee');
    if (!empSel.value) { markInvalid(empSel, '申請者名を選択してください'); invalids.push(empSel); }

    const rows = document.querySelectorAll('.detail-card');
    const details = [];
    rows.forEach((row) => {
      const hinInput = row.querySelector('[name="品名"]');
      const hinmei = hinInput.value.trim();
      if (!hinmei) { markInvalid(hinInput, '品名を入力してください'); invalids.push(hinInput); }
      const priceInput = row.querySelector('[name="単価"]');
      const unknownBtn = row.querySelector('.btn-unknown');
      const isUnknown = unknownBtn && unknownBtn.classList.contains('active');
      details.push({
        品名:    hinmei,
        数量:    row.querySelector('[name="数量"]').value,
        単位:    row.querySelector('[name="単位"]').value,
        単価:    isUnknown ? '不明' : priceInput.value,
        希望納期: row.querySelector('[name="希望納期"]').value,
        科目番号: row.querySelector('[name="科目番号"]').value,
        購入理由: row.querySelector('[name="購入理由"]').value.trim(),
      });
    });

    if (invalids.length) {
      invalids[0].scrollIntoView({ behavior: 'smooth', block: 'center' });
      try { invalids[0].focus({ preventScroll: true }); } catch(_) {}
      return null;
    }

    return {
      formId:   'purchase',
      申請日:   document.getElementById('f_date').value,
      申請者名: empSel.value,
      先行発注済: document.getElementById('f_preorder').checked ? 'あり' : 'なし',
      明細:     details,
    };
  },

  // 履歴に追加したい品名の配列を返す
  historyTerms(data) {
    return (data.明細 || []).map(d => d.品名).filter(Boolean);
  },

  // スプレッドシートに送る行データへ変換
  toRow(data) {
    const id = Date.now().toString(36).toUpperCase();
    const row = [id, data.申請日, data.申請者名, data.先行発注済];
    for (let i = 0; i < 10; i++) {
      const d = data.明細[i] || {};
      row.push(d.品名||'', d.数量||'', d.単位||'', d.単価||'', d.希望納期||'', d.科目番号||'', d.購入理由||'');
    }
    row.push('申請中', '', '', '', '', '');   // 進捗, 各承認日, 差戻しコメント
    return { id, row, sheetName: this.sheetName };
  },
};

// ===== ユーティリティ =====
function todayISO() {
  return new Date().toISOString().slice(0, 10);
}
function toggleUnknown(btn) {
  const input = btn.previousElementSibling;
  btn.classList.toggle('active');
  if (btn.classList.contains('active')) {
    input.value = '';
    input.disabled = true;
    btn.textContent = '不明 ✓';
  } else {
    input.disabled = false;
    btn.textContent = '不明';
  }
  if (typeof saveDraft === 'function') saveDraft();
}
function confirmRow(key, val) {
  return `<div class="confirm-row"><span class="confirm-key">${key}</span><span class="confirm-val">${val}</span></div>`;
}
function escAttr(s) {
  return String(s || '').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// 登録済みフォーム一覧(帳票を追加するたびここに足す)
const REGISTERED_FORMS = [FORM_PURCHASE];

// インラインの onclick 属性から参照できるよう、グローバル(window)に公開する。
// ※ const で宣言したオブジェクトは window のプロパティにならないため明示的に代入する。
if (typeof window !== 'undefined') {
  window.FORM_PURCHASE = FORM_PURCHASE;
  window.REGISTERED_FORMS = REGISTERED_FORMS;
}
