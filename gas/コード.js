// ============================================================
// Google Apps Script (GAS) - スプレッドシート連携
// ============================================================
// 使い方:
// 1. Google スプレッドシートを新規作成
// 2. メニュー「拡張機能」→「Apps Script」を開く
// 3. このファイルの内容を貼り付けて保存
// 4. 「デプロイ」→「新しいデプロイ」→「種類: ウェブアプリ」
//    次のユーザーとして実行: 自分 / アクセスできるユーザー: 全員  で公開
// 5. 発行されたURLを js/config.js の GAS_URL に貼る
// ============================================================

const SHEET_ID = SpreadsheetApp.getActiveSpreadsheet().getId();

// ▼▼ 通知設定(任意) ▼▼
// 承認担当者にメールで通知したい場合、ここにメールアドレスを設定してください。
// 空のままなら通知は送られません(アプリは問題なく動きます)。
const EMAIL_MAP = {
  '総務':   '',   // 例: 'somu@example.com'
  '課長':   '',
  '副社長': '',
  '社長':   '',
};
// アプリのURL(メール文面のリンク用・任意)。GitHub PagesのURLなどを入れる。
const APP_URL = '';
// ▲▲ 通知設定ここまで ▲▲

const HEADERS = [
  'id', '申請日', '申請者名', '先行発注済',
  ...[...Array(10)].flatMap((_, i) => [
    `品名${i+1}`, `数量${i+1}`, `単位${i+1}`,
    `単価${i+1}`, `希望納期${i+1}`, `科目番号${i+1}`, `購入理由${i+1}`
  ]),
  '進捗', '総務承認日', '課長承認日', '副社長承認日', '社長承認日', '差戻しコメント',
];

const APPROVAL_STEPS = ['総務', '課長', '副社長', '社長'];
const STEP_DATE = { '総務': '総務承認日', '課長': '課長承認日', '副社長': '副社長承認日', '社長': '社長承認日' };

function doGet(e) {
  const p = e.parameter;
  if (p.action === 'list')    return listAll();
  if (p.action === 'detail')  return getDetail(p.id);
  if (p.action === 'approve') return approve(p.id);
  if (p.action === 'reject')  return reject(p.id, p.comment);
  return json({ error: 'unknown action' });
}

function doPost(e) {
  try {
    const payload = JSON.parse(e.postData.contents);
    if (payload.action === 'submit') return submitRow(payload);
    return json({ error: 'unknown action' });
  } catch (err) {
    return json({ error: err.message });
  }
}

// ===== 一覧取得 =====
function listAll() {
  const ss = SpreadsheetApp.openById(SHEET_ID);
  const results = [];
  ss.getSheets().forEach(sheet => {
    const data = sheet.getDataRange().getValues();
    if (data.length < 2) return;
    const headers = data[0];
    data.slice(1).forEach(row => {
      const obj = {};
      headers.forEach((h, i) => { obj[h] = row[i] !== undefined ? String(row[i]) : ''; });
      obj._sheet = sheet.getName();
      results.push(obj);
    });
  });
  results.sort((a, b) => String(b.申請日).localeCompare(String(a.申請日)));
  return json(results);
}

function getDetail(id) {
  const row = findRow(id);
  return json(row || { error: 'not found' });
}

// ===== 申請の新規登録 =====
function submitRow(payload) {
  const ss = SpreadsheetApp.openById(SHEET_ID);
  const sheetName = payload.sheetName || '購入依頼';
  let sheet = ss.getSheetByName(sheetName);
  if (!sheet) {
    sheet = ss.insertSheet(sheetName);
    sheet.appendRow(HEADERS);
    sheet.getRange(1, 1, 1, HEADERS.length).setFontWeight('bold').setBackground('#dbeafe');
    sheet.setFrozenRows(1);
  }
  sheet.appendRow(payload.row);

  // 最初の承認者(総務)へ通知
  notifyApprover('総務', payload.row);
  return json({ success: true, id: payload.id });
}

// ===== 承認処理 =====
function approve(id) {
  const found = findRow(id, true);
  if (!found) return json({ error: 'not found' });
  const { sheet, rowIndex, headers, row } = found;

  const doneCount = APPROVAL_STEPS
    .map(s => headers.indexOf(STEP_DATE[s]))
    .filter(col => col >= 0 && row[col]).length;
  const step = APPROVAL_STEPS[doneCount];
  if (!step) return json({ error: 'already completed' });

  const dateCol = headers.indexOf(STEP_DATE[step]);
  sheet.getRange(rowIndex, dateCol + 1).setValue(today());

  const next = APPROVAL_STEPS[doneCount + 1];
  const progressCol = headers.indexOf('進捗');
  const newProgress = next ? `${next}承認待ち` : '完了';
  sheet.getRange(rowIndex, progressCol + 1).setValue(newProgress);

  if (next) notifyApprover(next, row, headers);
  return json({ success: true, progress: newProgress });
}

// ===== 差戻し処理 =====
function reject(id, comment) {
  const found = findRow(id, true);
  if (!found) return json({ error: 'not found' });
  const { sheet, rowIndex, headers } = found;

  const progressCol = headers.indexOf('進捗');
  sheet.getRange(rowIndex, progressCol + 1).setValue('差戻し');

  const commentCol = headers.indexOf('差戻しコメント');
  if (commentCol >= 0) sheet.getRange(rowIndex, commentCol + 1).setValue(comment || '');

  return json({ success: true, progress: '差戻し' });
}

// ===== メール通知 =====
function notifyApprover(step, row, headers) {
  const to = EMAIL_MAP[step];
  if (!to) return;   // 未設定なら送らない
  headers = headers || HEADERS;
  const applicant = row[headers.indexOf('申請者名')] || '';
  const item = row[headers.indexOf('品名1')] || '';
  const linkText = APP_URL ? `\n\n▼ 確認・承認はこちら\n${APP_URL}` : '';
  const subject = `【購入依頼】${step}の承認をお願いします`;
  const body = `${step} ご担当者さま\n\n`
    + `新しい購入依頼が${step}の承認待ちです。\n\n`
    + `申請者: ${applicant}\n`
    + `品名: ${item}\n`
    + linkText;
  try { MailApp.sendEmail(to, subject, body); } catch (e) {}
}

// ===== 内部: 行を探す =====
function findRow(id, withPosition) {
  const ss = SpreadsheetApp.openById(SHEET_ID);
  for (const sheet of ss.getSheets()) {
    const data = sheet.getDataRange().getValues();
    if (data.length < 2) continue;
    const headers = data[0];
    const idCol = headers.indexOf('id');
    if (idCol < 0) continue;
    for (let i = 1; i < data.length; i++) {
      if (String(data[i][idCol]) === String(id)) {
        if (!withPosition) {
          const obj = {};
          headers.forEach((h, j) => { obj[h] = String(data[i][j]); });
          return obj;
        }
        return { sheet, rowIndex: i + 1, headers, row: data[i] };
      }
    }
  }
  return null;
}

function today() { return new Date().toISOString().slice(0, 10); }

function json(data) {
  return ContentService
    .createTextOutput(JSON.stringify(data))
    .setMimeType(ContentService.MimeType.JSON);
}
