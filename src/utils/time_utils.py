"""
時間関連のユーティリティ関数
"""
from datetime import datetime, timedelta
import pytz
from typing import List, Dict, Optional, Tuple


def get_current_utc_time() -> datetime:
    """
    現在のUTC時間を取得する
    
    Returns:
        datetime: 現在のUTC時間
    """
    return datetime.now(pytz.UTC)


def get_jst_time() -> datetime:
    """
    現在の日本時間を取得する
    
    Returns:
        datetime: 現在の日本時間
    """
    jst = pytz.timezone('Asia/Tokyo')
    return datetime.now(jst)


def format_time_for_display(dt: datetime) -> str:
    """
    表示用に時間をフォーマットする
    
    Args:
        dt: 時間オブジェクト
        
    Returns:
        str: フォーマットされた時間文字列
    """
    return dt.strftime("%Y-%m-%d %H:%M:%S %Z")


def is_market_hours(market_type: str) -> bool:
    """
    特定の市場が取引時間内かどうかを判定する
    
    Args:
        market_type: 市場タイプ ("asia", "europe", "us")
        
    Returns:
        bool: 取引時間内であればTrue
    """
    now = get_current_utc_time()
    hour = now.hour
    
    if market_type.lower() == "asia":
        # UTC 0:00-8:00 (JST 9:00-17:00)
        return 0 <= hour < 8
    elif market_type.lower() == "europe":
        # UTC 8:00-16:00
        return 8 <= hour < 16
    elif market_type.lower() == "us":
        # UTC 16:00-24:00
        return 16 <= hour < 24
    
    return False


def get_timeframe_start_end(timeframe: str) -> Tuple[datetime, datetime]:
    """
    タイムフレームの開始時間と終了時間を取得する
    
    Args:
        timeframe: タイムフレーム文字列 (例: "1d", "4h", "1h", "15m")
        
    Returns:
        Tuple[datetime, datetime]: (開始時間, 終了時間)
    """
    now = get_current_utc_time()
    
    if timeframe == "1d":
        end = now
        start = end - timedelta(days=30)  # 30日分のデータ
    elif timeframe == "4h":
        end = now
        start = end - timedelta(days=10)  # 10日分のデータ
    elif timeframe == "1h":
        end = now
        start = end - timedelta(days=5)  # 5日分のデータ
    elif timeframe == "15m":
        end = now
        start = end - timedelta(days=2)  # 2日分のデータ
    else:
        # デフォルト: 1日
        end = now
        start = end - timedelta(days=1)
        
    return start, end


def determine_current_session() -> str:
    """
    現在どの取引セッション（アジア/欧州/米国）かを判定する
    
    Returns:
        str: 現在のセッション名 ("asia", "europe", "us")
    """
    if is_market_hours("asia"):
        return "asia"
    elif is_market_hours("europe"):
        return "europe"
    else:
        return "us"


def is_notification_time(notification_times: List[str]) -> bool:
    """
    通知時間かどうかを判定する
    
    Args:
        notification_times: 通知時間のリスト (例: ["09:00", "17:00", "01:00"])
        
    Returns:
        bool: 通知時間であればTrue
    """
    now = get_current_utc_time()
    current_time = now.strftime("%H:%M")
    
    # 完全一致（時分が同じ）
    if current_time in notification_times:
        return True
        
    # 指定時間から5分以内
    for time_str in notification_times:
        hour, minute = map(int, time_str.split(":"))
        target_time = now.replace(hour=hour, minute=minute)
        
        time_diff = abs((now - target_time).total_seconds())
        if time_diff <= 300:  # 5分 = 300秒
            return True
            
    return False
