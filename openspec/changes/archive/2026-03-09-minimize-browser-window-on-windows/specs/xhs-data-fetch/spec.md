## 新增需求

### 需求: Windows 环境下浏览器必须最小化启动

fetch 组件在 Windows 环境下启动浏览器时，必须使用 `--start-minimized` 参数使窗口最小化。

#### 场景: Windows 环境启动

- **当** 在 Windows 环境下启动 Edge 浏览器
- **那么** 必须添加 `--start-minimized` 参数
- **并且** 窗口应以最小化状态启动

#### 场景: 非 Windows 环境启动

- **当** 在 Linux 或其他非 Windows 环境下启动浏览器
- **那么** 不添加 `--start-minimized` 参数
- **并且** 保持现有启动行为
