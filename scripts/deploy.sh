#!/bin/bash
set -e

echo "开始部署函数: $FUNCTION_NAME"

# 1. 打包代码
zip -r code.zip . -x '*.git*' 'scripts/*'

# 2. 尝试更新函数，如果失败则创建新函数
if tccli scf UpdateFunction \
    --FunctionName "$FUNCTION_NAME" \
    --Region "$REGION" \
    --Handler "index.main_handler" \
    --Runtime "Python3.7" \
    --ZipFile "fileb://code.zip" \
    --Environment '{"Variables": {}}' 2>/dev/null; then
    echo "✅ 函数更新成功"
else
    echo "函数不存在，尝试创建..."
    tccli scf CreateFunction \
        --FunctionName "$FUNCTION_NAME" \
        --Region "$REGION" \
        --Runtime "Python3.7" \
        --Handler "index.main_handler" \
        --Type "Web" \
        --MemorySize 128 \
        --Timeout 30 \
        --ZipFile "fileb://code.zip" \
        --Environment '{"Variables": {}}'
    echo "✅ 函数创建成功"
fi

# 3. 配置函数URL (匿名访问，生产环境建议改为 TRUE)
echo "配置函数URL..."
tccli scf CreateFunctionUrlConfig \
    --FunctionName "$FUNCTION_NAME" \
    --Region "$REGION" \
    --AuthType "NONE" \
    --Qualifier "\$LATEST" 2>/dev/null || \
    echo "函数URL可能已存在，将继续..."

# 4. 清理
rm -f code.zip
echo "🎉 部署流程完成"
