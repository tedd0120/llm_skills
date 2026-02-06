# LLM Skills

面向大语言模型 (LLM) 的插件化金融数据获取工具集。通过标准化的 "Skill" 架构，为 AI 助手提供实时、准确的金融数据获取能力。

## 🌟 核心特性

- **插件化架构**：每个数据源/功能独立为 "Skill"，易于扩展和维护。
- **多源支持**：整合了 `akshare`, `yfinance`, `Alpha Vantage` 等多种主流金融数据接口。
- **覆盖广泛**：包含 A股、港股、美股、基金、现货黄金及财经新闻。
- **OpenSpec 驱动**：完整的开发工作流支持，确保 AI 助手开发的高效与规范。

## 🛠️ 快速开始

### 1. 克隆项目 & 安装依赖

```bash
git clone https://github.com/tedd0120/llm_skills.git
cd llm_skills

# 建议使用虚拟环境
python -m venv venv
source venv/bin/activate  # Windows 使用: venv\Scripts\activate

pip install -r requirements.txt
# 或者直接安装核心依赖:
pip install akshare yfinance python-dotenv requests
```

### 2. 配置环境变量

在项目根目录下创建 `.env` 文件，配置必要的 API Key：

```env
ALPHA_VANTAGE_API_KEY=your_api_key_here
```

## 📂 项目结构

```text
llm_skills/
├── .agent/
│   ├── skills/          # 核心功能插件 (Skills)
│   │   ├── finance-data-china-a-stock/
│   │   ├── ...
│   └── workflows/       # OpenSpec 工作流定义 (openspec-cn)
├── data/                # 示例数据与缓存
├── openspec/            # 项目规范与变更提案 (Proposal)
├── AGENTS.md            # AI 助手操作指南
└── README.md            # 本项目说明
```

## 📊 已实现的 Skills

| Skill | 核心功能 | 数据源 | 路径 |
|:---|:---|:---|:---|
| `china-a-stock` | A股 K线、实时快照 | akshare | [SKILL.md](file:///.agent/skills/finance-data-china-a-stock/SKILL.md) |
| `hk-stock` | 港股行情 | akshare / yfinance | [SKILL.md](file:///.agent/skills/finance-data-hk-stock/SKILL.md) |
| `us-stock` | 美股行情、基本面 | yfinance | [SKILL.md](file:///.agent/skills/finance-data-us-stock/SKILL.md) |
| `fund` | 基金净值、ETF | akshare | [SKILL.md](file:///.agent/skills/finance-data-fund/SKILL.md) |
| `shanghai-gold` | 沪金现货 | akshare | [SKILL.md](file:///.agent/skills/finance-data-shanghai-gold/SKILL.md) |
| `london-gold` | COMEX、XAU/USD | yfinance | [SKILL.md](file:///.agent/skills/finance-data-london-gold/SKILL.md) |
| `news` | 财经新闻、市场情绪 | akshare / AV | [SKILL.md](file:///.agent/skills/finance-data-news/SKILL.md) |

## 🚀 开发者工作流

本项目遵循 **OpenSpec** 规范进行开发。当需要添加新功能或修改现有架构时，请使用以下流程：

1. **提案 (Proposal)**: 使用 `/openspec-proposal` 发起新功能提案。
2. **实施 (Apply)**: 提案批准后，使用 `/openspec-apply` 执行变更。
3. **归档 (Archive)**: 部署完成后，使用 `/openspec-archive` 更新文档并归档。

## ⚠️ 注意事项

- **API 限制**：Alpha Vantage 免费版 API 每分钟限 5 次，每天限 25 次。
- **数据延迟**：行情数据通常有 15 分钟左右的延迟，具体取决于数据源。
- **合规性**：请确保在遵守数据源服务条款的前提下使用本项目。
