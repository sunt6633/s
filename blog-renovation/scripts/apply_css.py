#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WordPress博客CSS美化脚本
通过REST API应用自定义CSS，无需SSH访问

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

def apply_custom_css(css_file):
    """
    应用自定义CSS到WordPress博客

    Args:
        css_file: CSS文件路径

    Returns:
        bool: 成功返回True，失败返回False
    """
    # 读取CSS文件
    try:
        with open(css_file, 'r', encoding='utf-8') as f:
            custom_css = f.read()
        print(f"✅ 已读取CSS文件: {css_file}")
        print(f"📊 CSS大小: {len(custom_css)} 字符")
    except Exception as e:
        print(f"❌ 读取CSS文件失败: {e}")
        return False

    # 构建API请求
    api_url = f"{BASE_URL}/settings"
    auth = HTTPBasicAuth(WP_USER, WP_APP_PASS)

    # 发送请求
    try:
        print(f"📡 正在发送API请求到: {api_url}")
        response = requests.post(
            api_url,
            json={"custom_css": custom_css},
            auth=auth,
            timeout=30
        )

        if response.status_code == 200:
            print("✅ CSS美化成功应用！")
            print(f"🎨 博客地址：<ADDRESS_REDACTED"
            print(f"💡 提示: 请清除浏览器缓存后查看效果")
            return True
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
    print("WordPress博客CSS美化工具")
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

    # 默认CSS文件路径
    css_file = "D:/for_workbuddy/custom-blog.css"

    # 如果命令行提供了文件路径，使用命令行参数
    if len(sys.argv) > 1:
        css_file = sys.argv[1]

    # 检查文件是否存在
    if not os.path.exists(css_file):
        print(f"❌ CSS文件不存在: {css_file}")
        print(f"💡 提示: 请将CSS文件放到指定路径，或使用命令行参数指定")
        sys.exit(1)

    # 应用CSS
    print(f"📄 正在应用CSS文件: {css_file}")
    print()
    success = apply_custom_css(css_file)

    print()
    if success:
        print("🎉 博客装修完成！")
        sys.exit(0)
    else:
        print("💔 博客装修失败，请检查错误信息")
        sys.exit(1)
