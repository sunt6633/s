---
name: blog-renovation
description: |
  WordPress博客完整装修技能，包含云服务器+云主机协同工作流程。
  功能：1) 通过REST API自定义CSS美化博客；2) 创建社交分享页面支持一键转发到多平台（头条、抖音、小红书等）。
  当用户要求装修博客、美化网站、添加分享功能、一键转发时使用此技能。
agent_created: true
---

# Blog Renovation Skill

## 概述

此技能用于完整装修WordPress博客，包含两大核心功能：
1. **博客CSS美化**：通过WordPress REST API应用自定义CSS，无需SSH访问
2. **社交分享页面**：创建一键分享到8大平台的页面（头条、抖音、小红书、知乎、微博、QQ空间、快手、微信公众号）

### 精彩亮点：云服务器 + 云主机协同

本技能的一个精彩设计是**云服务器与云主机的协同配合**：
- **云主机**（http://43.226.44.9）：运行WordPress的Web服务器，通过REST API进行操作
- **本地机器**：运行Python脚本，调用REST API，避免直接SSH连接的不稳定性
- **协同优势**：本地脚本 + 远程API = 稳定可靠的操作方式

## WordPress REST API 认证

博客地址：<ADDRESS_REDACTED>
- 用户名：`sunt`
- 应用密码：`bp5RZDmsomAPFlmqk0xenYko`
- REST API基础URL：`http://43.226.44.9/wp-json/wp/v2`

### 认证方式

```python
import requests
from requests.auth import HTTPBasicAuth

# 使用应用密码认证
auth = HTTPBasicAuth('sunt', 'bp5RZDmsomAPFlmqk0xenYko')
BASE_URL = "http://43.226.44.9/wp-json/wp/v2"
```

## 功能一：博客CSS美化

### 工作流程

1. **设计CSS样式**：创建自定义CSS（渐变背景、卡片阴影、现代排版）
2. **通过REST API应用**：使用 `POST /wp/v2/settings` 端点
3. **验证效果**：访问博客首页查看美化效果

### 完整Python脚本

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WordPress博客CSS美化脚本
通过REST API应用自定义CSS，无需SSH访问
"""

import requests
from requests.auth import HTTPBasicAuth
import sys

# WordPress认证信息
WP_URL = "http://43.226.44.9"
WP_USER = "sunt"
WP_APP_PASS = "bp5RZDmsomAPFlmqk0xenYko"

def apply_custom_css(css_file):
    """应用自定义CSS到WordPress博客"""

    # 读取CSS文件
    try:
        with open(css_file, 'r', encoding='utf-8') as f:
            custom_css = f.read()
    except Exception as e:
        print(f"❌ 读取CSS文件失败: {e}")
        return False

    # 构建API请求
    api_url = f"{WP_URL}/wp-json/wp/v2/settings"
    auth = HTTPBasicAuth(WP_USER, WP_APP_PASS)

    # 发送请求
    try:
        response = requests.post(
            api_url,
            json={"custom_css": custom_css},
            auth=auth,
            timeout=30
        )

        if response.status_code == 200:
            print("✅ CSS美化成功应用！")
            print(f"🎨 博客地址：<ADDRESS_REDACTED>
            return True
        else:
            print(f"❌ API请求失败: {response.status_code}")
            print(response.text)
            return False

    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

if __name__ == "__main__":
    css_file = "D:/for_workbuddy/custom-blog.css"
    apply_custom_css(css_file)
```

### 美化CSS示例

```css
/* WordPress博客美化CSS */

/* 全局背景渐变 */
body {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    font-family: 'Microsoft YaHei', sans-serif;
}

/* 站点标题渐变 */
.site-title {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: bold;
}

/* 文章卡片阴影 */
.post, .card {
    background: #fff;
    border-radius: 15px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    padding: 25px;
    margin: 20px 0;
    transition: transform 0.3s ease;
}

.post:hover, .card:hover {
    transform: translateY(-5px);
}

/* 响应式设计 */
@media (max-width: 768px) {
    body {
        padding: 10px;
    }
    .post, .card {
        padding: 15px;
    }
}
```

## 功能二：社交分享页面（一键转发）

### 工作流程

1. **创建HTML分享页面**：包含8大平台的分享卡片
2. **通过REST API发布**：使用 `POST /wp/v2/pages` 创建页面
3. **访问分享页面**：`http://43.226.44.9/social-share/`

### 分享页面HTML模板

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>一键分享到全平台 | WordPress博客</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        .header {
            text-align: center;
            color: white;
            margin-bottom: 40px;
        }

        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }

        .platforms-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }

        .platform-card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: all 0.3s ease;
            cursor: pointer;
        }

        .platform-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.3);
        }

        .platform-icon {
            font-size: 3em;
            margin-bottom: 15px;
        }

        .platform-name {
            font-size: 1.3em;
            font-weight: bold;
            color: #333;
            margin-bottom: 10px;
        }

        .platform-desc {
            color: #666;
            font-size: 0.9em;
            margin-bottom: 15px;
        }

        .share-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 1em;
            transition: all 0.3s ease;
        }

        .share-btn:hover {
            transform: scale(1.05);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }

        .content-preview {
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-top: 30px;
        }

        .content-preview h3 {
            color: #333;
            margin-bottom: 15px;
        }

        .content-area {
            background: #f5f5f5;
            border-radius: 10px;
            padding: 20px;
            font-size: 0.95em;
            line-height: 1.6;
            color: #555;
            white-space: pre-wrap;
        }

        .copy-btn {
            background: #4CAF50;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 25px;
            cursor: pointer;
            margin-top: 15px;
            font-size: 0.95em;
        }

        .copy-btn:hover {
            background: #45a049;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 一键分享到全平台</h1>
            <p>选择平台，复制内容，快速发布</p>
        </div>

        <div class="platforms-grid">
            <!-- 今日头条 -->
            <div class="platform-card" onclick="window.open('https://mp.toutiao.com/profile_v4/', '_blank')">
                <div class="platform-icon">📰</div>
                <div class="platform-name">今日头条</div>
                <div class="platform-desc">发布文章到头条号</div>
                <button class="share-btn">打开头条后台</button>
            </div>

            <!-- 抖音 -->
            <div class="platform-card" onclick="window.open('https://creator.douyin.com/', '_blank')">
                <div class="platform-icon">🎵</div>
                <div class="platform-name">抖音</div>
                <div class="platform-desc">发布短视频内容</div>
                <button class="share-btn">打开抖音创作平台</button>
            </div>

            <!-- 小红书 -->
            <div class="platform-card" onclick="window.open('https://creator.xiaohongshu.com/', '_blank')">
                <div class="platform-icon">📕</div>
                <div class="platform-name">小红书</div>
                <div class="platform-desc">分享生活点滴</div>
                <button class="share-btn">打开小红书创作中心</button>
            </div>

            <!-- 知乎 -->
            <div class="platform-card" onclick="window.open('https://zhuanlan.zhihu.com/write', '_blank')">
                <div class="platform-icon">🤔</div>
                <div class="platform-name">知乎</div>
                <div class="platform-desc">写文章、回答问题</div>
                <button class="share-btn">打开知乎专栏</button>
            </div>

            <!-- 新浪微博 -->
            <div class="platform-card" onclick="window.open('https://weibo.com/', '_blank')">
                <div class="platform-icon">🦆</div>
                <div class="platform-name">新浪微博</div>
                <div class="platform-desc">发布微博动态</div>
                <button class="share-btn">打开微博</button>
            </div>

            <!-- QQ空间 -->
            <div class="platform-card" onclick="window.open('https://qzone.qq.com/', '_blank')">
                <div class="platform-icon">⭐</div>
                <div class="platform-name">QQ空间</div>
                <div class="platform-desc">分享到QQ空间</div>
                <button class="share-btn">打开QQ空间</button>
            </div>

            <!-- 快手 -->
            <div class="platform-card" onclick="window.open('https://cp.kuaishou.com/', '_blank')">
                <div class="platform-icon">🎬</div>
                <div class="platform-name">快手</div>
                <div class="platform-desc">发布快手短视频</div>
                <button class="share-btn">打开快手创作者中心</button>
            </div>

            <!-- 微信公众号 -->
            <div class="platform-card" onclick="window.open('https://mp.weixin.qq.com/', '_blank')">
                <div class="platform-icon">💬</div>
                <div class="platform-name">微信公众号</div>
                <div class="platform-desc">推送微信文章</div>
                <button class="share-btn">打开微信公众平台</button>
            </div>
        </div>

        <!-- 内容预览区域 -->
        <div class="content-preview">
            <h3>📝 文章内容预览</h3>
            <div class="content-area" id="contentArea">
{{POST_CONTENT}}
            </div>
            <button class="copy-btn" onclick="copyContent()">📋 复制内容</button>
        </div>
    </div>

    <script>
        function copyContent() {
            const content = document.getElementById('contentArea').innerText;
            navigator.clipboard.writeText(content).then(() => {
                alert('✅ 内容已复制到剪贴板！');
            });
        }
    </script>
</body>
</html>
```

### 发布分享页面的Python脚本

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建WordPress分享页面脚本
通过REST API创建社交分享页面
"""

import requests
from requests.auth import HTTPBasicAuth

# WordPress认证信息
WP_URL = "http://43.226.44.9"
WP_USER = "sunt"
WP_APP_PASS = "bp5RZDmsomAPFlmqk0xenYko"

def create_share_page(html_file):
    """创建社交分享页面"""

    # 读取HTML文件
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except Exception as e:
        print(f"❌ 读取HTML文件失败: {e}")
        return False

    # 构建API请求
    api_url = f"{WP_URL}/wp-json/wp/v2/pages"
    auth = HTTPBasicAuth(WP_USER, WP_APP_PASS)

    # 页面数据
    page_data = {
        "title": "一键分享到全平台",
        "content": html_content,
        "status": "publish",
        "slug": "social-share"
    }

    # 发送请求
    try:
        response = requests.post(
            api_url,
            json=page_data,
            auth=auth,
            timeout=30
        )

        if response.status_code == 201:
            result = response.json()
            print("✅ 分享页面创建成功！")
            print(f"📄 页面ID: {result['id']}")
            print(f"🔗 访问地址: <ADDRESS_REDACTED>
            return True
        else:
            print(f"❌ API请求失败: {response.status_code}")
            print(response.text)
            return False

    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

if __name__ == "__main__":
    html_file = "D:/for_workbuddy/social-share-page.html"
    create_share_page(html_file)
```

## 技术要点总结

### 环境配置

1. **Python依赖安装**（必须安装到D盘）
   ```bash
   pip install --target=D:/for_workbuddy/pylibs requests
   ```

2. **Python执行路径**
   ```
   /d/Python/Python311/python.exe
   ```

3. **脚本存放路径**
   ```
   D:/for_workbuddy/apply_css.py
   D:/for_workbuddy/create_share_page.py
   ```

### 云服务器 + 云主机协同架构

```
┌─────────────────┐         ┌──────────────────┐
│   本地机器       │         │  云主机           │
│  (Python脚本)   │────────>│  (WordPress)     │
│                 │  REST   │  http://43.226.  │
│                 │  API    │  44.9             │
└─────────────────┘         └──────────────────┘
        │                            │
        │                            │
        v                            v
   D:/for_workbuddy/          WordPress数据库
   (脚本+CSS+HTML)            (博客内容)
```

**优势**：
- 避免SSH连接不稳定问题
- 本地灵活编辑脚本和样式
- API调用稳定可靠

## API端点速查表

| 功能 | 方法 | 端点 |
|------|------|------|
| 获取设置 | GET | `/wp-json/wp/v2/settings` |
| 更新设置(CSS) | POST | `/wp-json/wp/v2/settings` |
| 获取主题列表 | GET | `/wp-json/wp/v2/themes` |
| 获取插件列表 | GET | `/wp-json/wp/v2/plugins` |
| 激活插件 | POST | `/wp-json/wp/v2/plugins/{slug}/{file}` |
| 创建页面 | POST | `/wp-json/wp/v2/pages` |
| 获取文章列表 | GET | `/wp-json/wp/v2/posts` |
| 创建文章 | POST | `/wp-json/wp/v2/posts` |

## 常见问题

### Q1: REST API返回401认证失败？
**A**: 确认使用应用密码（Application Password），不是登录密码。在WordPress后台「用户」→「个人资料」中生成。

### Q2: CSS应用后博客没有变化？
**A**: 清除浏览器缓存，或检查CSS选择器是否匹配当前主题。使用浏览器开发者工具检查元素。

### Q3: 分享页面打开后样式错乱？
**A**: 确认HTML模板中的CSS是完整的，所有标签正确闭合。

## 扩展功能

### 自动获取最新文章并预填到分享页面

```python
def get_latest_post():
    """获取最新文章用于分享"""
    api_url = f"{WP_URL}/wp-json/wp/v2/posts"
    auth = HTTPBasicAuth(WP_USER, WP_APP_PASS)

    response = requests.get(
        api_url,
        params={"per_page": 1, "status": "publish"},
        auth=auth
    )

    if response.status_code == 200:
        posts = response.json()
        if posts:
            return {
                "title": posts[0]['title']['rendered'],
                "content": posts[0]['content']['rendered']
            }
    return None
```

## 安全提醒

1. **应用密码保密**：不要在公开代码仓库中包含真实的应用密码
2. **使用环境变量**：生产环境使用 `os.environ.get('WP_APP_PASS')` 读取密码
3. **API限流**：避免频繁调用API，添加适当延时

## 文件路径总结

| 文件 | 路径 |
|------|------|
| 自定义CSS | `D:/for_workbuddy/custom-blog.css` |
| 分享页面HTML | `D:/for_workbuddy/social-share-page.html` |
| CSS应用脚本 | `D:/for_workbuddy/apply_css.py` |
| 分享页面创建脚本 | `D:/for_workbuddy/create_share_page.py` |
| 分享页面访问 | `http://43.226.44.9/social-share/` |
| 博客首页 | `http://43.226.44.9` |
