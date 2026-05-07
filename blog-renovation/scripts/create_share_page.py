#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WordPress社交分享页面创建脚本
通过REST API创建一键分享到多平台的页面

使用云服务器+云主机协同架构：
- 本地机器：运行此脚本（云主机）
- 云服务器：运行WordPress (http://43.226.44.9)
- 通过REST API通信，避免SSH不稳定问题
"""

import requests
from requests.auth import HTTPBasicAuth
import sys
import os

# WordPress认证信息
WP_URL = "http://43.226.44.9"
WP_USER = "sunt"
WP_APP_PASS = "bp5RZDmsomAPFlmqk0xenYko"
BASE_URL = f"{WP_URL}/wp-json/wp/v2"

def create_share_page(html_file, title="一键分享到全平台", slug="social-share"):
    """
    创建社交分享页面

    Args:
        html_file: HTML文件路径
        title: 页面标题
        slug: 页面别名（用于URL）

    Returns:
        bool: 成功返回True，失败返回False
    """
    # 读取HTML文件
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        print(f"✅ 已读取HTML文件: {html_file}")
        print(f"📊 HTML大小: {len(html_content)} 字符")
    except Exception as e:
        print(f"❌ 读取HTML文件失败: {e}")
        return False

    # 构建API请求
    api_url = f"{BASE_URL}/pages"
    auth = HTTPBasicAuth(WP_USER, WP_APP_PASS)

    # 页面数据
    page_data = {
        "title": title,
        "content": html_content,
        "status": "publish",
        "slug": slug
    }

    # 发送请求
    try:
        print(f"📡 正在发送API请求到: {api_url}")
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
            print(f"💡 提示: 如果页面已存在，会创建新版本")
            return True
        elif response.status_code == 400:
            print(f"❌ 请求错误: {response.status_code}")
            print(f"响应内容: {response.text}")
            print("💡 提示: 可能是slug已存在，尝试使用不同的slug")
            return False
        else:
            print(f"❌ API请求失败: {response.status_code}")
            print(f"响应内容: {response.text}")
            return False

    except requests.exceptions.Timeout:
        print("❌ 请求超时，请检查网络连接")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ 连接错误，请检查博客地址是否正确")
        return False
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

def get_latest_post():
    """
    获取最新发布的文章（用于分享预览）

    Returns:
        dict: 包含title和content的字典，失败返回None
    """
    print("📡 正在获取最新文章...")
    api_url = f"{BASE_URL}/posts"
    auth = HTTPBasicAuth(WP_USER, WP_APP_PASS)

    try:
        response = requests.get(
            api_url,
            params={"per_page": 1, "status": "publish"},
            auth=auth,
            timeout=10
        )

        if response.status_code == 200:
            posts = response.json()
            if posts:
                post = posts[0]
                print(f"✅ 获取最新文章成功: {post['title']['rendered']}")
                return {
                    "title": post['title']['rendered'],
                    "content": post['content']['rendered'],
                    "link": post['link']
                }
        print(f"❌ 获取文章失败: {response.status_code}")
        return None

    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return None

def test_api_connection():
    """
    测试API连通性

    Returns:
        bool: 连接成功返回True，失败返回False
    """
    print("🔍 测试API连通性...")
    api_url = f"{BASE_URL}/settings"
    auth = HTTPBasicAuth(WP_USER, WP_APP_PASS)

    try:
        response = requests.get(api_url, auth=auth, timeout=10)
        if response.status_code == 200:
            print("✅ API连接正常")
            return True
        else:
            print(f"❌ API连接失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 连接异常: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("WordPress社交分享页面创建工具")
    print("云主机协同版本")
    print("=" * 60)
    print()

    # 测试API连通性
    if not test_api_connection():
        print("\n❌ 请检查：")
        print("  1. 博客地址是否正确")
        print("  2. 应用密码是否有效")
        print("  3. 网络连接是否正常")
        sys.exit(1)

    print()

    # 默认HTML文件路径
    html_file = "D:/for_workbuddy/social-share-page.html"

    # 如果命令行提供了文件路径，使用命令行参数
    if len(sys.argv) > 1:
        html_file = sys.argv[1]

    # 检查文件是否存在
    if not os.path.exists(html_file):
        print(f"❌ HTML文件不存在: {html_file}")
        print(f"💡 提示: 请将HTML文件放到指定路径，或使用命令行参数指定")
        sys.exit(1)

    # 创建分享页面
    print(f"📄 正在创建分享页面...")
    print(f"📄 HTML文件: {html_file}")
    print()
    success = create_share_page(html_file)

    print()
    if success:
        print("🎉 社交分享页面创建完成！")
        print(f"🔗 访问地址: <ADDRESS_REDACTED>
        sys.exit(0)
    else:
        print("💔 分享页面创建失败，请检查错误信息")
        sys.exit(1)
