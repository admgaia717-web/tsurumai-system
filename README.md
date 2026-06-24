# つるまい移動支援 コパイロット

ボランティア電話受付支援システム。

## 構成
- `index.html` — ボランティア用受付画面（Supabase連携）
- Supabaseプロジェクト: ftemqjfkibpprtvitgph
- DB: locations(50) / users(94) / drivers(1) / reservations(891) / operation_rules(8)

## ConoHa WING デプロイ手順
1. このリポジトリをWING管理画面「Git デプロイ」で連携
2. デプロイ先ディレクトリを公開ディレクトリに設定
3. https://（ドメイン）/index.html でアクセス

## 注意
- メール通知（notify_server.py）はWINGでは動かない
  → 別途 Supabase Edge Function で実装予定
- 個人宅の場所ピンは現場で育成（S/A/Bランク）

## 運用
- ボランティア：電話→赤ボタン録音→承認（2タップ）
- ドライバー：メール通知で地図リンク受信
