#!/usr/bin/env python3
import os, json, zipfile, base64, sys
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.scf.v20180416 import scf_client, models

# 从环境变量获取配置
SECRET_ID = os.environ.get("TENCENT_SECRET_ID")
SECRET_KEY = os.environ.get("TENCENT_SECRET_KEY")
REGION = os.environ.get("TENCENT_REGION", "ap-shanghai")
FUNCTION_NAME = os.environ.get("TENCENT_FUNCTION_NAME")

def zip_directory():
    """打包当前目录为zip文件"""
    zip_path = "code.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk("."):
            # 排除不需要的文件
            if '.git' in root: continue
            for file in files:
                if file.endswith(('.zip', '.pyc')): continue
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, ".")
                zipf.write(file_path, arcname)
    print("✅ 代码打包完成")
    return zip_path

def main():
    # 验证环境变量
    if not all([SECRET_ID, SECRET_KEY, FUNCTION_NAME]):
        print("❌ 错误：请设置 TENCENT_SECRET_ID, TENCENT_SECRET_KEY, TENCENT_FUNCTION_NAME")
        sys.exit(1)
    
    # 初始化客户端
    cred = credential.Credential(SECRET_ID, SECRET_KEY)
    http_profile = HttpProfile(endpoint="scf.tencentcloudapi.com")
    client_profile = ClientProfile(httpProfile=http_profile)
    client = scf_client.ScfClient(cred, REGION, client_profile)
    
    # 打包代码
    zip_path = zip_directory()
    with open(zip_path, 'rb') as f:
        zip_content = f.read()
    
    # 尝试更新函数，如果不存在则创建
    try:
        # 先尝试获取函数信息
        try:
            req_get = models.GetFunctionRequest()
            req_get.FunctionName = FUNCTION_NAME
            client.GetFunction(req_get)
            print(f"ℹ️ 函数 {FUNCTION_NAME} 已存在，更新代码...")
            
            # 更新代码
            req_update = models.UpdateFunctionCodeRequest()
            req_update.FunctionName = FUNCTION_NAME
            req_update.Handler = "index.main_handler"
            req_update.ZipFile = zip_content
            client.UpdateFunctionCode(req_update)
            print("✅ 函数代码更新成功")
            
        except Exception as e:
            if "ResourceNotFound.Function" in str(e):
                print(f"ℹ️ 函数 {FUNCTION_NAME} 不存在，创建新函数...")
                # 创建函数
                req_create = models.CreateFunctionRequest()
                req_create.FunctionName = FUNCTION_NAME
                req_create.Runtime = "Python3.7"
                req_create.Handler = "index.main_handler"
                req_create.Code = models.Code(ZipFile=zip_content)
                req_create.Type = "Web"  # Web函数支持函数URL
                req_create.MemorySize = 128
                req_create.Timeout = 30
                client.CreateFunction(req_create)
                print("✅ 函数创建成功")
            else:
                raise e
        
        # 配置函数URL
        try:
            url_req = models.CreateFunctionUrlConfigRequest()
            url_req.FunctionName = FUNCTION_NAME
            url_req.AuthType = "NONE"  # 测试用，生产环境建议改为 "TRUE"
            url_req.Qualifier = "$LATEST"
            client.CreateFunctionUrlConfig(url_req)
            print("✅ 函数URL配置成功")
        except Exception as url_e:
            if "ResourceInUse" in str(url_e):
                print("ℹ️ 函数URL已存在")
            else:
                print(f"⚠️ URL配置警告: {url_e}")
        
        # 获取函数URL
        try:
            get_url_req = models.GetFunctionUrlConfigRequest()
            get_url_req.FunctionName = FUNCTION_NAME
            get_url_req.Qualifier = "$LATEST"
            resp = client.GetFunctionUrlConfig(get_url_req)
            print(f"🌐 你的函数URL: {resp.FunctionUrl}")
        except:
            print("ℹ️ 可在腾讯云控制台查看函数URL")
        
    except Exception as e:
        print(f"❌ 部署失败: {e}")
        sys.exit(1)
    finally:
        # 清理
        if os.path.exists(zip_path):
            os.remove(zip_path)
    
    print("🎉 部署完成！")

if __name__ == "__main__":
    main()
