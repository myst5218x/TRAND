"""
TRANDアプリケーションのメインモジュール
"""
import os
import sys
import time
import schedule
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from .config import TRADING_INTERVALS, NOTIFICATION_TIMES, validate_config
from .data_fetcher import DataFetcher
from .analyzer import TechnicalAnalyzer
from .gpt_analyzer import GPTAnalyzer
from .notifier import DiscordNotifier
from .utils.logger import setup_logger
from .utils.time_utils import get_current_utc_time, determine_current_session, is_notification_time

logger = setup_logger("main")

class TradingBot:
    """メインのトレーディングボットクラス"""
    
    def __init__(self):
        """初期化"""
        self.data_fetcher = DataFetcher(exchange_id="bybit", symbol="BTC/USDT")
        self.tech_analyzer = TechnicalAnalyzer()
        self.gpt_analyzer = GPTAnalyzer()
        self.notifier = DiscordNotifier()
        
    def run_analysis(self) -> Dict[str, Any]:
        """
        すべてのタイムフレームの分析を実行
        
        Returns:
            Dict[str, Any]: 分析結果と技術分析データ
        """
        analysis_results = {}
        tech_analysis = {}
        
        try:
            # 複数のタイムフレームのデータを取得
            logger.info(f"Fetching data for timeframes: {TRADING_INTERVALS}")
            timeframe_data = self.data_fetcher.fetch_multi_timeframe_data(TRADING_INTERVALS)
            
            if not timeframe_data:
                logger.error("Failed to fetch any timeframe data")
                return {"error": "データ取得に失敗しました"}
                
            # 各タイムフレームごとにテクニカル分析
            for timeframe, ohlcv_data in timeframe_data.items():
                logger.info(f"Performing technical analysis for {timeframe}")
                self.tech_analyzer.set_data(ohlcv_data)
                tech_analysis[timeframe] = self.tech_analyzer.analyze_timeframe(timeframe)
            
            # GPT分析を試行
            gpt_analysis = {}
            try:
                logger.info("Performing GPT analysis for all timeframes")
                gpt_analysis = self.gpt_analyzer.analyze_multi_timeframe(tech_analysis)
            except Exception as gpt_error:
                logger.warning(f"GPT分析に失敗しましたが、技術分析のみで継続します: {str(gpt_error)}")
                # GPT分析なしでも続行
            
            # 結果を統合
            for timeframe in TRADING_INTERVALS:
                if timeframe in tech_analysis:
                    # GPT分析があればそれを使用、なければ技術分析のみ
                    if timeframe in gpt_analysis:
                        analysis_results[timeframe] = gpt_analysis[timeframe]
                    else:
                        # 技術分析のみのフォールバック結果を作成
                        signals = tech_analysis[timeframe].get("signals", {})
                        trend = tech_analysis[timeframe].get("summary", {}).get("trend", "不明")
                        
                        # シグナルから判断を決定
                        judgment = "中立"
                        if signals.get("overall", "") == "BUY":
                            judgment = "弱い買い"
                        elif signals.get("overall", "") == "STRONG_BUY":
                            judgment = "強い買い"
                        elif signals.get("overall", "") == "SELL":
                            judgment = "弱い売り"
                        elif signals.get("overall", "") == "STRONG_SELL":
                            judgment = "強い売り"
                        
                        analysis_results[timeframe] = {
                            "judgment": judgment,
                            "outlook": f"{timeframe}のトレンドは{trend}です。GPT分析は利用できません。",
                            "reasoning": "技術的指標のみに基づく判断です。",
                            "advice": "詳細な分析はできませんが、テクニカル指標の総合判断に従ってください。"
                        }
            
            return {"results": analysis_results, "tech_data": tech_analysis}
            
        except Exception as e:
            logger.exception(f"Error in run_analysis: {str(e)}")
            return {"error": str(e)}
            
    def send_notification(self) -> bool:
        """
        分析結果の通知を送信
        
        Returns:
            bool: 送信成功の場合はTrue
        """
        try:
            # 現在のセッションを判定
            session = determine_current_session()
            logger.info(f"Current trading session: {session}")
            
            # 分析を実行
            analysis_data = self.run_analysis()
            
            if "error" in analysis_data:
                error_msg = f"分析中にエラーが発生しました: {analysis_data['error']}"
                logger.error(error_msg)
                return self.notifier.send_error_notification(
                    error_msg,
                    exchange_id=self.data_fetcher.exchange_id,
                    symbol=self.data_fetcher.symbol
                )
            
            # 分析結果を取得
            analysis_results = analysis_data.get("results", {})
            
            if not analysis_results:
                logger.error("No analysis results available to send")
                return self.notifier.send_error_notification(
                    "分析結果が利用できません",
                    exchange_id=self.data_fetcher.exchange_id,
                    symbol=self.data_fetcher.symbol
                )
                
            # Discord通知を送信
            success = self.notifier.send_market_analysis(analysis_results, session)
            
            if success:
                logger.info(f"Successfully sent {session} market analysis notification")
            else:
                logger.error(f"Failed to send {session} market analysis notification")
                
            return success
            
        except Exception as e:
            logger.exception(f"Error in send_notification: {str(e)}")
            error_msg = f"通知送信中にエラーが発生しました: {str(e)}"
            self.notifier.send_error_notification(
                error_msg,
                exchange_id=self.data_fetcher.exchange_id,
                symbol=self.data_fetcher.symbol,
                details={"エラータイプ": type(e).__name__}
            )
            return False
            
    def schedule_notifications(self) -> None:
        """通知スケジュールを設定"""
        for time_str in NOTIFICATION_TIMES:
            logger.info(f"Scheduling notification at {time_str} UTC")
            schedule.every().day.at(time_str).do(self.send_notification)
            
        logger.info("All notifications scheduled successfully")
        
    def run_scheduled(self) -> None:
        """スケジュールに従って実行"""
        self.schedule_notifications()
        
        logger.info("Starting scheduled execution. Press Ctrl+C to exit.")
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # 1分ごとにスケジュールをチェック
        except KeyboardInterrupt:
            logger.info("Scheduled execution stopped by user")
            
    def run_once(self) -> None:
        """1回だけ実行（テスト用）"""
        logger.info("Running single analysis and notification")
        success = self.send_notification()
        if success:
            logger.info("Notification sent successfully")
        else:
            logger.error("Failed to send notification")


def main():
    """メインエントリポイント"""
    try:
        # 設定の検証
        if not validate_config():
            logger.error("Invalid configuration. Please check your .env file and API keys.")
            sys.exit(1)
            
        bot = TradingBot()
        
        # コマンドライン引数で動作を制御
        if len(sys.argv) > 1 and sys.argv[1] == "--once":
            bot.run_once()
        else:
            bot.run_scheduled()
            
    except Exception as e:
        logger.exception(f"Unhandled exception in main: {str(e)}")
        
        # 設定されていればエラー通知も送信
        try:
            notifier = DiscordNotifier()
            error_details = {
                "エラータイプ": type(e).__name__,
                "発生時刻": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "システム情報": f"Python {sys.version.split()[0]}"
            }
            notifier.send_error_notification(
                f"アプリケーションで重大なエラーが発生しました: {str(e)}",
                details=error_details
            )
        except Exception as notify_error:
            logger.error(f"エラー通知の送信に失敗しました: {str(notify_error)}")
            pass
        
        sys.exit(1)


if __name__ == "__main__":
    main()
