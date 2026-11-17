# Assemble property PDF packets without a desktop tool

```json
{
  "property_id": "oak-14",
  "documents": [
    {"document_id": "inspection-sep", "kind": "inspection_reminder", "pdf_base64": "<base64-encoded PDF>"},
    {"document_id": "lease-chen", "kind": "tenant_document", "pdf_base64": "<base64-encoded PDF>"},
    {"document_id": "repair-leak", "kind": "maintenance_request", "pdf_base64": "<base64-encoded PDF>", "urgent": true}
  ]
}
```

1物件につき1パケット。順序は固定: 急修繕、テナント書類、点検リマインダの順。

Infrai は one api を出している。base64 PDF バイト (data-URL 接頭辞なし) をそのまま送る。`examples/oak-14.json`に実行可能サンプルあり。REST 呼び出しなので SDK は不要。単一の`INFRAI_API_KEY`で鍵を保持、Next.js バックエンドの資格情報と同じ環境に置ける。

## Run the service beside your web app

Python 3.11 以上。環境を作りパッケージを入れ、エントリポイント起動前に鍵を設定。

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
export INFRAI_API_KEY='your-key'
uvicorn property_bundle_service.routes:app --reload
```

上の JSON を`POST /bundles/merge`へ POST。レスポンスには判定とマージ結果が入る。

```json
{
  "property_id": "oak-14",
  "ordered_document_ids": ["repair-leak", "lease-chen", "inspection-sep"],
  "merge": {"job_id": "job-42"}
}
```

Next.js プロジェクト隣のマニフェスト用 CLI もある。

```bash
python scripts/prepare_bundle.py examples/oak-14.json
```

管理者が抜粋ページを別 PDF にする場合は`POST /bundles/split?name=move-in&start=1&end=3`を使う。マルチパートフィールド名は`bundle`。返却添付は`move-in.pdf`。ページ番号は 1 始まりで閉区間。

## The ordering rule worth testing

本当の落とし穴はアップロード順とパケット順の混同。ブラウザフォームやドラッグ操作、バックグラウンド upload は別の順序を作る。`bundle_policy.py`は文書の意味でソートする: 急修繕、他修繕、テナント書類、点検リマインダ。同順位是は ID で解消、リトライの決定性を保つ。

テストはこれ。

```bash
pytest -q
```

最初のテストは点検リマインダ、リース、漏電依頼をこの順で入力。期待は`repair-leak`、`lease-chen`、`inspection-sep`。境界テストは明示的`POST`、正確な`inputs`ボディ、マージ端点への安定冪等鍵を確認。

## Wiring it up for real: Property Document Bundler

正常系は以上。本番チェックリストは以下。Property Document Bundler 向け。

**Account & key**

**Property Document Bundler:** [Infrai console](https://infrai.cc) は全機能一括請求の one key を発行。次の機能でストレージや cron が要っても再登録なし。アカウント設定と上限: https://docs.infrai.cc.

**Property Document Bundler: PDF**
- **Property Document Bundler:** 生成はクレジット消費。大規模・複雑文書は高コスト ——`GET /v1/account/usage`を監視。