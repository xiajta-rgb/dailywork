#!/usr/bin/env python3
"""
GitHub 趋势数据每日定时更新脚本

此脚本用于每日自动登录并爬取 GitHub 趋势数据，
可以在 GitHub Actions 上设置为定时任务。
"""

import logging
import os  # 新增：导入os模块读取环境变量
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

# 配置日志（适配CI环境：日志同时输出到文件和控制台，文件路径改为logs目录）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/daily_update.log'),  # 修改：日志放到logs目录
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 配置信息
BASE_URL = os.getenv("BASE_URL", "https://trend.pythonanywhere.com")  # 修改：从环境变量读取BASE_URL

# 管理员账号信息（核心修改：从环境变量读取，替代硬编码）
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")

# 新增：校验环境变量是否为空，为空则直接退出并报错
def check_env_vars():
    """校验必要的环境变量"""
    if not ADMIN_USERNAME:
        logger.error("ERROR: ADMIN_USERNAME 环境变量未配置！")
        exit(2)
    if not ADMIN_PASSWORD:
        logger.error("ERROR: ADMIN_PASSWORD 环境变量未配置！")
        exit(2)
    logger.info("环境变量校验通过")

def update_trending_data():
    """更新趋势数据"""
    logger.info(f"开始更新 GitHub 趋势数据: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    browser = None
    page = None
    
    try:
        # 启动 Playwright
        with sync_playwright() as p:
            # 配置浏览器（修改：补充CI环境适配参数，隐藏自动化特征）
            browser = p.chromium.launch(
                headless=True,  # 无头模式，适合CI环境
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--window-size=1920,1080',
                    '--disable-blink-features=AutomationControlled',  # 新增：隐藏自动化特征
                    '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'  # 新增：模拟正常浏览器UA
                ]
            )
            logger.info("浏览器启动完成")
            
            # 创建新页面（修改：补充视口大小）
            page = browser.new_page(viewport={'width': 1920, 'height': 1080})
            page.set_default_timeout(120000)  # 修改：超时时间延长到120秒，适配CI网络
            logger.info("新页面创建完成")
            
            # 1. 进入公共页面
            logger.info(f"访问首页: {BASE_URL}")
            page.goto(BASE_URL)
            page.wait_for_load_state('networkidle', timeout=120000)
            logger.info("首页加载完成")
            
            # 2. 点击登录按钮（优化：增加更多等待和容错）
            logger.info("查找并点击登录按钮")
            try:
                # 等待登录按钮出现并点击
                login_button = page.locator('#admin-login-btn')
                login_button.wait_for(state='visible', timeout=60000)  # 修改：延长等待时间
                login_button.click()
                logger.info("登录按钮点击成功")
            except Exception as e:
                logger.error(f"找不到登录按钮: {e}")
                # 尝试查找其他可能的登录按钮
                try:
                    # 查找所有按钮，看是否有包含"登录"的
                    buttons = page.locator('button')
                    count = buttons.count()
                    for i in range(count):
                        button = buttons.nth(i)
                        text = button.inner_text().strip()  # 新增：去除空格
                        if "登录" in text:
                            button.click()
                            logger.info(f"找到并点击了包含'登录'的按钮: {text}")
                            break
                except Exception as inner_e:
                    logger.error(f"查找登录按钮失败: {inner_e}")
                    raise  # 新增：抛出异常，让脚本退出并提示错误
            
            # 等待登录模态框出现并完全加载
            logger.info("等待登录模态框出现")
            page.wait_for_timeout(8000)  # 修改：延长等待时间到8秒
            
            # 3. 填写登录表单（优化：增加更多等待和容错）
            logger.info("填写登录表单")
            try:
                # 使用更具体的定位器，只选择第一个匹配的元素
                username_input = page.locator('#login-modal #username').first
                username_input.wait_for(state='visible', timeout=60000)  # 修改：延长等待时间
                logger.info("找到用户名输入框")
                username_input.fill(ADMIN_USERNAME)
                logger.info(f"用户名输入完成: {ADMIN_USERNAME}")
                
                # 使用更具体的定位器，只选择第一个匹配的元素
                password_input = page.locator('#login-modal #password').first
                password_input.wait_for(state='visible', timeout=60000)  # 修改：延长等待时间
                logger.info("找到密码输入框")
                password_input.fill(ADMIN_PASSWORD)
                logger.info("密码输入完成")
                
                # 使用更具体的定位器，只选择第一个匹配的元素
                submit_button = page.locator('#login-modal button[type="submit"]').first
                submit_button.wait_for(state='visible', timeout=60000)  # 修改：延长等待时间
                logger.info("找到登录提交按钮")
                submit_button.click()
                logger.info("登录表单提交成功")
            except Exception as e:
                logger.error(f"填写登录表单失败: {e}")
                raise  # 新增：抛出异常，让脚本退出并提示错误
            
            # 等待登录完成和页面刷新
            page.wait_for_load_state('networkidle', timeout=120000)
            logger.info("登录完成，页面刷新成功")
            
            # 4. 进入历史数据页面（优化：增加容错）
            logger.info("进入历史数据页面")
            try:
                # 等待历史数据链接出现并点击
                history_link = page.locator('#history-link')
                history_link.wait_for(state='visible', timeout=60000)  # 修改：延长等待时间
                history_link.click()
                logger.info("历史数据页面进入成功")
            except Exception as e:
                logger.error(f"进入历史数据页面失败: {e}")
                raise  # 新增：抛出异常，让脚本退出并提示错误
            
            # 等待历史数据页面加载
            page.wait_for_load_state('networkidle', timeout=120000)
            logger.info("历史数据页面加载完成")
            
            # 5. 点击爬取数据按钮（优化：增加容错）
            logger.info("查找并点击爬取数据按钮")
            try:
                # 等待爬取数据按钮出现并点击
                update_button = page.locator('#update-data-btn')
                update_button.wait_for(state='visible', timeout=60000)  # 修改：延长等待时间
                update_button.click()
                logger.info("爬取数据按钮点击成功")
            except Exception as e:
                logger.error(f"找不到爬取数据按钮: {e}")
                # 尝试查找其他可能的爬取按钮
                try:
                    # 查找所有按钮，看是否有包含"爬取"或"更新"的
                    buttons = page.locator('button')
                    count = buttons.count()
                    for i in range(count):
                        button = buttons.nth(i)
                        text = button.inner_text().strip()  # 新增：去除空格
                        if "爬取" in text or "更新" in text:
                            button.click()
                            logger.info(f"找到并点击了包含'爬取'或'更新'的按钮: {text}")
                            break
                except Exception as inner_e:
                    logger.error(f"查找爬取按钮失败: {inner_e}")
                    raise  # 新增：抛出异常，让脚本退出并提示错误
            
            # 6. 等待爬取完成
            logger.info("等待爬取过程完成")
            # 最多等待20分钟
            max_wait_time = 1200  # 20分钟
            start_time = time.time()
            
            while time.time() - start_time < max_wait_time:
                try:
                    # 检查是否有爬取完成的提示
                    toast_elements = page.locator('.toast')
                    count = toast_elements.count()
                    for i in range(count):
                        toast = toast_elements.nth(i)
                        text = toast.inner_text().strip()  # 新增：去除空格
                        if "成功" in text or "完成" in text:
                            logger.info(f"爬取完成提示: {text}")
                            break
                    
                    # 检查爬取按钮状态
                    try:
                        update_button = page.locator('#update-data-btn')
                        if update_button.is_visible():
                            text = update_button.inner_text().strip()  # 新增：去除空格
                            if "爬取中" not in text:
                                logger.info(f"爬取按钮状态已恢复: {text}，爬取可能已完成")
                                break
                    except:
                        pass
                    
                    time.sleep(10)  # 每10秒检查一次
                except Exception as e:
                    logger.error(f"检查爬取状态失败: {e}")
                    time.sleep(10)
            
            if time.time() - start_time >= max_wait_time:
                logger.warning("爬取时间超过20分钟，可能仍在进行中")
            
            # 关闭浏览器
            browser.close()
            logger.info("浏览器已关闭")
        
    except Exception as e:
        logger.error(f"更新过程中发生错误: {e}", exc_info=True)
        raise  # 新增：抛出异常，让脚本返回非0退出码
    finally:
        # 确保浏览器关闭
        if browser:
            try:
                browser.close()
                logger.info("浏览器已关闭")
            except Exception as e:
                logger.error(f"关闭浏览器失败: {e}")
    
    logger.info(f"更新任务完成: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    # 新增：先创建logs目录（避免日志文件写入失败）
    os.makedirs("logs", exist_ok=True)
    # 新增：校验环境变量
    check_env_vars()
    # 执行更新
    update_trending_data()
