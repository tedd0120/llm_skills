# Teams 群组成员数据与 API 参考

本文件供需要通过 Python 代码直接调用底层接口或解析输出 JSON 结构时查阅。

## Python SDK 接口

```python
from scripts.fetch_group_members import fetch_group_members, fetch_group_members_union
```

### 1. `fetch_group_members`（单群抓取）

```python
fetch_group_members(
    group_code: str,
    authorization: str = None,
    verbose: bool = True,
    save_path: str = None,
    fill_virtual_superiors: bool = True,
    generate_html: bool = True
) -> list[dict]
```

| 参数 | 类型 | 说明 |
|:---|:---|:---|
| `group_code` | str | 群组代码（必填） |
| `authorization` | str | 授权令牌（可选，默认读取 `.env`） |
| `verbose` | bool | 是否打印成员列表（默认 `True`） |
| `save_path` | str | JSON 保存路径（可选） |
| `fill_virtual_superiors` | bool | 是否自动补齐虚拟上级节点（默认 `True`） |
| `generate_html` | bool | 是否生成交互式 HTML 组织树（默认 `True`） |

### 2. `fetch_group_members_union`（多群并集去重）

```python
fetch_group_members_union(
    group_codes: list[str],
    authorization: str = None,
    verbose: bool = True,
    save_path: str = None,
    generate_html: bool = True
) -> list[dict]
```

---

## 成员数据字段定义（JSON）

每个成员对象包含以下标准化字段：

| 字段 | 类型 | 说明 |
|:---|:---|:---|
| `name` | str | 姓名 |
| `id` | str | 员工工号 |
| `userName` | str | 登录账号 |
| `role` | int | 角色编码（1=群主, 4=普通成员） |
| `role_desc` | str | 角色描述 |
| `deptName` | str | 部门名称 |
| `deptCode` | str | 部门编码 |
| `superior` | str | 直属上级工号/标识 |
| `bpName` | str | 对应 HRBP |
| `workPlaceName` | str | 办公地点 |
| `sex` / `sex_desc` | int / str | 性别与描述 |
| `portrait_url` | str | 头像 URL |
| `is_virtual` | bool | 是否为补齐的虚拟上级节点 |

## 组织架构树 HTML 交互特性

生成的 HTML 单文件具备：
1. **分栏逐级钻取**：首列展示按规模排序的业务线，后续列展示下级。
2. **常驻路径条**：顶栏显示选中节点的完整管理层级链路。
3. **全局搜索定位**：搜索命中项平滑定位并展开对应链路。
4. **底部详情条**：常驻呈现当前成员完整组织属性。
