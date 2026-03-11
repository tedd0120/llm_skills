# 设计：Cookie 路径修复

## 文件修改

### 1. `xiaohongshu-scraper/scripts/login_xhs.py`

```python
# 旧代码 (第 36-40 行)
self.auth_state_path = os.environ.get(
    "XHS_AUTH_STATE",
    ".claude/skills/xiaohongshu-scraper/scripts/xhs_auth.json",
)
Path(self.auth_state_path).parent.mkdir(parents=True, exist_ok=True)

# 新代码
SCRIPT_DIR = Path(__file__).parent.resolve()
self.auth_state_path = os.environ.get(
    "XHS_AUTH_STATE",
    str(SCRIPT_DIR / "xhs_auth.json"),
)
```

### 2. `xiaohongshu-fetch/scripts/fetch_xhs.py`

```python
# 旧代码 (第 52-56 行)
self.auth_state_path = os.environ.get(
    'XHS_AUTH_STATE',
    '.claude/skills/xiaohongshu-scraper/scripts/xhs_auth.json'
)
Path(self.auth_state_path).parent.mkdir(parents=True, exist_ok=True)

# 新代码
SCRIPT_DIR = Path(__file__).parent.resolve()
SKILLS_DIR = SCRIPT_DIR.parent.parent  # scripts -> xiaohongshu-fetch -> skills
self.auth_state_path = os.environ.get(
    'XHS_AUTH_STATE',
    str(SKILLS_DIR / "xiaohongshu-scraper" / "scripts" / "xhs_auth.json"),
)
```

## 路径计算说明

```
login_xhs.py 位置: .claude/skills/xiaohongshu-scraper/scripts/login_xhs.py
__file__.parent   → .claude/skills/xiaohongshu-scraper/scripts/
+ xhs_auth.json   → .claude/skills/xiaohongshu-scraper/scripts/xhs_auth.json ✅

fetch_xhs.py 位置: .claude/skills/xiaohongshu-fetch/scripts/fetch_xhs.py
__file__.parent   → .claude/skills/xiaohongshu-fetch/scripts/
.parent           → .claude/skills/xiaohongshu-fetch/
.parent           → .claude/skills/
+ xiaohongshu-scraper/scripts/xhs_auth.json → 目标路径 ✅
```

## 清理

删除错误位置的旧 cookie 文件：
```
.claude/skills/xiaohongshu-scraper/.claude/skills/xiaohongshu-scraper/scripts/xhs_auth.json
```
