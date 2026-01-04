# -*- coding: utf-8 -*-
"""
腾讯云云函数（SCF）- 新闻情绪判断API
Web函数类型，监听 0.0.0.0:9000
"""

import json
import logging
import os
from typing import Dict, Any

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
        
        request = CommonRequest()
        request.set_domain(ALIYUN_ENDPOINT)
        request.set_version('2020-06-29')
        request.set_action_name('GetSaChGeneral')
        request.set_method('POST')
        request.add_body_params('ServiceCode', 'alinlp')
        request.add_body_params('Text', text)
        
        response = client.do_action_with_exception(request)
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


def parse_request(request: Any) -> Dict[str, Any]:
    """
    解析HTTP请求
    
    Args:
        request: SCF Web函数的request对象
        
    Returns:
        解析后的请求数据字典
    """
    try:
        # 获取请求方法
        method = request.get('requestContext', {}).get('http', {}).get('method', 'GET')
        
        # 获取请求体
        body = request.get('body', '')
        if isinstance(body, str):
            try:
                body_data = json.loads(body) if body else {}
            except json.JSONDecodeError:
                body_data = {}
        else:
            body_data = body
        
        # 获取请求路径
        path = request.get('requestContext', {}).get('http', {}).get('path', '/')
        
        return {
            'method': method,
            'body': body_data,
            'path': path,
            'headers': request.get('headers', {})
        }
    except Exception as e:
        logger.error(f"解析请求失败: {str(e)}")
        return {
            'method': 'GET',
            'body': {},
            'path': '/',
            'headers': {}
        }


def create_response(status_code: int, body: Dict[str, Any], headers: Dict[str, str] = None) -> Dict[str, Any]:
    """
    创建HTTP响应
    
    Args:
        status_code: HTTP状态码
        body: 响应体（字典）
        headers: 响应头（可选）
        
    Returns:
        SCF Web函数响应格式
    """
    if headers is None:
        headers = {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
    
    return {
        'statusCode': status_code,
        'headers': headers,
        'body': json.dumps(body, ensure_ascii=False)
    }


def main_handler(request: Any, context: Any) -> Dict[str, Any]:
    """
    云函数主入口
    
    Args:
        request: HTTP请求对象
        context: 函数上下文对象
        
    Returns:
        HTTP响应对象
    """
    try:
        # 解析请求
        req_data = parse_request(request)
        method = req_data['method']
        body = req_data['body']
        
        # 处理OPTIONS请求（CORS预检）
        if method == 'OPTIONS':
            return create_response(200, {'message': 'OK'})
        
        # 只处理POST请求
        if method != 'POST':
            return create_response(405, {
                'error': 'Method not allowed',
                'message': '只支持POST请求'
            })
        
        # 检查必需参数
        if not body or 'text' not in body:
            return create_response(400, {
                'error': 'Missing parameter',
                'message': '请求体中必须包含text字段'
            })
        
        text = body['text']
        
        # 验证text参数
        if not isinstance(text, str) or not text.strip():
            return create_response(400, {
                'error': 'Invalid parameter',
                'message': 'text字段必须是非空字符串'
            })
        
        # 调用情感分析API
        logger.info(f"分析文本: {text[:50]}...")
        result = call_aliyun_sentiment_api(text)
        
        # 构建响应
        response_body = {
            'sentiment': result['sentiment'],
            'confidence': result['confidence'],
            'text': text
        }
        
        return create_response(200, response_body)
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON解析错误: {str(e)}")
        return create_response(400, {
            'error': 'Invalid JSON',
            'message': '请求体必须是有效的JSON格式'
        })
    except Exception as e:
        logger.error(f"处理请求时发生错误: {str(e)}")
        return create_response(500, {
            'error': 'Internal server error',
            'message': f'服务器内部错误: {str(e)}'
        })


# Web函数需要监听端口（SCF会自动处理，这里仅作说明）
if __name__ == '__main__':
    # 本地测试代码
    test_request = {
        'requestContext': {
            'http': {
                'method': 'POST',
                'path': '/'
            }
        },
        'body': json.dumps({'text': '今天天气真好，心情很愉快！'})
    }
    
    result = main_handler(test_request, None)
    print(json.dumps(result, ensure_ascii=False, indent=2))
