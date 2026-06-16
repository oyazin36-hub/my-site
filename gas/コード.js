// ============================================================
// Google Apps Script (GAS) - スプレッドシート連携
// ============================================================
// 使い方:
// 1. Google スプレッドシートを新規作成
// 2. メニュー「拡張機能」→「Apps Script」を開く
// 3. このファイルの内容を貼り付けて保存
// 4. 「デプロイ」→「新しいデプロイ」→「種類: ウェブアプリ」
//    アクセスできるユーザー: 全員  で公開
// 5. 発行されたURLを js/config.js の GAS_URL に貼る
// ============================================================

const SHEET_ID = SpreadsheetApp.getActiveSpreadsheet().getId();

function doGet(e) {
  const action = e.parameter.action;
  if (action === 'list') return listAll();
  if (action === 'detail') return getDetail(e.parameter.id);
  if (action === 'approve') return approve(e.parameter.id, e.parameter.step, e.parameter.user);
  return json({ error: 'unknown action' });
}

function doPost(e) {
  try {
    const payload = JSON.parse(e.postData.contents);
    if (payload.action === 'submit') return submitRow(payload);
    return json({ error: 'unknown action' });
  } catch(err) {
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
  // 申請日降順
  results.sort((a, b) => b.申請日.localeCompare(a.申請日));
  return json(results);
}

// ===== 詳細取得 =====
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
    // シートがなければ自動作成(ヘッダー行を書く)
    sheet = ss.insertSheet(sheetName);
    // 購入依頼の列ヘッダー
    const headers = [
      'id', '申請日', '申請者名', '先行発注済',
      ...[...Array(10)].flatMap((_, i) => [
        `品名${i+1}`, `数量${i+1}`, `単位${i+1}`,
        `単価${i+1}`, `希望納期${i+1}`, `科目番号${i+1}`, `購入理由${i+1}`
      ]),
      '進捗', '総務承認日', '課長承認日', '副社長承認日', '社長承認日',
    ];
    sheet.appendRow(headers);
    sheet.getRange(1, 1, 1, headers.length).setFontWeight('bold').setBackground('#dbeafe');
    sheet.setFrozenRows(1);
  }
  sheet.appendRow(payload.row);

  // 承認担当者にメール通知(省略可:メールアドレスを設定する場合)
  notifyApprover('総務', payload.row);

  return json({ success: true, id: payload.id });
}

// ===== 承認処理 =====
function approve(id, step, approvedBy) {
  const stepKeyMap = { '総務': '総務承認日', '課長': '課長承認日', '副社長': '副社長承認日', '社長': '社長承認日' };
  const steps = ['総務', '課長', '副社長', '社長'];

  const result = findRow(id, true); // withPosition=true
  if (!result) return json({ error: 'not found' });
  const { sheet, rowIndex, headers, row } = result;

  const dateCol = headers.indexOf(stepKeyMap[step]);
  if (dateCol < 0) return json({ error: 'invalid step' });
  sheet.getRange(rowIndex, dateCol + 1).setValue(new Date().toISOString().slice(0, 10));

  const stepIdx = steps.indexOf(step);
  const nextStep = steps[stepIdx + 1];
  const progressCol = headers.indexOf('進捗');
  const newProgress = nextStep ? `${nextStep}承認待ち` : '完了';
  sheet.getRange(rowIndex, progressCol + 1).setValue(newProgress);

  if (nextStep) notifyApprover(nextStep, row, headers);

  return json({ success: true, progress: newProgress });
}

// ===== メール通知(任意設定) =====
function notifyApprover(step, row, headers) {
  // 通知したい場合はここに宛先を設定してください
  // const EMAIL_MAP = { '総務': 'somu@example.com', '課長': 'kacho@example.com', ... };
  // const to = EMAIL_MAP[step];
  // if (!to) return;
  // MailApp.sendEmail(to, `【購入依頼】${step}の承認依頼が届いています`, `...`);
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
      if (String(data[i][idCol]) === id) {
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

// ===== JSON レスポンス =====
function json(data) {
  return ContentService
    .createTextOutput(JSON.stringify(data))
    .setMimeType(ContentService.MimeType.JSON);
}
