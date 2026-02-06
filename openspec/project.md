# 项目 上下文

## 目的
为 LLM (大语言模型) 提供标准化的金融数据获取接口 (Skills)，使其能够辅助用户进行数据分析、行情查看和财经新闻检索。

## 技术栈
- **语言**: Python 3.8+
- **数据源库**: `akshare`, `yfinance`
- **基础库**: `pandas`, `requests`, `python-dotenv`
- **规范体系**: OpenSpec

## 项目约定

### 代码风格
- 遵循 PEP 8 规范。
- 变量和函数命名使用小写字母加下划线 (`snake_case`)。
- 关键函数需包含 docstring，说明参数和返回值。

### 架构模式
- **Skill 模式**: 每个功能模块封装在 `.agent/skills/` 下，包含脚本、示例和 `SKILL.md` 文档。
- **数据持久化**: 临时或示例数据保存在 `data/` 目录下。

### 测试策略
- 开发者在应用变更前需运行相关 Skill 的脚本进行功能验证。

### Git工作流
- 遵循 OpenSpec 工作流：Proposal -> Apply -> Archive。

## 领域上下文
- 金融数据包含股票 (A/H/US)、基金、贵金属及财经新闻。
- 数据获取需考虑延迟限制、API 配额限制 (如 Alpha Vantage)。

## 重要约束
- 严禁在代码中硬编码 API Key，必须通过 `.env` 加载。
- 保持 Skill 接口的简洁性，易于 AI 助手解析和调用。

## 外部依赖
- [AkShare](https://akshare.akfamily.xyz/): A股、基金等数据。
- [yfinance](https://github.com/ranaroussi/yfinance): 美股、港股、外汇/贵金属。
- [Alpha Vantage](https://www.alphavantage.co/): 新闻情绪分析。
