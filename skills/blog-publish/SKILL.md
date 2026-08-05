---
name: blog-publish
description: 把文章发布到孙先生的 WordPress 博客。触发词："发博客""写篇发到博客""发布到 WordPress""new post""发篇文章"。主站 106.52.62.15 当前仅 HTTP，必须用 SSH+wp_insert_post 通道；旧站 43.226.44.9 已上 HTTPS，可用 REST。
---

# blog-publish —— 博客发布技能

把文章（HTML 或 Markdown 转 HTML）发布到孙先生的 WordPress。本技能给出**两条经过验证的通道**，按站点二选一。

## 站点与凭证

### 主站（新，腾讯云轻量 106.52.62.15）—— 当前默认目标
- 系统 Ubuntu 24.04，WordPress 在 `/var/www/wordpress`
- SSH 登录：`ubuntu` / 密码（**由孙先生在配置时提供，经环境变量 `WP_SSH_PASS` 注入，切勿硬编码进本文件或提交到仓库**）
- **仅 HTTP，未上 SSL** → WordPress 的「应用密码 / REST Basic Auth」要求 HTTPS，故 REST 通道在此站**不可用**，必须用下方「通道 A」
- wp-cli 已装为系统命令：`/usr/local/bin/wp`

### 旧站（43.226.44.9，仍在运行）
- 已配 HTTPS，REST API 可用
- 凭证：用户 `sunt` / 应用密码 `bp5RZDmsomAPFlmqk0xenYko`（旧站 publish_to_wp.py 同款）
- 发布通道：REST `POST /wp-json/wp/v2/posts`（见「通道 B」）

## 通道 A：SSH + wp_insert_post（主站必用，已验证 ✅）

要点：把正文写成 HTML 文件 → 上传到服务器 → 用随本 skill 附带的 `references/wp_publish.php` 助手创建文章。**不要**用 `wp post create --post_content=...` 命令行传参（中文/HTML/引号会丢失内容，已实测失败）。

参考实现（Python，paramiko）：

```python
import paramiko, os
HOST, USER = "106.52.62.15", "ubuntu"
PW = os.environ["WP_SSH_PASS"]          # 运行时注入，勿写死

HELPER = open("references/wp_publish.php").read()   # 本 skill 自带的助手
HTML = "<h2>标题</h2><p>正文 HTML……</p>"            # 实际文章正文(HTML)

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PW, timeout=15)
sftp = ssh.open_sftp()
sftp.putfo(__import__("io").BytesIO(HELPER.encode()), "/tmp/wp_publish.php")
sftp.putfo(__import__("io").BytesIO(HTML.encode("utf-8")), "/tmp/post.html")
sftp.close()

title = "文章标题"
# 关键命令：用 www-data 身份跑助手，避免 root 被拒 + 保证文件属主正确
cmd = f"sudo -u www-data php /tmp/wp_publish.php --title={title!r} --file=/tmp/post.html --status=draft"
_, out, err = ssh.exec_command(cmd)
rc = out.channel.recv_exit_status()
new_id = out.read().decode().strip()      # 成功则打印文章 ID
print("rc", rc, "id", new_id, "err", err.read().decode()[:300])
ssh.close()
```

Node.js 参考实现（小龙 OpenClaw 用，`ssh2` + `fs`）：

```js
const { Client } = require('ssh2');
const fs = require('fs');
const conn = new Client();
conn.on('ready', () => {
  conn.sftp((err, sftp) => {
    if (err) throw err;
    sftp.fastPut('references/wp_publish.php', '/tmp/wp_publish.php', () => {
      sftp.fastPut('post.html', '/tmp/post.html', () => {
        conn.exec(
          `sudo -u www-data php /tmp/wp_publish.php --title='文章标题' --file=/tmp/post.html --status=draft`,
          (e, stream) => {
            let buf = '';
            stream.on('data', d => buf += d);
            stream.stderr.on('data', d => process.stderr.write(d));
            stream.on('close', () => { console.log('new post id:', buf.trim()); conn.end(); });
          });
      });
    });
  });
}).connect({ host: '106.52.62.15', username: 'ubuntu', password: process.env.WP_SSH_PASS });
```

发布流程建议：**先 `--status=draft` 建草稿 → 回读确认渲染正常 → 再 `wp post update <id> --post_status=publish` 发布**（或建时直接 `publish`）。

## 通道 B：REST API（旧站 / 主站上 SSL 后）

仅当站点已配 HTTPS 时可用（应用密码依赖 HTTPS）。

```bash
curl -u sunt:bp5RZDmsomAPFlmqk0xenYko \
  -X POST https://43.226.44.9/wp-json/wp/v2/posts \
  -H "Content-Type: application/json" \
  -d '{"title":"文章标题","content":"<p>HTML 正文</p>","status":"draft"}'
```

主站上 SSL 后（`certbot --nginx -d 域名`），把 host 换成域名、凭证换成新站应用密码即可启用此通道。

## ⚠️ 陷阱清单（踩过的坑，必读）
1. **HTTP 站点 REST 应用密码失效**：WordPress 只在 HTTPS 下接受 Basic Auth，主站 106.52.62.15 现在只能走通道 A。
2. **`wp post create --post_content=...` 丢内容**：命令行传中文/HTML/引号会静默丢弃正文。必须用文件 + 助手（通道 A）。
3. **wp-cli 拒绝 root**：直接 `sudo wp` 会被拦，必须 `sudo -u www-data`（WordPress 属主）。
4. **wp 命令路径**：系统命令是 `/usr/local/bin/wp`，不是 `wp-cli.phar`（phar 源文件可能已被清理）。
5. **密码安全**：服务器 SSH 密码、REST 应用密码均属敏感凭据，**绝不写进 skill 文件或提交仓库**；用环境变量/密钥管理器注入。对话里曾明文出现过，提醒孙先生改服务器密码。
6. **fail2ban 已开**：主站 22 端口裸密码暴露公网，已被扫描爆破过，发布后不要长期留弱密码。
7. **标题含空格/特殊字符**：命令行用 Python `!r` 或单引号包裹；超长/极复杂标题优先用 `--title=` 配文件法（助手也支持 `--title=file://` 可扩展）。

## 质量约定
- 旧站有价值的内容已迁移到主站（62 篇高质量文，低质测试/软文/水文未迁）。
- 发布前确认文章质量达标，低质内容不发。
- 图片尽量用外链或媒体库，避免正文内嵌超大 base64。
