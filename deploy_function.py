# deploy_function.py
import os
import json
import base64
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.scf.v20180416 import scf_client, models

def main():
    # 1. 从环境变量读取认证信息（GitHub Actions Secrets会自动注入）
    secret_id = os.environ.get('TENCENT_SECRET_ID')
    secret_key = os.environ.get('TENCENT_SECRET_KEY')
    
    if not secret_id or not secret_key:
        print("❌ 错误：未找到 TENCENT_SECRET_ID 或 TENCENT_SECRET_KEY 环境变量")
        exit(1)
    
    # 2. 配置信息 - ⚠️ 请务必修改为你自己的值！
    REGION = 'ap-guangzhou'  # 重要：修改为你的函数地域，例如 ap-shanghai
    FUNCTION_NAME = 'news-sentiment-analyzer'  # 重要：修改为你的函数名，确保与控制台完全一致
    
    # 3. 认证
    cred = credential.Credential(secret_id, secret_key)
    
    # 4. 初始化客户端
    httpProfile = HttpProfile()
    httpProfile.endpoint = 'scf.tencentcloudapi.com'
    clientProfile = ClientProfile()
    clientProfile.httpProfile = httpProfile
    client = scf_client.ScfClient(cred, REGION, clientProfile)
    
    # 5. 读取并编码部署包（假设与脚本同目录存在 function.zip）
    zip_filename = 'function.zip'
    if not os.path.exists(zip_filename):
        print(f"❌ 错误：找不到部署包文件 {zip_filename}")
        exit(1)
        
    with open(zip_filename, 'rb') as f:
        zip_file = base64.b64encode(f.read()).decode('utf-8')
    
    # 6. 构建并发送更新请求
    req = models.UpdateFunctionCodeRequest()
    req.FunctionName = FUNCTION_NAME
    req.ZipFile = zip_file
    
    try:
        print(f"🚀 正在更新函数 {FUNCTION_NAME} 的代码...")
        resp = client.UpdateFunctionCode(req)
        print('🎉 函数代码更新成功！')
        print('请求ID:', resp.RequestId)
    except Exception as e:
        print('❌ 更新失败:', e)
        exit(1)

if __name__ == '__main__':
    main()
