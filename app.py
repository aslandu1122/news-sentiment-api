# -*- coding: utf-8 -*-
"""
腾讯云云函数（SCF）- 新闻情绪判断API
Web函数类型，使用Python内置http.server监听 0.0.0.0:9000
"""

import json
import logging
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Dict, Any
from urllib.parse import urlparse

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 阿里云API配置（从环境变量读取）
ALIYUN_ACCESS_KEY_ID = os.environ.get('ALIYUN_ACCESS_KEY_ID', '')
ALIYUN_ACCESS_KEY_SECRET = os.environ.get('ALIYUN_ACCESS_KEY_SECRET', '')
ALIYUN_ENDPOINT = os.environ.get('ALIYUN_ENDPOINT', 'alinlp.cn-hangzhou.aliyuncs.com')
USE_MOCK = os.environ.get('USE_MOCK', 'true').lower() == 'true'  # 默认使用模拟


def call_aliyun_sentiment_api(text: str) -> Dict[str, Any]:
    """
    调用阿里云情感分析API
    
    Args:
        text: 待分析的文本
        
    Returns:
        包含sentiment和confidence的字典
    """
    try:
        # 如果配置了模拟模式或没有配置密钥，使用模拟逻辑
        if USE_MOCK or not ALIYUN_ACCESS_KEY_ID or not ALIYUN_ACCESS_KEY_SECRET:
            logger.info("使用模拟情感分析API")
            return mock_sentiment_analysis(text)
        
        # 实际调用阿里云API
        from aliyunsdkcore.client import AcsClient
        from aliyunsdkcore.request import CommonRequest
        
        client = AcsClient(ALIYUN_ACCESS_KEY_ID, ALIYUN_ACCESS_KEY_SECRET, 'cn-hangzhou')
        
        request_obj = CommonRequest()
        request_obj.set_domain(ALIYUN_ENDPOINT)
        request_obj.set_version('2020-06-29')
        request_obj.set_action_name('GetSaChGeneral')
        request_obj.set_method('POST')
        request_obj.add_body_params('ServiceCode', 'alinlp')
        request_obj.add_body_params('Text', text)
        
        response = client.do_action_with_exception(request_obj)
        result = json.loads(response.decode('utf-8'))
        
        # 解析阿里云返回结果
        if result.get('Data'):
            data = json.loads(result['Data'])
            sentiment = data.get('result', {}).get('sentiment', '中性')
            confidence = float(data.get('result', {}).get('confidence', 0.5))
            
            # 统一情绪标签格式
            sentiment_map = {
                'positive': '积极',
                'negative': '消极',
                'neutral': '中性',
                '积极': '积极',
                '消极': '消极',
                '中性': '中性'
            }
            sentiment = sentiment_map.get(sentiment.lower(), '中性')
            
            return {
                'sentiment': sentiment,
                'confidence': confidence
            }
        else:
            raise Exception("阿里云API返回数据格式错误")
            
    except ImportError:
        logger.warning("阿里云SDK未安装，使用模拟API")
        return mock_sentiment_analysis(text)
    except Exception as e:
        logger.error(f"调用阿里云API失败: {str(e)}")
        # API调用失败时回退到模拟逻辑
        return mock_sentiment_analysis(text)


def mock_sentiment_analysis(text: str) -> Dict[str, Any]:
    """
    模拟情感分析逻辑（用于测试）
    
    Args:
        text: 待分析的文本
        
    Returns:
        包含sentiment和confidence的字典
    """
    # 简单的关键词匹配逻辑
    positive_keywords = ['好', '棒', '优秀', '成功', '胜利', '高兴', '满意', '喜欢', '爱', 
                        '赞', '支持', '推荐', '美好', '幸福', '快乐', '开心', '积极']
    negative_keywords = ['坏', '差', '失败', '失望', '讨厌', '恨', '糟糕', '问题', '困难',
                        '危机', '危险', '损失', '错误', '负面', '消极', '悲伤', '痛苦']
    
    text_lower = text.lower()
    positive_count = sum(1 for keyword in positive_keywords if keyword in text)
    negative_count = sum(1 for keyword in negative_keywords if keyword in text)
    
    # 计算情绪和置信度
    if positive_count > negative_count:
        sentiment = '积极'
        confidence = min(0.7 + (positive_count - negative_count) * 0.1, 0.95)
    elif negative_count > positive_count:
        sentiment = '消极'
        confidence = min(0.7 + (negative_count - positive_count) * 0.1, 0.95)
    else:
        sentiment = '中性'
        confidence = 0.6
    
    return {
        'sentiment': sentiment,
        'confidence': round(confidence, 2)
    }


def main_handler(request_data: Dict[str, Any], context: Any = None) -> Dict[str, Any]:
    """
    云函数主入口（兼容事件函数格式）
    
    Args:
        request_data: HTTP请求数据
        context: 函数上下文对象（可选）
        
    Returns:
        包含sentiment、confidence和text的字典
    """
    try:
        # 检查必需参数
        if not request_data or 'text' not in request_data:
            return {
                'error': 'Missing parameter',
                'message': '请求体中必须包含text字段'
            }
        
        text = request_data['text']
        
        # 验证text参数
        if not isinstance(text, str) or not text.strip():
            return {
                'error': 'Invalid parameter',
                'message': 'text字段必须是非空字符串'
            }
        
        # 调用情感分析API
        logger.info(f"分析文本: {text[:50]}...")
        result = call_aliyun_sentiment_api(text)
        
        # 构建响应
        return {
            'sentiment': result['sentiment'],
            'confidence': result['confidence'],
            'text': text
        }
        
    except Exception as e:
        logger.error(f"处理请求时发生错误: {str(e)}")
        return {
            'error': 'Internal server error',
            'message': f'服务器内部错误: {str(e)}'
        }


class SentimentHandler(BaseHTTPRequestHandler):
    """HTTP请求处理器"""
    
    def _set_cors_headers(self):
        """设置CORS响应头"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Content-Type', 'application/json; charset=utf-8')
    
    def do_OPTIONS(self):
        """处理CORS预检请求"""
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()
    
    def do_GET(self):
        """处理GET请求"""
        parsed_path = urlparse(self.path)
        
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()
        
        # 健康检查接口
        if parsed_path.path == '/health':
            response = {'status': 'ok', 'message': '服务正常运行'}
        else:
            # 根路径返回API使用说明
            response = {
                'message': '新闻情绪判断API',
                'usage': {
                    'method': 'POST',
                    'url': '/',
                    'headers': {
                        'Content-Type': 'application/json'
                    },
                    'body': {
                        'text': '待分析的文本内容'
                    },
                    'example': {
                        'text': '今天天气真好，心情很愉快！'
                    }
                },
                'response': {
                    'sentiment': '积极/消极/中性',
                    'confidence': 0.95,
                    'text': '输入文本片段'
                }
            }
        
        self.wfile.write(json.dumps(response, ensure_ascii=False, indent=2).encode('utf-8'))
    
    def do_POST(self):
        """处理POST请求"""
        try:
            # 读取请求体
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self.send_response(400)
                self._set_cors_headers()
                self.end_headers()
                response = {
                    'error': 'Invalid request',
                    'message': '请求体不能为空'
                }
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
                return
            
            body = self.rfile.read(content_length)
            
            # 解析JSON
            try:
                request_data = json.loads(body.decode('utf-8'))
            except json.JSONDecodeError:
                self.send_response(400)
                self._set_cors_headers()
                self.end_headers()
                response = {
                    'error': 'Invalid JSON',
                    'message': '请求体必须是有效的JSON格式'
                }
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
                return
            
            # 调用主处理函数
            result = main_handler(request_data)
            
            # 判断响应状态码
            if 'error' in result:
                if result['error'] == 'Missing parameter' or result['error'] == 'Invalid parameter':
                    status_code = 400
                else:
                    status_code = 500
            else:
                status_code = 200
            
            # 发送响应
            self.send_response(status_code)
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            logger.error(f"处理请求时发生错误: {str(e)}")
            self.send_response(500)
            self._set_cors_headers()
            self.end_headers()
            response = {
                'error': 'Internal server error',
                'message': f'服务器内部错误: {str(e)}'
            }
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
    
    def log_message(self, format, *args):
        """重写日志方法，使用自定义logger"""
        logger.info("%s - - [%s] %s" % (self.client_address[0], self.log_date_time_string(), format % args))


def run_server(port=9000):
    """启动HTTP服务器"""
    server_address = ('0.0.0.0', port)
    httpd = HTTPServer(server_address, SentimentHandler)
    logger.info(f'服务器启动，监听端口 {port}')
    httpd.serve_forever()


if __name__ == '__main__':
    # 启动服务器
    run_server(9000)
