#!/usr/bin/env python3
import logging
import os
from playwright.sync_api import sync_playwright

# 极简日志配置（只输出关键信息，不写文件也能缩短时间）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]  # 只输出到控制台，不写日志文件
)
logger = logging.getLogger(__name__)

# 读取环境变量
BASE_URL = os.getenv("BASE_URL", "https://trend.pythonanywhere.com")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")

# 校验环境变量（快速失败）
if not ADMIN_USERNAME or not ADMIN_PASSWORD:
    logger.error("账号/密码未配置！")
    exit(1)

def quick_click_update_btn():
    """极简逻辑：只做“访问→登录→点击按钮→退出”"""
    with sync_playwright() as p:
        # 浏览器极简配置（关闭不必要的功能）
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-images',  # 不加载图片，提速
                '--disable-javascript-harmony-shipping',  # 精简JS
                '--window-size=1920,1080'
            ]
        )
        page = browser.new_page()
        page.set_default_timeout(30000)  # 超时缩短到30秒（原120秒）

        try:
            # 1. 快速访问首页（只等基本加载）
            logger.info("访问首页")
            page.goto(BASE_URL, wait_until="domcontentloaded")  # 只等DOM加载，不等网络空闲

            # 2. 快速点击登录按钮
            logger.info("点击登录按钮")
            page.locator('#admin-login-btn').click(timeout=10000)
            page.wait_for_timeout(2000)  # 极简等待（2秒）

            # 3. 快速填写登录信息
            logger.info("填写登录信息")
            page.locator('#login-modal #username').first.fill(ADMIN_USERNAME, timeout=10000)
            page.locator('#login-modal #password').first.fill(ADMIN_PASSWORD, timeout=10000)
            page.locator('#login-modal button[type="submit"]').first.click(timeout=10000)
            page.wait_for_timeout(3000)  # 登录后极简等待（3秒）

            # 4. 快速点击爬取按钮（核心操作）
            logger.info("点击爬取数据按钮")
            page.locator('#update-data-btn').click(timeout=10000)
            logger.info("按钮点击成功，立即退出！")

        except Exception as e:
            logger.error(f"操作失败: {e}")
            exit(1)
        finally:
            # 点击按钮后立即关闭浏览器，不等待任何后续操作
            browser.close()

if __name__ == "__main__":
    quick_click_update_btn()
    exit(0)  # 执行完成立即退出，无多余等待
