"""
Discord通知モジュール
"""
import json
import time
from typing import Dict, List, Any, Optional
from discord_webhook import DiscordWebhook, DiscordEmbed
from datetime import datetime

from .utils.logger import get_notification_logger
from .utils.time_utils import get_current_utc_time, format_time_for_display
from .config import DISCORD_WEBHOOK_URL, MAX_RETRIES, RETRY_DELAY

logger = get_notification_logger()

class DiscordNotifier:
    """Discord通知を送信するクラス"""
    
    def __init__(self, webhook_url: Optional[str] = None):
        """
        初期化
        
        Args:
            webhook_url: Discord Webhook URL (デフォルトはconfig.pyから取得)
        """
        self.webhook_url = webhook_url or DISCORD_WEBHOOK_URL
        
    def send_message(self, content: str, embeds: List[Dict[str, Any]] = None) -> bool:
        """
        基本的なメッセージを送信する
        
        Args:
            content: メッセージの本文
            embeds: 埋め込みオブジェクトのリスト
            
        Returns:
            bool: 送信成功の場合はTrue
        """
        if not self.webhook_url:
            logger.error("Discord webhook URL is not configured")
            return False
            
        webhook = DiscordWebhook(url=self.webhook_url, content=content)
        
        if embeds:
            for embed_data in embeds:
                embed = DiscordEmbed(**embed_data)
                webhook.add_embed(embed)
                
        # 再試行メカニズム
        for attempt in range(MAX_RETRIES):
            try:
                response = webhook.execute()
                
                if response and response.status_code in [200, 204]:
                    logger.info(f"Discord notification sent successfully")
                    return True
                else:
                    status = response.status_code if response else "No response"
                    logger.error(f"Failed to send Discord notification: Status {status}")
                    
                    if attempt < MAX_RETRIES - 1:
                        logger.info(f"Retrying in {RETRY_DELAY} seconds... (Attempt {attempt + 1}/{MAX_RETRIES})")
                        time.sleep(RETRY_DELAY)
                    else:
                        return False
                        
            except Exception as e:
                logger.error(f"Error sending Discord notification: {str(e)}")
                
                if attempt < MAX_RETRIES - 1:
                    logger.info(f"Retrying in {RETRY_DELAY} seconds... (Attempt {attempt + 1}/{MAX_RETRIES})")
                    time.sleep(RETRY_DELAY)
                else:
                    return False
                    
        return False
        
    def send_market_analysis(self, analysis_data: Dict[str, Any], session_name: str) -> bool:
        """
        市場分析結果の通知を送信する
        
        Args:
            analysis_data: 分析データ
            session_name: セッション名 (例: "asia", "europe", "us")
            
        Returns:
            bool: 送信成功の場合はTrue
        """
        now = get_current_utc_time()
        formatted_time = format_time_for_display(now)
        
        # セッション名を日本語に変換
        session_display = {
            "asia": "アジアセッション",
            "europe": "欧州セッション",
            "us": "米国セッション"
        }.get(session_name.lower(), session_name)
        
        content = f"📊 **BTC/USDT {session_display}分析レポート** ({formatted_time})"
        
        embeds = []
        
        # タイムフレームごとの埋め込みを作成
        for timeframe, tf_analysis in analysis_data.items():
            if "error" in tf_analysis:
                logger.error(f"Error in {timeframe} analysis: {tf_analysis['error']}")
                continue
                
            judgment = tf_analysis.get("judgment", "不明")
            
            # 判断に基づいて色を設定
            color = {
                "強い買い": "00FF00",  # 緑
                "弱い買い": "66CC66",  # 薄緑
                "中立": "FFFF00",      # 黄色
                "弱い売り": "FF6666",  # 薄赤
                "強い売り": "FF0000",  # 赤
            }.get(judgment, "808080")  # デフォルトはグレー
            
            embed = {
                "title": f"{timeframe} 分析結果",
                "color": int(color, 16),
                "fields": [
                    {
                        "name": "判断",
                        "value": judgment,
                        "inline": True
                    },
                    {
                        "name": "見通し",
                        "value": tf_analysis.get("outlook", "情報なし"),
                        "inline": False
                    },
                    {
                        "name": "根拠",
                        "value": tf_analysis.get("reasoning", "情報なし"),
                        "inline": False
                    },
                    {
                        "name": "注意点",
                        "value": tf_analysis.get("advice", "情報なし"),
                        "inline": False
                    }
                ],
                "footer": {
                    "text": f"TRAND Bot • {timeframe} 分析"
                },
                "timestamp": now.isoformat()
            }
            
            embeds.append(embed)
        
        if not embeds:
            logger.error("No valid analysis data to send")
            return False
        
        logger.info(f"Sending {session_name} analysis with {len(embeds)} timeframes")
        return self.send_message(content, embeds)
        
    def send_error_notification(self, error_message: str, exchange_id: str = None, symbol: str = None, details: Dict[str, Any] = None) -> bool:
        """
        エラー通知を送信する
        
        Args:
            error_message: エラーメッセージ
            exchange_id: 取引所ID
            symbol: 通貨ペア
            details: 追加の詳細情報
            
        Returns:
            bool: 送信成功の場合はTrue
        """
        now = get_current_utc_time()
        formatted_time = format_time_for_display(now)
        
        # 取引所と通貨ペアの情報を含めたタイトルを作成
        title_parts = []
        if exchange_id:
            title_parts.append(f"取引所: {exchange_id.upper()}")
        if symbol:
            title_parts.append(f"通貨ペア: {symbol}")
            
        title_suffix = f" ({', '.join(title_parts)})" if title_parts else ""
        content = f"⚠️ **TRAND Bot エラー通知** ({formatted_time})"
        
        # 基本的なエラー情報
        embed = {
            "title": f"エラーが発生しました{title_suffix}",
            "description": error_message,
            "color": int("FF0000", 16),  # 赤色
            "timestamp": now,  # datetimeオブジェクトをそのまま渡す
            "fields": []
        }
        
        # 追加情報があればフィールドに追加
        if details:
            for key, value in details.items():
                if value is not None:
                    # 追加情報が複雑なオブジェクトの場合はJSON形式に変換
                    if isinstance(value, (dict, list)):
                        try:
                            value_str = json.dumps(value, indent=2, ensure_ascii=False)
                        except:
                            value_str = str(value)
                    else:
                        value_str = str(value)
                        
                    embed["fields"].append({
                        "name": key,
                        "value": f"```{value_str}```" if len(value_str) > 20 else value_str,
                        "inline": False
                    })
        
        # フォールバック情報を追加
        if exchange_id:
            embed["footer"] = {
                "text": f"TRAND Bot • フォールバック取引所を試行中"
            }
        
        logger.info(f"Sending error notification: {error_message}")
        return self.send_message(content, [embed])
