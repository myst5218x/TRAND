"""
設定モジュール - 環境変数とアプリケーション設定の管理
"""
import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# .envファイルを読み込む
load_dotenv()

# プロジェクトルートディレクトリ
ROOT_DIR = Path(__file__).parent.parent

# ログディレクトリ
LOG_DIR = ROOT_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# APIキー
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")

# 取引設定
try:
    TRADING_INTERVALS = json.loads(os.getenv("TRADING_INTERVALS", '["1d", "4h", "1h", "15m"]'))
except json.JSONDecodeError:
    TRADING_INTERVALS = ["1d", "4h", "1h", "15m"]

try:
    NOTIFICATION_TIMES = json.loads(os.getenv("NOTIFICATION_TIMES", '["09:00", "17:00", "01:00"]'))
except json.JSONDecodeError:
    NOTIFICATION_TIMES = ["09:00", "17:00", "01:00"]  # Asia, Europe, US market times (UTC)

# 分析対象の暗号資産
DEFAULT_SYMBOL = "BTC/USDT"

# テクニカル指標設定
TECHNICAL_INDICATORS = {
    "sma": [20, 50, 200],  # 単純移動平均
    "ema": [9, 21, 55, 200],  # 指数移動平均
    "rsi": 14,  # RSI
    "macd": {"fast": 12, "slow": 26, "signal": 9},  # MACD
    "bbands": {"period": 20, "std": 2.0},  # ボリンジャーバンド
}

# 通知設定
MAX_RETRIES = 3  # 通知失敗時の再試行回数
RETRY_DELAY = 5  # 再試行間隔（秒）

# ロギング設定
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def validate_config() -> bool:
    """
    設定の検証を行う
    
    Returns:
        bool: 設定が有効であればTrue
    """
    if not OPENAI_API_KEY:
        print("警告: OPENAI_API_KEYが設定されていません")
        return False
        
    if not DISCORD_WEBHOOK_URL:
        print("警告: DISCORD_WEBHOOK_URLが設定されていません")
        return False
    
    return True
