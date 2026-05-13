---
name: feishu-connect
description: 将飞书（Feishu）接入 OpenClaw 的完整流程。适用于中国版飞书（feishu.cn）自建应用配置，包括权限导入、机器人能力、事件订阅、WebSocket 长连接、配对批准等。当用户提到"飞书接通"、"飞书机器人"、"飞书渠道"时使用此 skill。
---

# 飞书接入 OpenClaw

## 流程概览

1. 飞书开放平台创建企业自建应用
2. 配置权限
3. 启用机器人能力
4. 发布应用
5. OpenClaw 侧配置
6. 配对批准

## 详细步骤

### 1. 创建应用

打开 https://open.feishu.cn/app → 创建企业自建应用 → 填写应用名称和描述

### 2. 权限导入

进入应用 → 权限管理 → 批量导入，添加以下权限：

```
contact:contact.base:readonly
contact:user.employee_id:readonly
im:message:send_as_bot
im:message.receive_v1
```

### 3. 启用机器人能力

应用能力 → 机器人 → 启用

### 4. 事件订阅（⚠️ 关键步骤）

**必须按正确顺序操作：**

1. 先在 OpenClaw 侧运行 `openclaw channels add` 配置飞书（生成 WebSocket 连接信息）
2. 再回到飞书开放平台配置事件订阅

事件订阅配置：
- 接收方式：**使用长连接接收事件**
- 添加事件：`im.message.receive_v1`（接收消息）

**注意：** WebSocket 模式下不需要填写回调地址。

### 5. 发布应用

版本管理 → 创建版本 → 填写更新说明 → 申请发布

发布后才能在飞书中使用机器人。

### 6. OpenClaw 侧配置

```bash
openclaw channels add
# 选择 Feishu/Lark
# 填入 App ID 和 App Secret
# 选择 WebSocket 模式
# 选择 feishu.cn（中国版）
# 群聊策略选 Open
# DM 策略选 pairing
```

### 7. 配对批准

首次私聊机器人会返回配对码。管理员运行：

```bash
openclaw pairing approve feishu <配对码>
```

## 常见问题

### 权限不足
确保已发布应用版本，未发布的应用权限不生效。

### 事件订阅配置顺序错误
必须先在 OpenClaw 配置好飞书渠道，再在飞书配事件订阅。否则 WebSocket 连接会失败。

### 选择错误的域名
中国版飞书选 `feishu.cn`，国际版选 `larksuite.com`。

### 群聊不响应
检查群聊策略是否为 Open，且机器人已被添加到群中。

## 参考

- 飞书开放平台：https://open.feishu.cn
- OpenClaw 文档：https://docs.openclaw.ai
