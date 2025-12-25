#!/usr/bin/env python3
import os
import json
import zipfile
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.scf.v20180416 import scf_client, models

# 从环境变量获取配置（对应GitHub Secrets）
SECRET_ID = os.environ.get("TENCENT_SECRET_ID")
SECRET_KEY = os.environ.get("TENCENT_SECRET_KEY")
REGION = os.environ.get("TENCENT_REGION", "ap-shanghai")
FUNCTION_NAME = os.environ.get("TENCENT_FUNCTION_NAME")

def zip_directory(folder_path, output_path):
    """将当前目录打包为zip文件，排除.git和脚本自身"""
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            # 排除.git目录和部署脚本本身
            dirs[:] = [d for d in dirs if d not in ['.git']]
            for file in files:
                if file in ['deploy_with_sdk.py', 'code.zip']:
                    continue
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, folder_path)
                zipf.write(file_path, arcname)
    print(f"✅ 代码已打包: {output_path}")

def main():
    if not all([SECRET_ID, SECRET_KEY, FUNCTION_NAME]):
        print("❌ 环境变量 TENCENT_SECRET_ID, TENCENT_SECRET_KEY, TENCENT_FUNCTION_NAME 必须设置")
        return

    # 1. 初始化客户端
    cred = credential.Credential(SECRET_ID, SECRET_KEY)
    http_profile = HttpProfile()
    http_profile.endpoint = "scf.tencentcloudapi.com"
    client_profile = ClientProfile()
    client_profile.httpProfile = http_profile
    client = scf_client.ScfClient(cred, REGION, client_profile)

    # 2. 打包代码
    zip_path = "code.zip"
    zip_directory(".", zip_path)
    
    # 读取zip文件为base64
    with open(zip_path, 'rb') as f:
        zip_content = f.read()

    # 3. 尝试更新函数（假设函数已存在）
    try:
        req = models.UpdateFunctionCodeRequest()
        req.FunctionName = FUNCTION_NAME
        req.Handler = "index.main_handler"
        req.ZipFile = zip_content
        
        client.UpdateFunctionCode(req)
        print(f"✅ 函数代码更新成功: {FUNCTION_NAME}")
        operation = "更新"
    except Exception as e:
        # 如果更新失败，尝试创建新函数
        if "ResourceNotFound.Function" in str(e):
            print("ℹ️ 函数不存在，尝试创建...")
            try:
                req = models.CreateFunctionRequest()
                req.FunctionName = FUNCTION_NAME
                req.Runtime = "Python3.7"
                req.Handler = "index.main_handler"
                req.Code = models.Code()
                req.Code.ZipFile = zip_content
                req.Type = "Web"  # Web函数类型，支持函数URL
                req.MemorySize = 128
                req.Timeout = 30
                req.Namespace = "default"
                
                client.CreateFunction(req)
                print(f"✅ 函数创建成功: {FUNCTION_NAME}")
                operation = "创建"
            except Exception as create_e:
                print(f"❌ 函数创建失败: {create_e}")
                return
        else:
            print(f"❌ 函数更新失败: {e}")
            return
    
    # 4. 配置函数URL（如果不存在则创建）
    try:
        url_req = models.CreateFunctionUrlConfigRequest()
        url_req.FunctionName = FUNCTION_NAME
        url_req.AuthType = "NONE"  # 测试用，生产环境建议改为 "TRUE"
        url_req.Qualifier = "$LATEST"
        
        client.CreateFunctionUrlConfig(url_req)
        print("✅ 函数URL配置成功")
    except Exception as url_e:
        if "ResourceInUse.FunctionUrlConfig" in str(url_e):
            print("ℹ️ 函数URL已存在，跳过创建")
        else:
            print(f"⚠️ 函数URL配置异常（可忽略）: {url_e}")
    
    # 5. 获取函数URL信息（验证）
    try:
        get_url_req = models.GetFunctionUrlConfigRequest()
        get_url_req.FunctionName = FUNCTION_NAME
        get_url_req.Qualifier = "$LATEST"
        resp = client.GetFunctionUrlConfig(get_url_req)
        print(f"🌐 函数URL: {resp.FunctionUrl}")
    except Exception as get_e:
        print(f"⚠️ 获取函数URL失败: {get_e}")
    
    # 清理
    if os.path.exists(zip_path):
        os.remove(zip_path)
    
    print(f"🎉 部署流程完成 ({operation}函数)")

if __name__ == "__main__":
    main()
