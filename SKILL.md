---
name: suntv-deploy
description: >
  MoonTV 完整部署 Skill：包含 Next.js 14 项目初始化、电视直播（CCTV+卫视）功能开发、
  自动换源机制、常见 Bug 修复（Artplayer/Hls.js）、Docker 部署全流程。
  当用户说"部署 MoonTV"、"搭建电视直播"、"moontv 部署"、"电视直播功能开发"时触发。
allowed-tools: Bash, Read, Write, Edit, PowerShell, Git
---

# SunTV Deploy Skill

## 概述

MoonTV 是一个基于 **Next.js 14 + Tailwind CSS + TypeScript** 的跨平台影视聚合播放器，
本 skill 覆盖从零部署到电视直播功能完整上线的全过程。

---

## 一、环境要求

| 依赖 | 版本 |
|------|------|
| Node.js | ≥ 18 |
| pnpm | ≥ 8 |
| Git | latest |
| Docker（可选） | ≥ 20 |

---

## 二、项目初始化

```bash
# 克隆项目（以 MoonTV 为例，也可替换为你的 fork）
git clone https://github.com/sunt6633/s.git suntv
cd suntv/src

# 安装依赖
pnpm install

# 启动开发服务器（监听 0.0.0.0，允许局域网访问）
pnpm dev
# → 访问 http://localhost:3000
```

### 关键脚本（`package.json`）

```json
{
  "scripts": {
    "dev": "pnpm gen:runtime && pnpm gen:manifest && next dev -H 0.0.0.0",
    "build": "pnpm gen:runtime && pnpm gen:manifest && next build",
    "start": "next start",
    "gen:runtime": "node scripts/convert-config.js",
    "gen:manifest": "node scripts/generate-manifest.js"
  }
}
```

---

## 三、电视直播功能开发

### 3.1 直播页面 `src/app/live/page.tsx`

核心功能：频道列表 + Artplayer 播放器 + 自动换源 + 手动换源

```tsx
'use client';
import Artplayer from 'artplayer';
import Hls from 'hls.js';
import { useCallback, useEffect, useRef, useState } from 'react';

interface Channel {
  name: string;
  urls: string[];  // 多个源，用于自动换源
}

// 电视频道列表（从 live.zbds.top 每日更新获取最新 M3U）
const channels: Channel[] = [
  {
    name: 'CCTV-13 新闻',
    urls: [
      'http://ali-m-l.cztv.com/channels/lantian/channel21/1080p.m3u8',
      'https://piccpndali.v.myalicdn.com/audio/cctv13_2.m3u8', // 音频备用
    ],
  },
  {
    name: 'CCTV-1 综合',
    urls: [
      'http://39.134.115.163:8080/PLTV/88888888/224/3221226485/10000100000000060000000000009905_0.smil/index.m3u8',
      'http://ali-m-l.cztv.com/channels/lantian/channel01/1080p.m3u8',
    ],
  },
  // ... 添加更多频道
];

export default function LiveTVPage() {
  const artRef = useRef<Artplayer>(null);
  const hlsRef = useRef<Hls>(null);
  const [currentChannel, setCurrentChannel] = useState<Channel>(channels[0]);
  const [currentSourceIndex, setCurrentSourceIndex] = useState(0);
  const [audioOnly, setAudioOnly] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 加载视频源
  const loadSource = useCallback((channel: Channel, sourceIdx: number) => {
    setCurrentSourceIndex(sourceIdx);
    setError(null);
    const url = channel.urls[sourceIdx];
    setAudioOnly(url.includes('/audio/'));

    if (hlsRef.current) {
      hlsRef.current.loadSource(url);
      hlsRef.current.startLoad();
    }
  }, []);

  // 自动换源：HLS 致命错误时自动切换下一个源
  const tryNextSource = useCallback((channel: Channel, currentIdx: number) => {
    const nextIdx = currentIdx + 1;
    if (nextIdx < channel.urls.length) {
      setError(`线路 ${currentIdx + 1} 失败，正在切换到线路 ${nextIdx + 1}...`);
      loadSource(channel, nextIdx);
    } else {
      setError(`${channel.name} 所有线路均不可用，请稍后重试`);
    }
  }, [loadSource]);

  // 手动换源按钮
  const manualSwitchSource = useCallback(() => {
    const nextIdx = (currentSourceIndex + 1) % currentChannel.urls.length;
    loadSource(currentChannel, nextIdx);
  }, [currentChannel, currentSourceIndex, loadSource]);

  // 初始化 Artplayer + Hls.js
  useEffect(() => {
    if (artRef.current) return;

    const art = new Artplayer({
      container: '.artplayer-container',
      url: currentChannel.urls[0],
      type: 'm3u8',
      autoplay: true,
      muted: true,   // 浏览器限制自动播放需先静音
      theme: '#0ea5e9',
      lang: 'zh-cn',
      volume: 0.8,
      cssVar: true,
      controls: [
        {
          name: 'nextSource',
          position: 'right',
          html: `换源(${currentSourceIndex + 1}/${currentChannel.urls.length})`,
          click: manualSwitchSource,
        },
      ],
    });

    // HLS 初始化
    if (Hls.isSupported()) {
      const hls = new Hls({
        enableWorker: true,
        lowLatencyMode: true,
      });
      hlsRef.current = hls;

      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        art.play();
      });

      // 自动换源：致命错误时切换
      hls.on(Hls.Events.ERROR, (_event: any, data: any) => {
        if (data.fatal) {
          console.error('HLS fatal error:', data);
          tryNextSource(currentChannel, currentSourceIndex);
        }
      });

      art.on('ready', () => {
        hls.loadSource(currentChannel.urls[currentSourceIndex]);
        hls.attachMedia(art.video);
      });
    } else if (art.video.canPlayType('application/vnd.apple.mpegurl')) {
      // Safari 原生支持 HLS
      art.video.src = currentChannel.urls[currentSourceIndex];
    }

    artRef.current = art;

    return () => {
      hlsRef.current?.destroy();
      art.destroy();
    };
  }, []);

  // 切换频道
  const switchChannel = (channel: Channel) => {
    setCurrentChannel(channel);
    setCurrentSourceIndex(0);
    loadSource(channel, 0);
  };

  return (
    <div className="flex h-screen bg-black">
      {/* 左侧频道列表 */}
      <div className="w-64 bg-gray-900 overflow-y-auto">
        <div className="p-3 text-white font-bold border-b border-gray-700">
          电视直播
        </div>
        {channels.map((ch) => (
          <div
            key={ch.name}
            className={`p-3 cursor-pointer text-sm ${
              ch.name === currentChannel.name
                ? 'bg-blue-600 text-white'
                : 'text-gray-300 hover:bg-gray-800'
            }`}
            onClick={() => switchChannel(ch)}
          >
            {ch.name}
            {ch.urls[0].includes('/audio/') && (
              <span className="text-yellow-400 ml-1">(音频)</span>
            )}
          </div>
        ))}
      </div>

      {/* 播放器区域 */}
      <div className="flex-1 flex flex-col">
        <div className="artplayer-container flex-1" />
        {audioOnly && (
          <div className="bg-yellow-600 text-white text-center py-1 text-sm">
            ⚠️ 当前为音频源，正在尝试切换视频源...
          </div>
        )}
        {error && (
          <div className="bg-red-600 text-white text-center py-1 text-sm">
            {error}
          </div>
        )}
      </div>
    </div>
  );
}
```

### 3.2 导航栏添加直播入口 `src/components/Sidebar.tsx`

```tsx
const [menuItems, setMenuItems] = useState([
  { icon: Film, label: '电影', href: '/douban?type=movie' },
  { icon: Tv, label: '剧集', href: '/douban?type=tv' },
  { icon: Clover, label: '综艺', href: '/douban?type=show' },
  { icon: Tv, label: '电视直播', href: '/live' },  // ← 放在综艺下方
]);
```

### 3.3 首页移除直播卡片 `src/app/page.tsx`

删除首页的"电视直播"入口 Card，保持首页整洁。

---

## 四、直播源获取与维护

### 4.1 从 M3U 文件提取直播源

```bash
# 下载最新 M3U 播放列表（每日更新）
curl -o iptv4.m3u "https://live.zbds.top/tv/iptv4.m3u"

# 提取 CCTV-13 的所有源
grep -A1 "CCTV-13" iptv4.m3u | grep -v "^--$"
```

### 4.2 已知可用直播源（2026-05-02 验证）

| 频道 | 视频源 | 备注 |
|------|--------|------|
| CCTV-13 | `http://ali-m-l.cztv.com/channels/lantian/channel21/1080p.m3u8` | 视频 |
| CCTV-1 | `http://ali-m-l.cztv.com/channels/lantian/channel01/1080p.m3u8` | 视频 |
| 北京卫视 | `http://112.27.235.94:8000/PLTV/88888888/224/...` | 视频 |
| 其他卫视 | 从 `live.zbds.top` M3U 提取 | 每日更新 |

### 4.3 自动换源机制说明

- **自动换源**：`hls.on(Hls.Events.ERROR)` 监听 fatal 错误 → 自动切换 `urls[]` 下一个源
- **手动换源**：播放器控制栏"换源"按钮，显示 `X/Y` 进度
- **音频源标注**：URL 含 `/audio/` 时在列表标记 `(音频)`，播放器显示黄色警告

---

## 五、常见错误与修复

### Error 1：`art.switchUrl is not a function`

**原因**：Artplayer 无 `switchUrl` 方法
**修复**：改用 `art.url = url` 或重新创建 HLS 实例

```tsx
// ❌ 错误
art.switchUrl(url);

// ✅ 正确
art.url = url;  // 简单场景
// 或重新 loadSource（推荐）
hls.loadSource(url);
hls.startLoad();
```

### Error 2：`useSearchParams() should be wrapped in a suspense boundary`

**原因**：Next.js 14 预渲染检查
**修复**：创建 `layout.tsx` 用 `<Suspense>` 包裹

```tsx
// src/app/live/layout.tsx
import { Suspense } from 'react';

export default function LiveLayout({ children }: { children: React.ReactNode }) {
  return (
    <Suspense fallback={<div className="text-white p-8">加载中...</div>}>
      {children}
    </Suspense>
  );
}
```

### Error 3：CCTV 只有声音/没有图像

**原因**：源是 `/audio/` 音频流，或非视频格式
**修复**：
1. 换用视频源（如 `ali-m-l.cztv.com` 的 `/video/` 路径）
2. 实现自动换源机制
3. 在 UI 标注音频源

### Error 4：`rm: cannot remove '.next/standalone': Device or resource busy`

**原因**：node 进程占用 `.next` 目录
**修复**：

```bash
# 终止占用进程
taskkill //F //IM node.exe

# 然后重新构建
pnpm build
```

### Error 5：ESLint `no-console` 警告

**修复**：移除所有 `console.warn`，改用 `console.error` 或状态管理

```tsx
// ❌ 触发 lint 警告
console.warn('HLS error');

// ✅ 正确
console.error('HLS error:', data);
// 或
setError('HLS error occurred');
```

---

## 六、Docker 部署

### 6.1 构建 Docker 镜像

```dockerfile
# Dockerfile（项目已包含）
FROM node:18-alpine AS builder
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN npm install -g pnpm && pnpm install
COPY . .
RUN pnpm build

FROM node:18-alpine
WORKDIR /app
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/public ./public
EXPOSE 3000
CMD ["node", "server.js"]
```

### 6.2 运行

```bash
docker build -t suntv:latest .
docker run -d -p 3000:3000 --name suntv suntv:latest
```

### 6.3 NSSM 注册为 Windows 服务（可选）

```powershell
# 安装 NSSM
choco install nssm -y

# 注册服务
nssm install MoonTV "C:\Program Files\nodejs\pnpm.cmd" "start"
nssm set MoonTV AppDirectory "D:\moontv\src"
nssm start MoonTV
```

---

## 七、目录结构

```
moontv/
├── src/
│   ├── app/
│   │   ├── live/          # 电视直播页面
│   │   │   ├── page.tsx   # 直播主页面
│   │   │   └── layout.tsx # Suspense 边界
│   │   ├── page.tsx       # 首页（已移除直播卡片）
│   │   └── layout.tsx     # 根布局
│   ├── components/
│   │   └── Sidebar.tsx    # 左侧导航栏（含直播入口）
│   └── ...
├── iptv4.m3u              # 电视直播源列表
├── package.json
├── next.config.js
├── tailwind.config.ts
└── Dockerfile
```

---

## 八、每日维护任务

1. **更新直播源**：重新下载 `https://live.zbds.top/tv/iptv4.m3u` 并提取最新 URL
2. **验证视频源**：检查 CCTV/卫视是否只有声音
3. **构建测试**：`pnpm build` 确保无编译错误
4. **进程管理**：部署前终止占用端口的 node 进程

---

## 触发词

- "部署 MoonTV"
- "搭建电视直播"
- "moontv 部署"
- "电视直播功能开发"
- "Next.js 电视直播"
- "Artplayer Hls.js 直播"
