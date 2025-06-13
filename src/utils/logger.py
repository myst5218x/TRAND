"""
ロギングユーティリティモジュール
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional

from ..config import LOG_DIR, LOG_LEVEL, LOG_FORMAT, LOG_DATE_FORMAT

def setup_logger(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """
    ロギング設定を行いロガーを返す
    
    Args:
        name: ロガー名
        log_file: ログファイル名（指定しない場合はデフォルトの命名規則を使用）
        
    Returns:
        logging.Logger: 設定されたロガーインスタンス
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL))
    
    # 既存のハンドラをクリア
    if logger.handlers:
        logger.handlers.clear()
    
    # コンソールハンドラ
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT))
    logger.addHandler(console_handler)
    
    # ファイルハンドラ
    if log_file is None:
        timestamp = datetime.now().strftime("%Y%m%d")
        log_file = f"{name}_{timestamp}.log"
        
    file_path = LOG_DIR / log_file
    file_handler = RotatingFileHandler(
        file_path, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
    )
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT))
    logger.addHandler(file_handler)
    
    return logger


def get_trade_logger() -> logging.Logger:
    """
    取引ログ専用のロガーを取得
    
    Returns:
        logging.Logger: 取引ログ用ロガー
    """
    return setup_logger("trade", "trading_signals.log")


def get_notification_logger() -> logging.Logger:
    """
    通知ログ専用のロガーを取得
    
    Returns:
        logging.Logger: 通知ログ用ロガー
    """
    return setup_logger("notification", "discord_notification.log")


def get_analysis_logger() -> logging.Logger:
    """
    分析ログ専用のロガーを取得
    
    Returns:
        logging.Logger: 分析ログ用ロガー
    """
    return setup_logger("analysis", "market_analysis.log")
