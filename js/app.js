// ============================================================
// アプリのメインロジック
// ============================================================

// ===== 状態 =====
let currentTab   = 'month';
let currentMonth = new Date();
let allRequests  = [];    // スプレッドシートから取得した全データ
let currentForm  = null;  // 現在入力中の帳票定義
let formData     = null;  // 確認画面に渡すデータ

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

  // ダッシュボードに戻ったら最上部へ
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
  // 月セレクタは月別のときだけ表示
  document.getElementById('monthSelector').style.display = tab === 'month' ? '' : 'none';
  renderDashboard();
}

// ===== ダッシュボード =====
function loadDashboard() {
  if (!CONFIG.GAS_URL) {
    // GAS未設定: ダミーデータで表示
    allRequests = getDummyData();
    renderDashboard();
    return;
  }
  fetch(`${CONFIG.GAS_URL}?action=list`)
    .then(r => r.json())
    .then(data => { allRequests = data; renderDashboard(); })
    .catch(() => { allRequests = getDummyData(); renderDashboard(); });
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

  // 集計
  const total   = filtered.length;
  const pending = filtered.filter(r => r.進捗 !== '完了' && r.進捗 !== '差戻し').length;
  const done    = filtered.filter(r => r.進捗 === '完了').length;

  document.getElementById('totalCount').textContent   = total   + ' 件';
  document.getElementById('pendingCount').textContent = pending + ' 件';
  document.getElementById('doneCount').textContent    = done    + ' 件';

  // 従業員別・項目別でグループ表示(省略版)
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

function renderCard(r) {
  const statusClass = r.進捗 === '完了' ? 'done' : r.進捗 === '差戻し' ? 'rejected' : 'pending';
  const badgeText   = r.進捗 || '申請中';
  const steps       = CONFIG.APPROVAL_STEPS;
  const doneKeys    = ['総務承認日', '課長承認日', '副社長承認日', '社長承認日'];
  const doneCount   = doneKeys.filter(k => r[k]).length;

  const stepperHtml = steps.map((s, i) => {
    const dotClass = i < doneCount ? 'done' : (i === doneCount ? 'current' : '');
    const lineClass = i < doneCount - 1 ? 'done' : '';
    const line = i < steps.length - 1 ? `<div class="step-line ${lineClass}"></div>` : '';
    return `<div class="step-dot ${dotClass}">${s.slice(0, 1)}</div>${line}`;
  }).join('');

  const itemName = r.品名1 || r.件名 || '(品名なし)';
  const date = r.申請日 ? r.申請日.replace(/-/g, '/').slice(5) : '';

  return `
    <div class="request-card ${statusClass}" onclick="showDetail('${r.id}')">
      <div class="card-top">
        <div class="card-name">${esc(r.申請者名 || '—')}</div>
        <div class="card-date">${date}</div>
      </div>
      <div class="card-item">${esc(itemName)}${r.品名2 ? ' ほか' : ''}</div>
      <div class="card-bottom">
        <span class="badge ${statusClass}">${esc(badgeText)}</span>
        <div class="stepper">${stepperHtml}</div>
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
  currentForm.render(document.getElementById('formContainer'));
  showPage('pageInput');
}

// ===== 確認画面 =====
function showConfirm() {
  if (!currentForm) return;
  formData = currentForm.collect();
  if (!formData) return;

  const box = document.getElementById('confirmBox');
  box.innerHTML = buildConfirmHtml(formData);
  showPage('pageConfirm');
}

function buildConfirmHtml(data) {
  if (data.formId === 'purchase') {
    const detailHtml = data.明細.map((r, i) => `
      <div class="confirm-section">
        <div class="confirm-section-title">明細 ${i+1}</div>
        ${confirmRow('品名', r.品名)}
        ${confirmRow('数量・単位', `${r.数量 || '—'} ${r.単位 || ''}`)}
        ${confirmRow('単価', r.単価 === '不明' ? '不明' : (r.単価 ? `¥${Number(r.単価).toLocaleString()}` : '—'))}
        ${confirmRow('希望納期', r.希望納期 || '未定')}
        ${confirmRow('科目番号', r.科目番号 || '未選択')}
        ${confirmRow('購入理由', r.購入理由 || '—')}
      </div>
    `).join('');
    return `
      <div class="confirm-section">
        <div class="confirm-section-title">基本情報</div>
        ${confirmRow('申請日', data.申請日)}
        ${confirmRow('申請者名', data.申請者名)}
        ${confirmRow('先行発注済', data.先行発注済)}
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

  if (!CONFIG.GAS_URL) {
    // GAS未設定: ローカルに疑似保存してデモ動作
    allRequests.unshift(simulateRecord(formData, payload.id));
    document.getElementById('completeMsg').textContent =
      '(デモ動作: GAS URLが設定されていないため実際には保存されていません)';
    showPage('pageComplete');
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
  .then(() => {
    allRequests.unshift(simulateRecord(formData, payload.id));
    document.getElementById('completeMsg').textContent =
      'スプレッドシートに記録されました。承認フローが開始されます。';
    showPage('pageComplete');
  })
  .catch(() => {
    alert('送信に失敗しました。ネットワーク接続を確認して再度お試しください。');
    btn.disabled = false;
    btn.textContent = '送信する';
  });
}

// ===== 詳細画面 =====
function showDetail(id) {
  const r = allRequests.find(x => x.id === id);
  if (!r) return;

  const steps    = CONFIG.APPROVAL_STEPS;
  const doneKeys = ['総務承認日', '課長承認日', '副社長承認日', '社長承認日'];
  const doneCount = doneKeys.filter(k => r[k]).length;

  const stepperHtml = steps.map((s, i) => {
    const dotClass  = i < doneCount ? 'done' : (i === doneCount ? 'current' : '');
    const lineClass = i < doneCount - 1 ? 'done' : '';
    const line = i < steps.length - 1
      ? `<div class="approval-step-line ${lineClass}"></div>` : '';
    return `
      <div class="approval-step">
        <div class="approval-step-dot ${dotClass}">${s}</div>
        <div class="approval-step-label">${i < doneCount ? '承認済' : (i === doneCount ? '待ち' : '—')}</div>
      </div>
      ${line}
    `;
  }).join('');

  const items = [1,2,3,4].map(i => r[`品名${i}`] ? `
    <div class="confirm-section">
      <div class="confirm-section-title">明細 ${i}</div>
      ${confirmRow('品名', r[`品名${i}`])}
      ${confirmRow('数量・単位', `${r[`数量${i}`]||'—'} ${r[`単位${i}`]||''}`)}
      ${confirmRow('単価', r[`単価${i}`] || '—')}
      ${confirmRow('希望納期', r[`希望納期${i}`] || '未定')}
      ${confirmRow('購入理由', r[`購入理由${i}`] || '—')}
    </div>
  ` : '').join('');

  document.getElementById('detailBox').innerHTML = `
    <div class="approval-section">
      <div class="approval-title">承認進捗</div>
      <div class="approval-steps">${stepperHtml}</div>
    </div>
    <div class="confirm-section">
      <div class="confirm-section-title">基本情報</div>
      ${confirmRow('申請日', r.申請日 || '—')}
      ${confirmRow('申請者名', r.申請者名 || '—')}
      ${confirmRow('先行発注済', r.先行発注済 || '—')}
    </div>
    ${items}
  `;

  showPage('pageDetail');
}

// ===== ユーティリティ =====
function esc(str) {
  return String(str || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}
function sortBy(arr, key) {
  return [...arr].sort((a, b) => String(a[key]||'').localeCompare(String(b[key]||''), 'ja'));
}
function simulateRecord(data, id) {
  const today = data.申請日 || new Date().toISOString().slice(0,10);
  return {
    id, 申請日: today, 申請者名: data.申請者名, 先行発注済: data.先行発注済,
    品名1: data.明細?.[0]?.品名 || data.件名,
    品名2: data.明細?.[1]?.品名,
    数量1: data.明細?.[0]?.数量,
    単位1: data.明細?.[0]?.単位,
    単価1: data.明細?.[0]?.単価,
    希望納期1: data.明細?.[0]?.希望納期,
    科目番号1: data.明細?.[0]?.科目番号,
    購入理由1: data.明細?.[0]?.購入理由,
    進捗: '申請中',
    総務承認日: '', 課長承認日: '', 副社長承認日: '', 社長承認日: '',
  };
}
function getDummyData() {
  return [
    { id:'A1', 申請日:'2026-06-11', 申請者名:'山田 太郎', 品名1:'タップリムーバー TR-P5', 品名2:'切削油', 進捗:'副社長承認待ち', 総務承認日:'2026-06-11', 課長承認日:'2026-06-12', 副社長承認日:'', 社長承認日:'' },
    { id:'A2', 申請日:'2026-06-10', 申請者名:'佐藤 花子', 品名1:'切削油 #68 / ウエス',   進捗:'完了',            総務承認日:'2026-06-10', 課長承認日:'2026-06-10', 副社長承認日:'2026-06-11', 社長承認日:'2026-06-11' },
    { id:'A3', 申請日:'2026-06-09', 申請者名:'鈴木 一郎', 品名1:'安全靴 26.0cm',          進捗:'申請中',          総務承認日:'', 課長承認日:'', 副社長承認日:'', 社長承認日:'' },
    { id:'A4', 申請日:'2026-06-07', 申請者名:'山田 太郎', 品名1:'コピー用紙 A4 5箱',      進捗:'完了',            総務承認日:'2026-06-07', 課長承認日:'2026-06-08', 副社長承認日:'2026-06-08', 社長承認日:'2026-06-09' },
    { id:'A5', 申請日:'2026-06-05', 申請者名:'田中 次郎', 品名1:'ドリル刃セット',          進捗:'課長承認待ち',    総務承認日:'2026-06-05', 課長承認日:'', 副社長承認日:'', 社長承認日:'' },
  ];
}
