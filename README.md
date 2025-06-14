# TRAND - Trading Analysis & Discord Notification Bot

暗号資産の自動テクニカル分析と売買シグナルをDiscordに通知するBotです。

## プロジェクトの目的

1. **一貫性のある分析の提供**
   - 主にChatGPT-3.5 Turboを活用し、人間の主観に左右されない一貫性のある分析を提供
   - 感情的な判断を排除し、データドリブンな売買判断を実現

2. **マルチタイムフレーム分析**
   - 月足から15分足まで複数の時間軸で分析
   - 各時間軸でのテクニカル分析と総合的な判断を提供

3. **ファンダメンタル分析の統合**
   - 市場のニュースやイベントを考慮した総合的な判断
   - テクニカルとファンダメンタルの両面から市場を分析

## 機能

- **マルチタイムフレーム分析**: 月足から15分足までの複数のタイムフレームを分析
- **AIによる判断**: ChatGPT-3.5 Turboを活用した売買判断の生成
- **ファンダメンタル分析**: 市場ニュースやイベントを考慮した総合的な判断
- **一貫性の維持**: 以下の方法で分析の一貫性を確保
  - 常に同じプロンプトテンプレートを使用
  - 分析フローを標準化
  - 過去の分析結果との整合性をチェック
  - 定期的なバックテストによる検証
- **定期通知**: アジアタイム・欧州タイム・米国タイムの1日3回通知
- **ログ管理**: すべての分析と判断を記録して戦略の強化に活用
- **簡単なセットアップ**: GitHub Actionsによる自動実行

## AI分析の特徴

1. **テクニカル分析**
   - 移動平均線（SMA, EMA）
   - RSI（相対力指数）
   - MACD（移動平均収束拡散）
   - ボリンジャーバンド
   - 出来高分析

2. **ファンダメンタル分析**
   - 主要な仮想通貨ニュースのモニタリング
   - 市場のセンチメント分析
   - 重要な経済指標の考慮

3. **統合的分析**
   - テクニカルとファンダメンタルの相関分析
   - リスク評価に基づくポジションサイジングの提案
   - 市場のボラティリティを考慮した戦略の調整

## 開発方針

1. **コードの一貫性**
   - PEP 8に準拠したコーディング規約の遵守
   - 型ヒントの活用による型安全性の確保
   - ドキュメント文字列（docstring）の充実

2. **テスト駆動開発**
   - 単体テストの充実
   - 統合テストの実施
   - バックテスト環境の整備

3. **モジュール化**
   - 機能ごとのモジュール分割
   - 依存関係の明確化
   - 設定ファイルの一元管理

4. **セキュリティ**
   - シークレット情報の適切な管理
   - APIレート制限の遵守
   - エラーハンドリングの徹底

## 今後の改善点

1. **分析精度の向上**
   - 追加のテクニカル指標の実装
   - 機械学習モデルの統合
   - センチメント分析の高度化

2. **ユーザビリティの向上**
   - カスタマイズ可能なアラート設定
   - ダッシュボードの作成
   - モバイルアプリの開発

3. **パフォーマンス最適化**
   - 非同期処理の導入
   - キャッシュ戦略の見直し
   - データベースの最適化

## セットアップ

1. リポジトリをクローン:
```bash
git clone https://github.com/myst5218x/TRAND.git
cd TRAND
```

2. Python環境のセットアップ:
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. 環境変数の設定:
`.env.example`ファイルを`.env`にコピーし、必要な情報を入力:
```
# Discord Webhook URL
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your_webhook_id/your_webhook_token

# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here

# Trading configuration
TRADING_INTERVALS=["1d", "4h", "1h", "15m"]
NOTIFICATION_TIMES=["09:00", "17:00", "01:00"]  # Asia, Europe, US market times (UTC)
```

4. Botの実行:
```bash
python -m src.main
```

## 使用方法

- 通知スケジュールは`.env`ファイルの`NOTIFICATION_TIMES`で設定できます
- 分析タイムフレームは`.env`ファイルの`TRADING_INTERVALS`で設定できます
- ログは`logs/`ディレクトリに保存されます

## GitHub Actionsによる自動実行

このリポジトリはGitHub Actionsを使って自動実行されるよう設定されています。詳細は`.github/workflows/trading_bot.yml`を参照してください。

## License

MIT
