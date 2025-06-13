"""
テクニカル分析モジュール
"""
import pandas as pd
import numpy as np
import talib
import pandas_ta as ta
from typing import Dict, List, Optional, Union, Tuple, Any
import json

from .utils.logger import setup_logger
from .config import TECHNICAL_INDICATORS

logger = setup_logger("analyzer")

class TechnicalAnalyzer:
    """テクニカル分析を行うクラス"""
    
    def __init__(self, ohlcv_data: pd.DataFrame = None):
        """
        初期化
        
        Args:
            ohlcv_data: OHLCV データフレーム
        """
        self.data = ohlcv_data
        self.indicators = {}
        self.signals = {}
        
    def set_data(self, ohlcv_data: pd.DataFrame) -> None:
        """
        分析対象のデータを設定
        
        Args:
            ohlcv_data: OHLCV データフレーム
        """
        self.data = ohlcv_data
        # データ設定時にシグナルとインジケーターをリセット
        self.indicators = {}
        self.signals = {}
        
    def calculate_all_indicators(self) -> Dict[str, Any]:
        """
        すべてのテクニカル指標を計算
        
        Returns:
            Dict[str, Any]: 計算されたテクニカル指標
        """
        if self.data is None or self.data.empty:
            logger.error("No data available for indicator calculation")
            return {}
            
        try:
            # SMA（単純移動平均）
            for period in TECHNICAL_INDICATORS["sma"]:
                self.indicators[f"sma_{period}"] = self.data['close'].rolling(window=period).mean()
                
            # EMA（指数移動平均）
            for period in TECHNICAL_INDICATORS["ema"]:
                self.indicators[f"ema_{period}"] = self.data['close'].ewm(span=period, adjust=False).mean()
                
            # RSI（相対力指数）
            period = TECHNICAL_INDICATORS["rsi"]
            delta = self.data['close'].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            
            avg_gain = gain.rolling(window=period).mean()
            avg_loss = loss.rolling(window=period).mean()
            
            rs = avg_gain / avg_loss
            self.indicators["rsi"] = 100 - (100 / (1 + rs))
            
            # MACD（移動平均収束拡散法）
            macd_config = TECHNICAL_INDICATORS["macd"]
            exp1 = self.data['close'].ewm(span=macd_config["fast"], adjust=False).mean()
            exp2 = self.data['close'].ewm(span=macd_config["slow"], adjust=False).mean()
            macd = exp1 - exp2
            signal = macd.ewm(span=macd_config["signal"], adjust=False).mean()
            histogram = macd - signal
            
            self.indicators["macd"] = macd
            self.indicators["macd_signal"] = signal
            self.indicators["macd_hist"] = histogram
            
            # ボリンジャーバンド
            bb_config = TECHNICAL_INDICATORS["bbands"]
            period = bb_config["period"]
            std = bb_config["std"]
            
            middle_band = self.data['close'].rolling(window=period).mean()
            std_dev = self.data['close'].rolling(window=period).std()
            
            upper_band = middle_band + (std_dev * std)
            lower_band = middle_band - (std_dev * std)
            
            self.indicators["bb_upper"] = upper_band
            self.indicators["bb_middle"] = middle_band
            self.indicators["bb_lower"] = lower_band
            
            logger.info(f"Successfully calculated all indicators")
            return self.indicators
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {str(e)}")
            return {}
            
    def generate_signals(self) -> Dict[str, str]:
        """
        各指標のシグナルを生成
        
        Returns:
            Dict[str, str]: インジケーターごとのシグナル（BUY, SELL, NEUTRAL）
        """
        if not self.indicators:
            self.calculate_all_indicators()
            
        if not self.indicators:
            return {}
            
        try:
            signals = {}
            
            # EMAs クロスオーバーシグナル (短期と長期)
            if "ema_9" in self.indicators and "ema_55" in self.indicators:
                ema_short = self.indicators["ema_9"].iloc[-2:].values
                ema_long = self.indicators["ema_55"].iloc[-2:].values
                
                if ema_short[-1] > ema_long[-1] and ema_short[-2] <= ema_long[-2]:
                    signals["ema_cross"] = "BUY"
                elif ema_short[-1] < ema_long[-1] and ema_short[-2] >= ema_long[-2]:
                    signals["ema_cross"] = "SELL"
                else:
                    signals["ema_cross"] = "NEUTRAL"
            
            # RSIシグナル
            if "rsi" in self.indicators:
                rsi = self.indicators["rsi"].iloc[-1]
                
                if rsi < 30:
                    signals["rsi"] = "BUY"  # 買われすぎ
                elif rsi > 70:
                    signals["rsi"] = "SELL"  # 売られすぎ
                else:
                    signals["rsi"] = "NEUTRAL"
            
            # MACDシグナル
            if "macd" in self.indicators and "macd_signal" in self.indicators:
                macd = self.indicators["macd"].iloc[-2:].values
                signal = self.indicators["macd_signal"].iloc[-2:].values
                
                if macd[-1] > signal[-1] and macd[-2] <= signal[-2]:
                    signals["macd"] = "BUY"  # ゴールデンクロス
                elif macd[-1] < signal[-1] and macd[-2] >= signal[-2]:
                    signals["macd"] = "SELL"  # デッドクロス
                else:
                    signals["macd"] = "NEUTRAL"
            
            # ボリンジャーバンドシグナル
            if all(k in self.indicators for k in ["bb_upper", "bb_middle", "bb_lower"]):
                close = self.data['close'].iloc[-1]
                upper = self.indicators["bb_upper"].iloc[-1]
                lower = self.indicators["bb_lower"].iloc[-1]
                
                if close < lower:
                    signals["bbands"] = "BUY"  # 下限を下回る（買い）
                elif close > upper:
                    signals["bbands"] = "SELL"  # 上限を上回る（売り）
                else:
                    signals["bbands"] = "NEUTRAL"
            
            # 総合シグナル（単純多数決）
            buy_count = sum(1 for s in signals.values() if s == "BUY")
            sell_count = sum(1 for s in signals.values() if s == "SELL")
            
            if buy_count > sell_count:
                signals["overall"] = "BUY"
            elif sell_count > buy_count:
                signals["overall"] = "SELL"
            else:
                signals["overall"] = "NEUTRAL"
            
            self.signals = signals
            logger.info(f"Generated signals: {json.dumps(signals)}")
            
            return signals
            
        except Exception as e:
            logger.error(f"Error generating signals: {str(e)}")
            return {"error": str(e)}
    
    def get_market_summary(self) -> Dict[str, Any]:
        """
        市場サマリーを取得
        
        Returns:
            Dict[str, Any]: 市場サマリー情報
        """
        if self.data is None or self.data.empty:
            return {}
            
        try:
            current_price = self.data['close'].iloc[-1]
            prev_price = self.data['close'].iloc[-2]
            price_change = current_price - prev_price
            price_change_pct = (price_change / prev_price) * 100
            
            # 過去24時間（またはデータフレーム期間）の値動き
            high_24h = self.data['high'].iloc[-24:].max() if len(self.data) >= 24 else self.data['high'].max()
            low_24h = self.data['low'].iloc[-24:].min() if len(self.data) >= 24 else self.data['low'].min()
            volume_24h = self.data['volume'].iloc[-24:].sum() if len(self.data) >= 24 else self.data['volume'].sum()
            
            # トレンド判定
            sma20 = self.data['close'].rolling(window=20).mean().iloc[-1] if len(self.data) >= 20 else None
            sma50 = self.data['close'].rolling(window=50).mean().iloc[-1] if len(self.data) >= 50 else None
            
            if sma20 and sma50:
                if current_price > sma20 > sma50:
                    trend = "強い上昇トレンド"
                elif current_price > sma20 and sma20 < sma50:
                    trend = "反発上昇の可能性"
                elif current_price < sma20 and sma20 > sma50:
                    trend = "調整の可能性"
                else:
                    trend = "下降トレンド"
            else:
                trend = "データ不足でトレンド判定不可"
                
            return {
                "current_price": current_price,
                "price_change": price_change,
                "price_change_pct": price_change_pct,
                "high_24h": high_24h,
                "low_24h": low_24h,
                "volume_24h": volume_24h,
                "trend": trend
            }
            
        except Exception as e:
            logger.error(f"Error generating market summary: {str(e)}")
            return {"error": str(e)}
    
    def analyze_timeframe(self, timeframe: str) -> Dict[str, Any]:
        """
        特定のタイムフレームの分析結果を取得
        
        Args:
            timeframe: 分析対象のタイムフレーム
            
        Returns:
            Dict[str, Any]: 分析結果
        """
        self.calculate_all_indicators()
        signals = self.generate_signals()
        summary = self.get_market_summary()
        
        # 最後の数値を取り出す
        last_indicators = {}
        for name, series in self.indicators.items():
            if not series.empty:
                last_indicators[name] = round(series.iloc[-1], 2)
        
        return {
            "timeframe": timeframe,
            "signals": signals,
            "indicators": last_indicators,
            "summary": summary
        }
