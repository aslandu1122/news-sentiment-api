# 腾讯云云函数 - 新闻情绪判断API

## 功能说明

这是一个腾讯云Web函数，用于分析新闻文本的情绪。接收POST请求，返回情绪标签（积极/消极/中性）及置信度。

## 部署步骤

1. **创建Web函数**
   - 在腾讯云SCF控制台创建新函数
   - 选择"Web函数"类型
   - 运行环境选择 Python 3.7 或更高版本
   - **注意**：Web函数不需要设置入口函数，会自动执行 `scf_bootstrap` 脚本

2. **准备代码包**
   - 确保包含以下文件：
     - `app.py` - 主程序文件（Flask应用）
     - `scf_bootstrap` - 启动脚本（必须具有执行权限）
     - `requirements.txt` - 依赖项列表
   - 将文件打包成ZIP文件（**重要**：确保 `scf_bootstrap` 在ZIP根目录）

3. **上传代码**
   - 在SCF控制台上传ZIP代码包
   - 或使用SCF CLI工具上传

3. **配置环境变量**（可选）
   - `ALIYUN_ACCESS_KEY_ID`: 阿里云AccessKey ID
   - `ALIYUN_ACCESS_KEY_SECRET`: 阿里云AccessKey Secret
   - `ALIYUN_ENDPOINT`: 阿里云API端点（默认：alinlp.cn-hangzhou.aliyuncs.com）
   - `USE_MOCK`: 是否使用模拟API（true/false，默认true）

4. **获取函数URL**
   - 在函数配置中启用"公网访问"
   - 获取函数URL用于调用

## API使用说明

### 请求格式

**URL**: `https://your-function-url.scf.tencentcs.com/`

**Method**: POST

**Headers**:
```
Content-Type: application/json
```

**Body**:
```json
{
  "text": "今天股市大涨，投资者情绪高涨！"
}
```

### 响应格式

**成功响应** (200):
```json
{
  "sentiment": "积极",
  "confidence": 0.85,
  "text": "今天股市大涨，投资者情绪高涨！"
}
```

**错误响应** (400/500):
```json
{
  "error": "Missing parameter",
  "message": "请求体中必须包含text字段"
}
```

## 测试示例

### 使用curl测试

```bash
curl -X POST https://your-function-url.scf.tencentcs.com/ \
  -H "Content-Type: application/json" \
  -d '{"text": "今天天气真好，心情很愉快！"}'
```

### 使用Python测试

```python
import requests
import json

url = "https://your-function-url.scf.tencentcs.com/"
data = {"text": "今天股市大跌，投资者损失惨重。"}

response = requests.post(url, json=data)
print(json.dumps(response.json(), ensure_ascii=False, indent=2))
```

## 模拟模式

如果未配置阿里云API密钥或设置 `USE_MOCK=true`，函数将使用内置的模拟情感分析逻辑。模拟逻辑基于关键词匹配，适合测试使用。

## 文件说明

- **app.py**: HTTP服务器主文件，使用Python内置http.server，无需外部依赖
- **scf_bootstrap**: 启动脚本，SCF会自动执行此文件启动Web服务
- **index.py**: 保留的事件函数版本（如需要可切换使用）
- **requirements.txt**: Python依赖包列表（可选，仅在使用阿里云API时需要）

## 注意事项

1. **scf_bootstrap 文件必须具有执行权限**
   - 在打包前执行：`chmod +x scf_bootstrap`
   - 或在打包后通过SCF控制台设置

2. **打包ZIP文件时注意事项**
   - 确保 `scf_bootstrap` 位于ZIP根目录
   - 不要包含 `.git`、`__pycache__` 等不必要的文件
   - 建议使用命令行打包：`zip -r function.zip . -x "*.git*" "*__pycache__*"`

3. **Web函数会自动监听 `0.0.0.0:9000` 端口**
   - HTTP服务器已配置监听此端口
   - SCF会自动将HTTP请求转发到此端口

4. **无需外部依赖**：使用Python内置http.server，无需安装Flask等第三方库

5. **函数支持CORS**，可直接在前端调用

6. **建议在生产环境中配置阿里云API密钥**以获得更准确的分析结果

6. **文本长度建议控制在合理范围内**（建议不超过5000字符）

## 故障排查

如果遇到启动错误：
1. 检查 `scf_bootstrap` 文件是否存在且具有执行权限
2. 确认 `app.py` 文件在ZIP根目录
3. 检查 `requirements.txt` 中的依赖是否正确
4. 查看SCF日志获取详细错误信息
