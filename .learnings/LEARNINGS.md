# Learnings

Corrections, insights, and knowledge gaps captured during development.

**Categories**: correction | insight | knowledge_gap | best_practice

---

## [LRN-20260515-001] correction

**Logged**: 2026-05-15T15:10:00+08:00
**Priority**: high
**Status**: pending
**Area**: config

### Summary
说话太AI了，被孙先生纠正

### Details
孙先生指出我说话太像AI：爱用emoji、老说"哈哈"、总是同意对方观点。应该更像朋友聊天，自然随意。

### Suggested Action
- 少用emoji
- 别老说"哈哈"
- 不要总是同意，可以有不同意见
- 说话像人，不要像AI

### Metadata
- Source: user_feedback
- Tags: communication, style

---

## [LRN-20260515-002] best_practice

**Logged**: 2026-05-15T15:10:00+08:00
**Priority**: high
**Status**: pending
**Area**: infra

### Summary
升级Node等操作别随便停gateway，断线是大忌

### Details
孙先生明确说"你可别随便重启gateway，断线是大忌"。gateway断线会导致所有连接中断。

### Suggested Action
- 需要重启gateway前必须确认不会影响当前连接
- 非必要不重启
- 如果必须重启，先通知孙先生

### Metadata
- Source: user_feedback
- Tags: gateway, stability

---

## [LRN-20260515-003] knowledge_gap

**Logged**: 2026-05-15T15:10:00+08:00
**Priority**: medium
**Status**: pending
**Area**: config

### Summary
不要往C盘装东西，C盘空间紧张会影响系统稳定性

### Details
孙先生明确说"不要往C盘装东西"。C盘空间紧张会影响系统稳定性。OpenClaw装在F盘，数据在D盘。

### Suggested Action
- 所有新软件/文件默认安装到D盘或F盘
- 检查安装路径，避免默认C盘

### Metadata
- Source: user_feedback
- Tags: windows, disk-space

---

## [LRN-20260515-004] best_practice

**Logged**: 2026-05-15T15:10:00+08:00
**Priority**: medium
**Status**: pending
**Area**: config

### Summary
被锁的文件要先停进程再替换

### Details
之前尝试替换被OpenClaw锁定的JS文件失败，报错"另一个进程正在使用"。后来通过停止gateway再替换解决。

### Suggested Action
- 替换被锁定的文件前，先停止相关进程
- 或者使用PowerShell的Stop-Process强制结束

### Metadata
- Source: error
- Tags: windows, file-locking

---

## [LRN-20260515-005] best_practice

**Logged**: 2026-05-15T15:10:00+08:00
**Priority**: medium
**Status**: pending
**Area**: config

### Summary
发博客用blog-publish skill，配置在D:\for workbuddy\skills\blog-publish

### Details
WordPress博客配置：
- URL: http://43.226.44.9
- 用户名: sunt
- 应用密码: bp5RZDmsomAPFlmqk0xenYko
- API: /wp-json/wp/v2/posts

### Suggested Action
- 发博客时直接用这个配置
- 已经复制到sunt-repo的skills目录

### Metadata
- Source: conversation
- Tags: wordpress, blog, publishing

---

