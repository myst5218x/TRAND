# TRAND - Trading Analysis & Discord Notification Bot

暗号資産の自動テクニカル分析と売買シグナルをDiscordに通知するBotです。

## 機能

- **マルチタイムフレーム分析**: 月足から15分足までの複数のタイムフレームを分析
- **AIによる判断**: ChatGPT Turboを活用した売買判断の生成
- **定期通知**: アジアタイム・欧州タイム・米国タイムの1日3回通知
- **ログ管理**: すべての分析と判断を記録して戦略の強化に活用
- **簡単なセットアップ**: GitHub Actionsによる自動実行

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
