# SunTV Deploy Skill

MoonTV 完整部署 Skill — 包含 Next.js 14 项目初始化、电视直播（CCTV+卫视）功能开发、自动换源机制、常见 Bug 修复、Docker 部署全流程。

## 功能覆盖

- ✅ MoonTV 项目初始化（Next.js 14 + Tailwind CSS + TypeScript）
- ✅ 电视直播功能开发（Artplayer + Hls.js）
- ✅ 自动换源机制（HLS 错误监听 + 手动换源按钮）
- ✅ 直播源获取与维护（M3U 解析）
- ✅ 常见错误修复（Artplayer/HLS/Next.js Suspense）
- ✅ Docker 部署 + NSSM Windows 服务注册
- ✅ 进程管理与端口占用处理

## 使用方法

将此 SKILL.md 放入 WorkBuddy `~/.workbuddy/skills/` 目录，或在对话中直接引用。

触发词：`部署 MoonTV`、`搭建电视直播`、`moontv 部署`、`电视直播功能开发`

## 目录结构

```
suntv-skill/
├── SKILL.md        # 完整部署流程
└── README.md       # 本文件
```

## 作者

sunt6633 — 2026-05-02
