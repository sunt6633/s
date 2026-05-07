# WordPress REST API 参考文档

本文档提供WordPress REST API的详细参考，用于blog-renovation技能。

## 基础信息

- **博客地址**: `http://43.226.44.9`
- **REST API基础URL**: `http://43.226.44.9/wp-json/wp/v2`
- **认证方式**: HTTP Basic Auth with Application Password
- **用户名**: `sunt`
- **应用密码**: `bp5RZDmsomAPFlmqk0xenYko`

## 认证

WordPress REST API使用应用密码（Application Password）进行认证。

```python
from requests.auth import HTTPBasicAuth

auth = HTTPBasicAuth('sunt', 'bp5RZDmsomAPFlmqk0xenYko')
```

### 生成应用密码

1. 登录WordPress后台
2. 进入「用户」→「个人资料」
3. 找到「应用密码」部分
4. 输入应用名称，点击「添加新应用密码」
5. 复制生成的密码（只显示一次）

## API端点详解

### 1. 设置（Settings）

#### 获取设置

```
GET /wp-json/wp/v2/settings
```

**响应示例**:
```json
{
  "title": "站点标题",
  "description": "站点描述",
  "custom_css": "CSS代码",
  "timezone": "Asia/Shanghai",
  "date_format": "Y-m-d",
  "time_format": "H:i"
}
```

#### 更新设置

```
POST /wp-json/wp/v2/settings
```

**请求体**:
```json
{
  "custom_css": "CSS代码内容",
  "title": "新站点标题"
}
```

**注意**: 只能更新当前用户有权限修改的设置。

### 2. 文章（Posts）

#### 获取文章列表

```
GET /wp-json/wp/v2/posts
```

**常用参数**:
- `per_page`: 每页文章数（默认10，最大100）
- `page`: 页码
- `status`: 文章状态（publish, draft, private, trash）
- `categories`: 分类ID
- `tags`: 标签ID
- `search`: 搜索关键词
- `after`: 获取指定日期后的文章
- `before`: 获取指定日期前的文章
- `exclude`: 排除指定ID的文章
- `include`: 只包括指定ID的文章
- `order`: 排序方向（asc, desc）
- `orderby`: 排序字段（date, title, modified, etc.）

**响应示例**:
```json
[
  {
    "id": 123,
    "title": {"rendered": "文章标题"},
    "content": {"rendered": "文章内容HTML"},
    "excerpt": {"rendered": "文章摘要"},
    "status": "publish",
    "link": "http://43.226.44.9/文章别名/",
    "slug": "文章别名",
    "date": "2026-05-07T10:30:00",
    "modified": "2026-05-07T11:00:00"
  }
]
```

#### 获取单篇文章

```
GET /wp-json/wp/v2/posts/{id}
```

#### 创建文章

```
POST /wp-json/wp/v2/posts
```

**请求体**:
```json
{
  "title": "文章标题",
  "content": "文章内容",
  "status": "publish",
  "slug": "post-slug",
  "categories": [1, 2],
  "tags": [3, 4]
}
```

#### 更新文章

```
POST /wp-json/wp/v2/posts/{id}
```

#### 删除文章

```
DELETE /wp-json/wp/v2/posts/{id}
```

**参数**:
- `force`: 是否永久删除（true/false）

### 3. 页面（Pages）

#### 获取页面列表

```
GET /wp-json/wp/v2/pages
```

**常用参数**: 与文章相同

#### 创建页面

```
POST /wp-json/wp/v2/pages
```

**请求体**:
```json
{
  "title": "页面标题",
  "content": "页面内容HTML",
  "status": "publish",
  "slug": "page-slug"
}
```

### 4. 主题（Themes）

#### 获取主题列表

```
GET /wp-json/wp/v2/themes
```

**响应示例**:
```json
[
  {
    "stylesheet": "astra",
    "template": "astra",
    "name": "Astra",
    "status": "inactive"
  }
]
```

### 5. 插件（Plugins）

#### 获取插件列表

```
GET /wp-json/wp/v2/plugins
```

**响应示例**:
```json
[
  {
    "plugin": "contact-form-7/wp-contact-form-7.php",
    "status": "active",
    "name": "Contact Form 7"
  }
]
```

#### 激活插件

```
POST /wp-json/wp/v2/plugins/{plugin_slug}/{plugin_file}
```

**请求体**:
```json
{
  "status": "active"
}
```

## 完整Python示例

### 应用自定义CSS

```python
import requests
from requests.auth import HTTPBasicAuth

WP_URL = "http://43.226.44.9"
auth = HTTPBasicAuth('sunt', 'bp5RZDmsomAPFlmqk0xenYko')

# 读取CSS文件
with open('custom-blog.css', 'r', encoding='utf-8') as f:
    css = f.read()

# 应用CSS
response = requests.post(
    f"{WP_URL}/wp-json/wp/v2/settings",
    json={"custom_css": css},
    auth=auth,
    timeout=30
)

if response.status_code == 200:
    print("✅ CSS应用成功")
else:
    print(f"❌ 失败: {response.status_code}")
    print(response.text)
```

### 创建分享页面

```python
import requests
from requests.auth import HTTPBasicAuth

WP_URL = "http://43.226.44.9"
auth = HTTPBasicAuth('sunt', 'bp5RZDmsomAPFlmqk0xenYko')

# 读取HTML文件
with open('social-share-page.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 创建页面
response = requests.post(
    f"{WP_URL}/wp-json/wp/v2/pages",
    json={
        "title": "一键分享到全平台",
        "content": html,
        "status": "publish",
        "slug": "social-share"
    },
    auth=auth,
    timeout=30
)

if response.status_code == 201:
    result = response.json()
    print(f"✅ 页面创建成功: {result['link']}")
else:
    print(f"❌ 失败: {response.status_code}")
    print(response.text)
```

### 获取最新文章

```python
import requests
from requests.auth import HTTPBasicAuth

WP_URL = "http://43.226.44.9"
auth = HTTPBasicAuth('sunt', 'bp5RZDmsomAPFlmqk0xenYko')

response = requests.get(
    f"{WP_URL}/wp-json/wp/v2/posts",
    params={
        "per_page": 1,
        "status": "publish"
    },
    auth=auth,
    timeout=10
)

if response.status_code == 200:
    posts = response.json()
    if posts:
        post = posts[0]
        print(f"标题: {post['title']['rendered']}")
        print(f"链接: {post['link']}")
        print(f"内容: {post['content']['rendered'][:200]}...")
```

## 错误处理

### 常见状态码

- `200 OK`: 请求成功
- `201 Created`: 创建成功
- `400 Bad Request`: 请求参数错误
- `401 Unauthorized`: 认证失败（检查应用密码）
- `403 Forbidden`: 权限不足
- `404 Not Found`: 资源不存在
- `500 Internal Server Error`: 服务器错误

### 错误处理示例

```python
try:
    response = requests.post(api_url, json=data, auth=auth, timeout=30)
    response.raise_for_status()  # 抛出HTTPError（如果状态码不是200-299）

    result = response.json()
    print("✅ 成功")

except requests.exceptions.Timeout:
    print("❌ 请求超时")
except requests.exceptions.ConnectionError:
    print("❌ 连接错误")
except requests.exceptions.HTTPError as e:
    print(f"❌ HTTP错误: {e.response.status_code}")
    print(f"响应: {e.response.text}")
except Exception as e:
    print(f"❌ 异常: {e}")
```

## 性能优化

### 1. 使用缓存

```python
import requests_cache

# 缓存GET请求（10分钟）
requests_cache.install_cache('wp_cache', expire_after=600)

# 之后的GET请求会自动使用缓存
response = requests.get(api_url, auth=auth)
```

### 2. 批量操作

```python
# 一次获取多篇文章（最多100篇）
response = requests.get(
    f"{WP_URL}/wp-json/wp/v2/posts",
    params={"per_page": 100},
    auth=auth
)
```

### 3. 字段过滤

```python
# 只获取需要的字段（减少响应大小）
response = requests.get(
    f"{WP_URL}/wp-json/wp/v2/posts",
    params={
        "per_page": 10,
        "_fields": "id,title,link,date"
    },
    auth=auth
)
```

## 安全建议

1. **不要在代码中硬编码密码**
   ```python
   import os
   WP_PASS = os.environ.get('WP_APP_PASS')
   ```

2. **使用HTTPS**（如果可能）
   - 虽然示例中使用HTTP，但生产环境应使用HTTPS

3. **限制应用密码权限**
   - 只为特定应用生成专用密码
   - 定期更换应用密码

4. **添加请求限速**
   ```python
   import time

   for post_id in post_ids:
       response = requests.get(f"{api_url}/posts/{post_id}", auth=auth)
       time.sleep(0.5)  # 每次请求间隔0.5秒
   ```

## 相关资源

- [WordPress REST API 官方文档](https://developer.wordpress.org/rest-api/)
- [WordPress REST API 手册](https://developer.wordpress.org/rest-api/using-the-rest-api/)
- [应用密码官方文档](https://wordpress.org/documentation/article/application-passwords/)
