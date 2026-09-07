# 本地 Pi 模型配置增删规范

当用户在测速完成后要求“帮我增/删模型”或“将测速出的优质模型加到配置里”时查阅本文件。

## 配置路径

默认修改本机 Pi 的全局配置文件：

```text
~/.pi/agent/models.json
```

目标位置为该 JSON 中 `providers["360"].models` 数组。

## 新增模型字段规范

新增模型时，基于网关 `/model/info` 或 models.dev 补全字段：

```json
{
  "id": "360/glm-5.3",
  "name": "GLM 5.3 (360)",
  "reasoning": true,
  "input": ["text", "image"],
  "contextWindow": 128000,
  "maxTokens": 8192
}
```

- `id`：使用实测速度最优的完整模型 ID（含 `360/`、`m1/` 等前缀）。
- `name`：规范化的人类可读名称，并可标注部署节点。
- `reasoning`：模型是否支持思考链推理（布尔值）。
- `input`：支持的多模态能力（包含 `image` 则需声明）。
- `contextWindow` 与 `maxTokens`：根据模型规格填写准确整数。

## 删除模型规范

直接从 `providers["360"].models` 数组中移除对应 `id` 的对象，保存文件后提示用户重启或刷新 Pi 会话生效。
