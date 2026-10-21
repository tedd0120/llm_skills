# assistant-ui 选型与接入

## 适用场景与核心原语

将 [assistant-ui](https://www.assistant-ui.com/docs)（仓库 [assistant-ui/assistant-ui](https://github.com/assistant-ui/assistant-ui)）用于 AI 聊天会话、流式消息渲染与工具调用生成式 UI（Generative UI）：
- **对话原语**：`Thread`（消息流、自动平滑滚动、重试与分支切换）、`Message`（消息体与代码块高亮）、`Composer`（输入框、附件与语音输入）、`ThreadList`（历史会话管理）、`ActionBar`（复制、重新生成等操作栏）。
- **生成式 UI**：将模型 Tool Call 参数、运行状态与返回值映射为自定义交互组件，支持人工确认（Human-in-the-loop）。

## 安装与依赖选择

1. **CLI 初始化**（自动识别项目的 Radix UI 或 Base UI 配置并生成组件至 `components/assistant-ui/`）：
   ```bash
   npx assistant-ui@latest init
   ```
2. **按后端协议安装桥接包**（配合核心包 `@assistant-ui/react` 与可选的 `@assistant-ui/react-markdown`）：
   - Vercel AI SDK：`@assistant-ui/ai-sdk`
   - LangGraph：`@assistant-ui/react-langgraph`
   - 自定义流式接口：`@assistant-ui/react-data-stream`

## 接入范式

### 1. 挂载运行时（Runtime Provider）
```tsx
"use client";

import { AssistantRuntimeProvider } from "@assistant-ui/react";
import { useChatRuntime } from "@assistant-ui/ai-sdk";
import { Thread } from "@/components/assistant-ui/thread";

export function AssistantPage() {
  const runtime = useChatRuntime({ api: "/api/chat" });
  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <main className="h-screen w-full">
        <Thread />
      </main>
    </AssistantRuntimeProvider>
  );
}
```

### 2. 绑定 Tool Call 生成式 UI
```tsx
import { makeAssistantToolUI } from "@assistant-ui/react";

export const WeatherToolUI = makeAssistantToolUI({
  toolName: "get_weather",
  render: ({ args, result, status }) => (
    <WeatherCard location={args.location} data={result} loading={status.type === "running"} />
  ),
});
```

## 样式与状态适配

- 生成的对话组件默认使用 shadcn/ui 语义变量（`bg-background`、`text-foreground`、`border`），直接跟随主应用主题。
- 业务请求头、会话持久化与鉴权回调统一通过 `runtime` 构造参数注入。

## 按需资料

- 官方文档与示例：[Documentation](https://www.assistant-ui.com/docs)、[Examples](https://www.assistant-ui.com/examples)
