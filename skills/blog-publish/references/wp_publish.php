<?php
// 博客发布助手 —— 由 blog-publish skill 调用
// 读取一个 HTML 文件，用 wp_insert_post 创建文章。
// 设计目的：绕过 WordPress REST 应用密码要求 HTTPS 的限制（主站当前仅 HTTP），
// 并彻底避开 wp-cli 命令行传参的引号/编码地狱。
//
// 用法（服务器侧）：
//   sudo -u www-data php /tmp/wp_publish.php --title="标题" --file=/tmp/内容.html --status=draft
//   --status 可选：draft(草稿) | publish(直接发布) | pending(待审)
// 输出：成功打印新文章 ID；失败打印 ERR ... 并以非 0 退出码结束。

$opts = getopt('', ['title:', 'file:', 'status:']);
if (empty($opts['file']) || !file_exists($opts['file'])) {
    fwrite(STDERR, "ERR: --file 不存在或缺失\n");
    exit(2);
}

// 加载 WordPress 运行环境（CLI 上下文）
require_once('/var/www/wordpress/wp-load.php');

$content = file_get_contents($opts['file']);
$pid = wp_insert_post([
    'post_title'    => $opts['title'] ?? '无标题',
    'post_content'  => $content,
    'post_status'   => $opts['status'] ?? 'draft',
    'post_author'   => 1,
], true);

if (is_wp_error($pid)) {
    fwrite(STDERR, 'ERR: ' . $pid->get_error_message() . "\n");
    exit(1);
}
echo $pid;
