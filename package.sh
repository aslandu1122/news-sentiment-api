#!/bin/bash
# 打包脚本 - 用于创建SCF部署包

echo "开始打包SCF函数..."

# 清理旧的打包文件
rm -f function.zip

# 创建ZIP文件，排除不必要的文件
zip -r function.zip . \
    -x "*.git*" \
    -x "*__pycache__*" \
    -x "*.pyc" \
    -x "*.pyo" \
    -x "*.pyd" \
    -x ".DS_Store" \
    -x "package.sh" \
    -x "README.md" \
    -x "*.md"

# 确保scf_bootstrap有执行权限
chmod +x scf_bootstrap

echo "打包完成！文件：function.zip"
echo "请将此文件上传到腾讯云SCF控制台"

