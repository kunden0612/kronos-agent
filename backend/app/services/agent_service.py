import re
import json
import logging
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime

logger = logging.getLogger(__name__)


class IntentRecognizer:
    """意图识别器 - 识别用户输入的意图并提取参数"""
    
    def __init__(self):
        self.patterns = {
            'predict': [
                r'(预测|预估|分析|走势)('
                r'.*?)(\d+个?交易?日?|明天|下周|未来|短期|长期)?',
                r'(茅台|AAPL|苹果|特斯拉|TSLA|BTC|比特币|ETH|以太坊)',
            ],
            'help': [
                r'^(帮助|help|怎么|如何|使用|说明)',
            ],
            'history': [
                r'^(历史|记录|查看.*历史|过去)',
            ],
        }
        
        self.symbol_map = {
            '茅台': '600519.SH',
            '贵州茅台': '600519.SH',
            'AAPL': 'AAPL',
            '苹果': 'AAPL',
            'TSLA': 'TSLA',
            '特斯拉': 'TSLA',
            'BTC': 'BTC/USDT',
            '比特币': 'BTC/USDT',
            'ETH': 'ETH/USDT',
            '以太坊': 'ETH/USDT',
        }
    
    def extract_symbol(self, message: str) -> Optional[str]:
        """从消息中提取资产代码"""
        for key, symbol in self.symbol_map.items():
            if key in message:
                return symbol
        
        import re
        match = re.search(r'[A-Z]{2,5}/?[A-Z]{0,4}', message)
        if match:
            return match.group()
        
        return None
    
    def extract_pred_len(self, message: str) -> int:
        """提取预测天数"""
        if '明天' in message or '1天' in message:
            return 1
        elif '下周' in message or '一周' in message:
            return 5
        elif '一月' in message or '一个月' in message:
            return 20
        
        import re
        match = re.search(r'(\d+)\s*(个?交易?日?|天)', message)
        if match:
            return int(match.group(1))
        
        return 5
    
    def recognize(self, message: str) -> Tuple[str, Dict[str, Any]]:
        """识别意图并返回参数"""
        message_lower = message.lower()
        
        if any(re.search(pattern, message_lower) for pattern in self.patterns['help']):
            return 'help', {}
        
        if any(re.search(pattern, message_lower) for pattern in self.patterns['history']):
            return 'history', {}
        
        if any(re.search(pattern, message_lower) for pattern in self.patterns['predict']):
            symbol = self.extract_symbol(message)
            pred_len = self.extract_pred_len(message)
            
            if symbol:
                return 'predict', {
                    'symbol': symbol,
                    'pred_len': pred_len
                }
            else:
                return 'need_symbol', {}
        
        return 'unknown', {}


class AgentService:
    """简化版 Hermes Agent 服务"""
    
    def __init__(self, kronos_client):
        self.kronos_client = kronos_client
        self.intent_recognizer = IntentRecognizer()
        self.conversations: Dict[str, List[Dict[str, Any]]] = {}
    
    async def process_message(
        self,
        message: str,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """处理用户消息"""
        if not conversation_id:
            conversation_id = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []
        
        self.conversations[conversation_id].append({
            'role': 'user',
            'content': message,
            'timestamp': datetime.now().isoformat()
        })
        
        intent, params = self.intent_recognizer.recognize(message)
        
        response = None
        prediction = None
        
        try:
            if intent == 'help':
                response = self._generate_help_response()
            elif intent == 'need_symbol':
                response = self._generate_need_symbol_response()
            elif intent == 'predict':
                prediction = await self.kronos_client.predict(**params)
                response = self._generate_prediction_response(prediction, params)
            elif intent == 'history':
                response = self._generate_history_response(conversation_id)
            else:
                response = self._generate_unknown_response()
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            response = f"抱歉，处理您的请求时出现错误：{str(e)}"
        
        self.conversations[conversation_id].append({
            'role': 'assistant',
            'content': response,
            'timestamp': datetime.now().isoformat()
        })
        
        return {
            'message': response,
            'conversation_id': conversation_id,
            'timestamp': datetime.now(),
            'prediction': prediction
        }
    
    def _generate_help_response(self) -> str:
        return (
            "您好！我可以帮您预测金融市场走势。\n\n"
            "您可以这样问我：\n"
            "1. 「预测茅台未来5天的走势」\n"
            "2. 「分析AAPL下周的表现」\n"
            "3. 「BTC明天会涨吗？」\n\n"
            "支持的资产：A股（如茅台）、美股（如AAPL）、加密货币（如BTC）"
        )
    
    def _generate_need_symbol_response(self) -> str:
        return (
            "我理解您想要进行预测，但需要您告诉我具体的资产代码。\n\n"
            "您可以这样说：\n"
            "「预测茅台未来5天的走势」\n"
            "「分析AAPL下周的表现」\n"
            "「BTC明天会涨吗？」"
        )
    
    def _generate_prediction_response(self, prediction: Dict[str, Any], params: Dict[str, Any]) -> str:
        symbol = params.get('symbol', '')
        pred_len = params.get('pred_len', 5)
        
        response = f"好的，正在为您预测 {symbol} 未来 {pred_len} 天的走势...\n\n"
        
        if prediction and 'interpretation' in prediction:
            response += prediction['interpretation'] + "\n\n"
        
        if prediction and 'risk_warning' in prediction:
            response += "⚠️ " + prediction['risk_warning']
        
        return response
    
    def _generate_history_response(self, conversation_id: str) -> str:
        if conversation_id not in self.conversations:
            return "暂无历史对话记录。"
        
        history = self.conversations[conversation_id]
        count = len([msg for msg in history if msg.get('role') == 'user'])
        
        return f"本会话共有 {count} 条历史消息。"
    
    def _generate_unknown_response(self) -> str:
        return (
            "抱歉，我不太理解您的请求。\n\n"
            "您可以试试这样说：\n"
            "「预测茅台未来5天的走势」\n"
            "「分析AAPL下周的表现」\n"
            "或者说「帮助」来查看使用说明。"
        )
