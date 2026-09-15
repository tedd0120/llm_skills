# assistant-ui 选型与接入

## 选型

- 将 [assistant-ui](https://www.assistant-ui.com/docs)（仓库 [assistant-ui/assistant-ui](https://github.com/assistant-ui/assistant-ui)）作为 AI 聊天、智能助手对话与生成式 UI（Generative UI）方案候选。
- 适用场景与核心特性：
  - 对话流式交互：内置打字机流式输出、自动平滑滚动、网络重试、消息分支与撤回编辑。
  - 模块化对话原语：提供 `Thread`（对话流）、`Message`（消息体）、`Composer`（输入框与附件区）、`ThreadList`（历史会话列表）、`ActionBar`（操作工具栏）。
  - 生成式 UI 与工具渲染：将大模型 Tool Call、结构化 JSON 输出映射为可交互的 React 组件；支持人工确认（Human-in-the-loop）交互。
  - 多模态与语音能力：集成语音听写输入、附件上传、富文本渲染与语法高亮代码块。
  - 广泛后端适配：开箱即用支持 Vercel AI SDK、LangGraph、LangChain 及自定义数据流。

## 源码与安装

1. 通过 CLI 自动初始化（适配 shadcn/ui 项目结构）：
   ```bash
   npx assistant-ui@latest init
   ```
   CLI 会根据项目使用的基础库（Base UI 或 Radix UI）生成对应的样式化对话组件到 `components/assistant-ui/`。
2. 安装依赖：
   - 基础渲染包：`@assistant-ui/react`。
   - 后端桥接包（按需选择）：
     - Vercel AI SDK：`@assistant-ui/ai-sdk`
     - LangGraph：`@assistant-ui/react-langgraph`
     - 自定义流式服务：`@assistant-ui/react-data-stream`
     - Markdown 渲染：`@assistant-ui/react-markdown`

## 架构与接入范式

### 1. 运行时接入（Runtime Provider）
在应用外层使用 `AssistantRuntimeProvider` 挂载对应后端的聊天状态：
```tsx
"use client";

import { AssistantRuntimeProvider } from "@assistant-ui/react";
import { useChatRuntime } from "@assistant-ui/ai-sdk";
import { Thread } from "@/components/assistant-ui/thread";

export function AssistantPage() {
  const runtime = useChatRuntime({
    api: "/api/chat",
  });

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <main className="h-screen w-full">
        <Thread />
      </main>
    </AssistantRuntimeProvider>
  );
}
```

### 2. Generative UI 与工具调用绑定
使用 `makeAssistantToolUI` 将模型工具调用参数与前端状态组件连接：
```tsx
import { makeAssistantToolUI } from "@assistant-ui/react";

export const WeatherToolUI = makeAssistantToolUI({
  toolName: "get_weather",
  render: ({ args, result, status }) => {
    return <WeatherCard location={args.location} data={result} loading={status.type === "running"} />;
  },
});
```

## 样式与状态适配

- 界面组件采用 shadcn/ui 风格的 Tailwind CSS 变量（`bg-background`, `text-foreground`, `border`, `rounded` 等），自动跟随主应用明暗主题。
- 对话状态由 `runtime` 统一管理，业务回调与自定义请求头通过 runtime 构造参数传递。
- 弹层、附件抽屉和代码复制按钮遵循已有无障碍规范。

## 按需资料

- 官方文档：[assistant-ui Documentation](https://www.assistant-ui.com/docs)。
- 示例与模板：[assistant-ui Examples](https://www.assistant-ui.com/examples)。
