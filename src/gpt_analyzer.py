"""
GPTを活用したトレード分析モジュール
"""
import json
import time
from typing import Dict, List, Any, Optional
import openai

from .utils.logger import setup_logger
from .config import OPENAI_API_KEY

logger = setup_logger("gpt_analyzer")

class GPTAnalyzer:
    """ChatGPT Turboを活用した市場分析を行うクラス"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初期化
        
        Args:
            api_key: OpenAI API Key (デフォルトはconfig.pyから取得)
        """
        self.api_key = api_key or OPENAI_API_KEY
        openai.api_key = self.api_key
        
    def _create_prompt(self, market_data: Dict[str, Any], timeframe: str) -> str:
        """
        GPTへの分析プロンプトを作成する
        
        Args:
            market_data: 市場データと指標
            timeframe: タイムフレーム
            
        Returns:
            str: 構築されたプロンプト
        """
        # データを抽出して読みやすくフォーマット
        current_price = market_data.get("summary", {}).get("current_price", "N/A")
        price_change = market_data.get("summary", {}).get("price_change", "N/A")
        price_change_pct = market_data.get("summary", {}).get("price_change_pct", "N/A")
        trend = market_data.get("summary", {}).get("trend", "不明")
        
        signals = market_data.get("signals", {})
        indicators = market_data.get("indicators", {})
        
        prompt = f"""あなたは暗号資産のトレードアドバイザーです。以下の{timeframe}時間足のビットコイン（BTC/USDT）の市場データを分析し、簡潔なトレード判断を日本語で提供してください。

【市場データ】
- 現在価格: {current_price} USDT
- 価格変動: {price_change} USDT ({price_change_pct:.2f}%)
- 全体トレンド: {trend}

【テクニカル指標】
"""
        
        # 指標情報を追加
        for name, value in indicators.items():
            prompt += f"- {name}: {value}\n"
            
        prompt += "\n【シグナル】\n"
        
        # シグナル情報を追加
        for name, signal in signals.items():
            prompt += f"- {name}: {signal}\n"
            
        prompt += """
以上のデータに基づいて、現在のトレード判断（強い買い、弱い買い、中立、弱い売り、強い売り）とその理由を3-4行程度で簡潔に説明してください。
特に重要な指標や、短期・中期の見通しについて言及してください。
必ず以下のフォーマットで回答してください：

判断: [強い買い/弱い買い/中立/弱い売り/強い売り]
見通し: [100文字以内の簡潔な市場分析]
根拠: [100文字以内のテクニカル指標に基づく根拠]
注意点: [トレーダーへの簡潔なアドバイス]
"""
        
        return prompt
        
    def analyze_market(self, market_data: Dict[str, Any], timeframe: str) -> Dict[str, str]:
        """
        市場データをGPTで分析し、トレード判断を取得する
        
        Args:
            market_data: 市場データと指標
            timeframe: タイムフレーム
            
        Returns:
            Dict[str, str]: GPTによる分析結果
        """
        if not self.api_key:
            logger.error("OpenAI API key is not configured")
            return {
                "error": "APIキーが設定されていません",
                "judgment": "エラー",
                "outlook": "APIキーが設定されていないため分析できません",
                "reasoning": "",
                "advice": "環境変数 OPENAI_API_KEY を設定してください"
            }
            
        prompt = self._create_prompt(market_data, timeframe)
        
        try:
            # 3回までリトライ
            for attempt in range(3):
                try:
                    logger.info(f"Sending request to OpenAI API for {timeframe} analysis")
                    
                    response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "あなたはプロのトレーダーで、暗号資産市場の分析を行います。"},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.5,  # 創造性と一貫性のバランス
                        max_tokens=300,   # 回答の長さ制限
                    )
                    
                    # レスポンスからテキスト部分を抽出
                    analysis_text = response.choices[0].message.content.strip()
                    
                    # 分析テキストをパースして構造化
                    result = self._parse_analysis(analysis_text)
                    
                    logger.info(f"Successfully received GPT analysis for {timeframe}")
                    return result
                    
                except Exception as e:
                    if attempt < 2:  # 2回目までは再試行
                        logger.warning(f"API error: {str(e)}. Retrying in 2 seconds...")
                        time.sleep(2)
                    else:
                        raise
            
        except Exception as e:
            logger.error(f"Error analyzing market with GPT: {str(e)}")
            return {
                "error": str(e),
                "judgment": "エラー",
                "outlook": "API呼び出し中にエラーが発生しました",
                "reasoning": str(e),
                "advice": "しばらく待ってから再試行してください"
            }
    
    def _parse_analysis(self, analysis_text: str) -> Dict[str, str]:
        """
        GPTの分析テキストをパースして構造化データに変換
        
        Args:
            analysis_text: GPTからの分析テキスト
            
        Returns:
            Dict[str, str]: 構造化された分析結果
        """
        result = {
            "judgment": "不明",
            "outlook": "",
            "reasoning": "",
            "advice": ""
        }
        
        try:
            # 行ごとに分割して各セクションを解析
            lines = analysis_text.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                if line.startswith("判断:"):
                    result["judgment"] = line[3:].strip()
                elif line.startswith("見通し:"):
                    result["outlook"] = line[4:].strip()
                elif line.startswith("根拠:"):
                    result["reasoning"] = line[3:].strip()
                elif line.startswith("注意点:"):
                    result["advice"] = line[4:].strip()
            
        except Exception as e:
            logger.error(f"Error parsing GPT analysis: {str(e)}")
            result["error"] = f"分析テキストのパースに失敗しました: {str(e)}"
            
        return result
        
    def analyze_multi_timeframe(self, all_market_data: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, str]]:
        """
        複数のタイムフレームのデータを分析する
        
        Args:
            all_market_data: タイムフレームごとの市場データ
            
        Returns:
            Dict[str, Dict[str, str]]: タイムフレームごとの分析結果
        """
        results = {}
        
        for timeframe, market_data in all_market_data.items():
            analysis = self.analyze_market(market_data, timeframe)
            results[timeframe] = analysis
            # APIレート制限を考慮して短い待機時間を挟む
            time.sleep(1)
            
        return results
