// ============================================================
// アプリのメインロジック
// ============================================================

// ===== 状態 =====
let currentTab   = 'month';
let currentMonth = new Date();
let allRequests  = [];    // スプレッドシートから取得した全データ
let currentForm  = null;  // 現在入力中の帳票定義
let formData     = null;  // 確認画面に渡すデータ

// 承認ステップ ↔ 承認日カラム の対応
const STEP_DATE_KEYS = {
  '総務': '総務承認日', '課長': '課長承認日', '副社長': '副社長承認日', '社長': '社長承認日',
};

// localStorage キー
const LS_DRAFT   = (formId) => `draft_${formId}`;
const LS_HISTORY = 'history_hinmei';

// ===== ページ切り替え =====
function showPage(pageId) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.getElementById(pageId).classList.add('active');

  const btnBack = document.getElementById('btnBack');
  const btnNew  = document.getElementById('btnNew');
  const title   = document.getElementById('pageTitle');

  const pageConfig = {
    pageDashboard: { back: false, new: true,  title: '社内帳票管理' },
    pageFormList:  { back: true,  new: false, title: '帳票を選択' },
    pageInput:     { back: true,  new: false, title: currentForm ? currentForm.name + ' 新規作成' : '入力' },
    pageConfirm:   { back: true,  new: false, title: '入力内容の確認' },
    pageComplete:  { back: false, new: false, title: '送信完了' },
    pageDetail:    { back: true,  new: false, title: '依頼の詳細' },
  };
  const cfg = pageConfig[pageId] || {};
  btnBack.classList.toggle('hidden', !cfg.back);
  btnNew.classList.toggle('hidden',  !cfg.new);
  if (cfg.title) title.textContent = cfg.title;

  if (pageId === 'pageDashboard') window.scrollTo(0, 0);
}

function goBack() {
  const active = document.querySelector('.page.active')?.id;
  const backMap = {
    pageFormList: 'pageDashboard',
    pageInput:    'pageFormList',
    pageConfirm:  'pageInput',
    pageDetail:   'pageDashboard',
  };
  const dest = backMap[active];
  if (dest) showPage(dest);
}

// ===== 初期化 =====
document.addEventListener('DOMContentLoaded', () => {
  renderFormList();
  loadDashboard();
  showPage('pageDashboard');
  registerServiceWorker();
});

// ===== 月切り替え =====
function changeMonth(delta) {
  currentMonth = new Date(currentMonth.getFullYear(), currentMonth.getMonth() + delta, 1);
  renderDashboard();
}

// ===== タブ切り替え =====
function switchTab(el, tab) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  el.classList.add('active');
  currentTab = tab;
  document.getElementById('monthSelector').style.display = tab === 'month' ? '' : 'none';
  renderDashboard();
}

// ===== ダッシュボード =====
function loadDashboard() {
  if (!CONFIG.GAS_URL) {
    useDemoData();
    return;
  }
  fetch(`${CONFIG.GAS_URL}?action=list`)
    .then(r => r.json())
    .then(data => { allRequests = data; renderDashboard(); })
    .catch(() => { useDemoData(); });
}

// デモ用: サンプルデータを表示し、データのある月を初期表示にする
function useDemoData() {
  allRequests = getDummyData();
  if (allRequests.length && allRequests[0].申請日) {
    currentMonth = new Date(allRequests[0].申請日);
  }
  renderDashboard();
}

function renderDashboard() {
  const label = document.getElementById('currentMonthLabel');
  label.textContent = `${currentMonth.getFullYear()}年 ${currentMonth.getMonth()+1}月`;

  let filtered = allRequests;
  if (currentTab === 'month') {
    filtered = allRequests.filter(r => {
      if (!r.申請日) return false;
      const d = new Date(r.申請日);
      return d.getFullYear() === currentMonth.getFullYear() &&
             d.getMonth()    === currentMonth.getMonth();
    });
  }

  const total   = filtered.length;
  const pending = filtered.filter(r => r.進捗 !== '完了' && r.進捗 !== '差戻し').length;
  const done    = filtered.filter(r => r.進捗 === '完了').length;
  document.getElementById('totalCount').textContent   = total   + ' 件';
  document.getElementById('pendingCount').textContent = pending + ' 件';
  document.getElementById('doneCount').textContent    = done    + ' 件';

  const list = document.getElementById('requestList');
  if (!filtered.length) {
    list.innerHTML = '<div class="empty">この期間の依頼はありません</div>';
    return;
  }

  let grouped = filtered;
  if (currentTab === 'employee') {
    grouped = sortBy(filtered, '申請者名');
  } else if (currentTab === 'category') {
    grouped = sortBy(filtered, '科目番号1');
  }
  list.innerHTML = grouped.map(r => renderCard(r)).join('');
}

function stepperHtml(r, small) {
  const steps     = CONFIG.APPROVAL_STEPS;
  const doneCount = steps.map(s => STEP_DATE_KEYS[s]).filter(k => r[k]).length;
  const rejected  = r.進捗 === '差戻し';
  return steps.map((s, i) => {
    let dotClass = i < doneCount ? 'done' : (i === doneCount && !rejected ? 'current' : '');
    const lineClass = i < doneCount - 1 ? 'done' : '';
    const line = i < steps.length - 1 ? `<div class="step-line ${lineClass}"></div>` : '';
    return `<div class="step-dot ${dotClass}">${s.slice(0, 1)}</div>${line}`;
  }).join('');
}

function renderCard(r) {
  const statusClass = r.進捗 === '完了' ? 'done' : r.進捗 === '差戻し' ? 'rejected' : 'pending';
  const badgeText   = r.進捗 || '申請中';
  const itemName = r.品名1 || r.件名 || '(品名なし)';
  const date = r.申請日 ? String(r.申請日).replace(/-/g, '/').slice(5) : '';

  return `
    <div class="request-card ${statusClass}" onclick="showDetail('${r.id}')">
      <div class="card-top">
        <div class="card-name">${esc(r.申請者名 || '—')}</div>
        <div class="card-date">${date}</div>
      </div>
      <div class="card-item">${esc(itemName)}${r.品名2 ? ' ほか' : ''}</div>
      <div class="card-bottom">
        <span class="badge ${statusClass}">${esc(badgeText)}</span>
        <div class="stepper">${stepperHtml(r)}</div>
      </div>
    </div>
  `;
}

// ===== 帳票選択 =====
function showFormList() {
  renderFormList();
  showPage('pageFormList');
}
function renderFormList() {
  const container = document.getElementById('formList');
  container.innerHTML = REGISTERED_FORMS.map(f => `
    <div class="form-item" onclick="startForm('${f.id}')">
      <div class="form-icon">${f.icon}</div>
      <div class="form-info">
        <div class="form-info-name">${esc(f.name)}</div>
        <div class="form-info-desc">${esc(f.desc)}</div>
      </div>
      <div class="form-arrow">›</div>
    </div>
  `).join('');
}

// ===== 入力フォーム =====
function startForm(formId) {
  currentForm = REGISTERED_FORMS.find(f => f.id === formId);
  if (!currentForm) return;
  document.getElementById('pageTitle').textContent = currentForm.name + ' 新規作成';

  const container = document.getElementById('formContainer');
  currentForm.render(container);

  // 下書きがあれば復元
  const saved = localStorage.getItem(LS_DRAFT(formId));
  if (saved) {
    try {
      currentForm.restore(JSON.parse(saved));
      const banner = document.getElementById('draftBanner');
      if (banner) banner.classList.remove('hidden');
    } catch(_) {}
  }

  // 入力のたびに下書きを自動保存
  container.addEventListener('input',  saveDraft);
  container.addEventListener('change', saveDraft);
  // 入力し始めたらエラー表示を消す
  container.addEventListener('input',  (e) => clearInvalid(e.target));

  showPage('pageInput');
}

// ===== 下書きの自動保存 =====
let draftTimer = null;
function saveDraft() {
  if (!currentForm || typeof currentForm.snapshot !== 'function') return;
  clearTimeout(draftTimer);
  draftTimer = setTimeout(() => {
    try {
      localStorage.setItem(LS_DRAFT(currentForm.id), JSON.stringify(currentForm.snapshot()));
    } catch(_) {}
  }, 400);
}
function clearDraft() {
  if (currentForm) localStorage.removeItem(LS_DRAFT(currentForm.id));
}
function discardDraft() {
  if (!currentForm) return;
  clearDraft();
  currentForm.render(document.getElementById('formContainer'));
}

// ===== 品名の入力候補(履歴 + 既存データ) =====
function getHinmeiCandidates() {
  const set = new Set();
  // localStorage の履歴
  try {
    (JSON.parse(localStorage.getItem(LS_HISTORY) || '[]')).forEach(x => x && set.add(x));
  } catch(_) {}
  // 既に登録済みのデータの品名も候補に
  allRequests.forEach(r => {
    for (let i = 1; i <= 10; i++) { if (r['品名'+i]) set.add(r['品名'+i]); }
  });
  return [...set].slice(0, 100);
}
function addToHistory(terms) {
  if (!terms || !terms.length) return;
  let hist = [];
  try { hist = JSON.parse(localStorage.getItem(LS_HISTORY) || '[]'); } catch(_) {}
  terms.forEach(t => {
    const i = hist.indexOf(t);
    if (i >= 0) hist.splice(i, 1);
    hist.unshift(t);
  });
  localStorage.setItem(LS_HISTORY, JSON.stringify(hist.slice(0, 100)));
}

// ===== 親切な必須チェック(インライン表示) =====
function markInvalid(el, msg) {
  const field = el.closest('.field') || el.parentElement;
  el.classList.add('invalid');
  field.classList.add('has-error');
  let m = field.querySelector('.field-error');
  if (!m) { m = document.createElement('div'); m.className = 'field-error'; field.appendChild(m); }
  m.textContent = msg;
}
function clearInvalid(el) {
  if (!el || !el.classList || !el.classList.contains('invalid')) return;
  el.classList.remove('invalid');
  const field = el.closest('.field');
  if (field) { field.classList.remove('has-error'); const m = field.querySelector('.field-error'); if (m) m.remove(); }
}
function clearAllErrors() {
  document.querySelectorAll('.invalid').forEach(el => el.classList.remove('invalid'));
  document.querySelectorAll('.has-error').forEach(f => f.classList.remove('has-error'));
  document.querySelectorAll('.field-error').forEach(m => m.remove());
}

// ===== 確認画面 =====
function showConfirm() {
  if (!currentForm) return;
  formData = currentForm.collect();
  if (!formData) return;   // エラーあり
  document.getElementById('confirmBox').innerHTML = buildConfirmHtml(formData);
  showPage('pageConfirm');
}

function buildConfirmHtml(data) {
  if (data.formId === 'purchase') {
    const detailHtml = data.明細.map((r, i) => `
      <div class="confirm-section">
        <div class="confirm-section-title">明細 ${i+1}</div>
        ${confirmRow('品名', esc(r.品名))}
        ${confirmRow('数量・単位', `${esc(r.数量) || '—'} ${esc(r.単位)}`)}
        ${confirmRow('単価', r.単価 === '不明' ? '不明' : (r.単価 ? `¥${Number(r.単価).toLocaleString()}` : '—'))}
        ${confirmRow('希望納期', esc(r.希望納期) || '未定')}
        ${confirmRow('科目番号', esc(r.科目番号) || '未選択')}
        ${confirmRow('購入理由', esc(r.購入理由) || '—')}
      </div>
    `).join('');
    return `
      <div class="confirm-section">
        <div class="confirm-section-title">基本情報</div>
        ${confirmRow('申請日', esc(data.申請日))}
        ${confirmRow('申請者名', esc(data.申請者名))}
        ${confirmRow('先行発注済', esc(data.先行発注済))}
      </div>
      ${detailHtml}
    `;
  }
  return '<p>確認データの表示に対応していない帳票です。</p>';
}

// ===== 送信 =====
function submitForm() {
  if (!formData || !currentForm) return;
  const payload = currentForm.toRow(formData);

  const finalize = (msg) => {
    // 品名を履歴に追加・下書きを消す
    if (currentForm.historyTerms) addToHistory(currentForm.historyTerms(formData));
    clearDraft();
    allRequests.unshift(simulateRecord(formData, payload.id));
    document.getElementById('completeMsg').textContent = msg;
    showPage('pageComplete');
  };

  if (!CONFIG.GAS_URL) {
    finalize('(デモ動作: GAS URLが未設定のため実際には保存されていません)');
    return;
  }

  const btn = document.querySelector('.btn-submit');
  btn.disabled = true;
  btn.textContent = '送信中...';

  fetch(CONFIG.GAS_URL, {
    method: 'POST',
    mode:   'no-cors',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action: 'submit', ...payload }),
  })
  .then(() => finalize('スプレッドシートに記録されました。承認フローが開始されます。'))
  .catch(() => {
    alert('送信に失敗しました。ネットワーク接続を確認して再度お試しください。');
    btn.disabled = false;
    btn.textContent = '送信する';
  });
}

// ===== 詳細画面 + 承認・差戻し =====
function showDetail(id) {
  const r = allRequests.find(x => x.id === id);
  if (!r) return;

  const steps     = CONFIG.APPROVAL_STEPS;
  const doneCount = steps.map(s => STEP_DATE_KEYS[s]).filter(k => r[k]).length;
  const rejected  = r.進捗 === '差戻し';
  const completed = r.進捗 === '完了';
  const currentStep = steps[doneCount];

  const stepHtml = steps.map((s, i) => {
    const dotClass  = i < doneCount ? 'done' : (i === doneCount && !rejected && !completed ? 'current' : '');
    const lineClass = i < doneCount - 1 ? 'done' : '';
    const line = i < steps.length - 1 ? `<div class="approval-step-line ${lineClass}"></div>` : '';
    const label = i < doneCount ? '承認済' : (i === doneCount && !rejected ? '待ち' : '—');
    return `
      <div class="approval-step">
        <div class="approval-step-dot ${dotClass}">${s}</div>
        <div class="approval-step-label">${label}</div>
      </div>${line}`;
  }).join('');

  const items = [1,2,3,4,5,6,7,8,9,10].map(i => r[`品名${i}`] ? `
    <div class="confirm-section">
      <div class="confirm-section-title">明細 ${i}</div>
      ${confirmRow('品名', esc(r[`品名${i}`]))}
      ${confirmRow('数量・単位', `${esc(r[`数量${i}`])||'—'} ${esc(r[`単位${i}`])||''}`)}
      ${confirmRow('単価', r[`単価${i}`] === '不明' ? '不明' : (r[`単価${i}`] ? `¥${Number(r[`単価${i}`]).toLocaleString()}` : '—'))}
      ${confirmRow('希望納期', esc(r[`希望納期${i}`]) || '未定')}
      ${confirmRow('購入理由', esc(r[`購入理由${i}`]) || '—')}
    </div>` : '').join('');

  // アクション領域
  let actionHtml = '';
  if (completed) {
    actionHtml = `<div class="approval-result done">✓ すべての承認が完了しました</div>`;
  } else if (rejected) {
    actionHtml = `
      <div class="approval-result rejected">差戻し中(修正が必要です)</div>
      ${r.差戻しコメント ? `<div class="reject-comment"><b>差戻し理由:</b> ${esc(r.差戻しコメント)}</div>` : ''}`;
  } else {
    actionHtml = `
      <div class="approval-actions">
        <button class="btn-approve" onclick="approveStep('${id}')">「${currentStep}」として承認する</button>
        <button class="btn-reject"  onclick="showRejectBox('${id}')">差戻し(修正を依頼)</button>
      </div>
      <div id="rejectBox" class="reject-box hidden">
        <label>差戻しの理由(申請者に伝わります)</label>
        <textarea id="rejectComment" placeholder="例:型番を確認してください"></textarea>
        <button class="btn-reject" onclick="rejectStep('${id}')">この内容で差戻す</button>
      </div>`;
  }

  document.getElementById('detailBox').innerHTML = `
    <div class="approval-section">
      <div class="approval-title">承認進捗</div>
      <div class="approval-steps">${stepHtml}</div>
      ${actionHtml}
    </div>
    <div class="confirm-section">
      <div class="confirm-section-title">基本情報</div>
      ${confirmRow('申請日', esc(r.申請日) || '—')}
      ${confirmRow('申請者名', esc(r.申請者名) || '—')}
      ${confirmRow('先行発注済', esc(r.先行発注済) || '—')}
    </div>
    ${items}
  `;
  showPage('pageDetail');
}

function showRejectBox(id) {
  const box = document.getElementById('rejectBox');
  if (box) box.classList.toggle('hidden');
}

function approveStep(id) {
  const r = allRequests.find(x => x.id === id);
  if (!r) return;
  const steps = CONFIG.APPROVAL_STEPS;
  const doneCount = steps.map(s => STEP_DATE_KEYS[s]).filter(k => r[k]).length;
  const step = steps[doneCount];
  if (!step) return;

  // ローカルを先に更新(楽観的更新)
  r[STEP_DATE_KEYS[step]] = todayISO();
  const next = steps[doneCount + 1];
  r.進捗 = next ? `${next}承認待ち` : '完了';

  sendApprovalToGas('approve', id, step, '');
  showDetail(id);
  renderDashboard();
}

function rejectStep(id) {
  const r = allRequests.find(x => x.id === id);
  if (!r) return;
  const comment = (document.getElementById('rejectComment')?.value || '').trim();
  const steps = CONFIG.APPROVAL_STEPS;
  const doneCount = steps.map(s => STEP_DATE_KEYS[s]).filter(k => r[k]).length;
  const step = steps[doneCount] || '';

  r.進捗 = '差戻し';
  r.差戻しコメント = comment;

  sendApprovalToGas('reject', id, step, comment);
  showDetail(id);
  renderDashboard();
}

function sendApprovalToGas(action, id, step, comment) {
  if (!CONFIG.GAS_URL) return;   // デモ: ローカル更新のみ
  const url = `${CONFIG.GAS_URL}?action=${action}&id=${encodeURIComponent(id)}`
            + `&step=${encodeURIComponent(step)}&comment=${encodeURIComponent(comment)}`;
  fetch(url, { mode: 'no-cors' }).catch(() => {});
}

// ===== Service Worker(PWA) =====
function registerServiceWorker() {
  if ('serviceWorker' in navigator && location.protocol === 'https:') {
    navigator.serviceWorker.register('sw.js').catch(() => {});
  }
}

// ===== ユーティリティ =====
function esc(str) {
  return String(str == null ? '' : str)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}
function sortBy(arr, key) {
  return [...arr].sort((a, b) => String(a[key]||'').localeCompare(String(b[key]||''), 'ja'));
}
function simulateRecord(data, id) {
  const rec = {
    id, 申請日: data.申請日 || todayISO(), 申請者名: data.申請者名, 先行発注済: data.先行発注済,
    進捗: '申請中', 総務承認日:'', 課長承認日:'', 副社長承認日:'', 社長承認日:'', 差戻しコメント:'',
  };
  (data.明細 || []).forEach((d, i) => {
    const n = i + 1;
    rec[`品名${n}`] = d.品名; rec[`数量${n}`] = d.数量; rec[`単位${n}`] = d.単位;
    rec[`単価${n}`] = d.単価; rec[`希望納期${n}`] = d.希望納期;
    rec[`科目番号${n}`] = d.科目番号; rec[`購入理由${n}`] = d.購入理由;
  });
  return rec;
}
function getDummyData() {
  return [
    { id:'A1', 申請日:'2026-06-11', 申請者名:'山田 太郎', 品名1:'タップリムーバー TR-P5', 数量1:'1', 単位1:'本', 単価1:'不明', 品名2:'切削油', 進捗:'副社長承認待ち', 総務承認日:'2026-06-11', 課長承認日:'2026-06-12', 副社長承認日:'', 社長承認日:'' },
    { id:'A2', 申請日:'2026-06-10', 申請者名:'佐藤 花子', 品名1:'切削油 #68 / ウエス', 数量1:'5', 単位1:'缶', 単価1:'8400', 進捗:'完了', 総務承認日:'2026-06-10', 課長承認日:'2026-06-10', 副社長承認日:'2026-06-11', 社長承認日:'2026-06-11' },
    { id:'A3', 申請日:'2026-06-09', 申請者名:'鈴木 一郎', 品名1:'安全靴 26.0cm', 数量1:'1', 単位1:'足', 単価1:'6900', 進捗:'申請中', 総務承認日:'', 課長承認日:'', 副社長承認日:'', 社長承認日:'' },
    { id:'A4', 申請日:'2026-06-07', 申請者名:'山田 太郎', 品名1:'コピー用紙 A4 5箱', 数量1:'5', 単位1:'箱', 単価1:'14500', 進捗:'完了', 総務承認日:'2026-06-07', 課長承認日:'2026-06-08', 副社長承認日:'2026-06-08', 社長承認日:'2026-06-09' },
    { id:'A5', 申請日:'2026-06-05', 申請者名:'田中 次郎', 品名1:'ドリル刃セット', 数量1:'2', 単位1:'セット', 単価1:'21000', 進捗:'差戻し', 差戻しコメント:'型番を確認してください', 総務承認日:'2026-06-05', 課長承認日:'', 副社長承認日:'', 社長承認日:'' },
  ];
}
