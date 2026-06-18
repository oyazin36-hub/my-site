Attribute VB_Name = "Module_集約"
Option Explicit

' === 全案件シートを「年間スケジュール」に集約する ===
Sub 集約()
    Dim wsM As Worksheet, ws As Worksheet
    Dim n As Long, rp As Long, t As Long, off As Long
    Dim baseD As Date, sd As Variant, nm As String
    Application.ScreenUpdating = False
    Set wsM = ThisWorkbook.Sheets("年間スケジュール")
    baseD = wsM.Range("D2").Value
    ' 既存データ・ラベルをクリア（6〜45行）
    wsM.Range("A6:F45").ClearContents
    For rp = 6 To 45
        wsM.Range(wsM.Cells(rp, 8), wsM.Cells(rp, 372)).ClearContents
    Next rp
    n = 0
    For Each ws In ThisWorkbook.Worksheets
        If IsProjectSheet(ws) Then
            rp = 6 + n * 2
            If rp > 44 Then Exit For
            wsM.Cells(rp, 1).Value = n + 1
            wsM.Cells(rp, 2).Value = ws.Name
            wsM.Cells(rp, 3).Value = ws.Range("C6").Value
            wsM.Cells(rp, 4).Formula = "=MIN('" & ws.Name & "'!D6:D45)"
            wsM.Cells(rp, 5).Formula = "=MAX('" & ws.Name & "'!E6:E45)"
            wsM.Cells(rp, 6).Formula = "=IF(COUNT('" & ws.Name & "'!F6:F45)=0,"""",MAX('" & ws.Name & "'!F6:F45))"
            ' 予定バー上に各タスク名を配置
            For t = 6 To 45
                sd = ws.Cells(t, 4).Value
                nm = CStr(ws.Cells(t, 2).Value)
                If IsDate(sd) And Len(nm) > 0 Then
                    off = CLng(CDate(sd) - baseD)
                    If off >= 0 And off < 365 Then wsM.Cells(rp, 8 + off).Value = nm
                End If
            Next t
            n = n + 1
        End If
    Next ws
    Application.ScreenUpdating = True
    MsgBox n & " 件の案件を集約しました。", vbInformation, "集約"
End Sub

' 案件シートかどうか判定（ビュー系シートは除外）
Function IsProjectSheet(ws As Worksheet) As Boolean
    Select Case ws.Name
        Case "年間スケジュール", "月別", "簡易表", "使い方・マクロ"
            IsProjectSheet = False
        Case Else
            IsProjectSheet = (ws.Range("A3").Value = "No" And ws.Range("G6").Value = "予定")
    End Select
End Function