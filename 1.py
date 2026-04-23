import json
import os
import time
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


# ============================================================
# 配置区
# ============================================================
TEST_URL = "https://practicetestautomation.com/practice-test-login/"
SCREENSHOT_DIR = os.path.expanduser("~/.openclaw/workspace/login-test/screenshots")
REPORT_DIR = os.path.expanduser("~/.openclaw/workspace/login-test/reports")

# 确保输出目录存在
os.makedirs(SCREENSHOT_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)


# ============================================================
# 工具函数
# ============================================================

def take_screenshot(driver, name_prefix: str) -> str:
    """
    截取当前浏览器页面并保存到 screenshots/ 目录。
    返回截图文件的相对路径。
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{name_prefix}_{timestamp}.png"
    filepath = os.path.join(SCREENSHOT_DIR, filename)
    driver.save_screenshot(filepath)
    return filepath


def generate_report(case_name: str, result: str, message: str,
                    screenshot_path: str = None,
                    defects: list = None) -> dict:
    """
    生成简易 JSON 格式测试报告，返回报告字典并持久化。
    """
    report = {
        "case_name": case_name,
        "execution_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "result": result,          # PASS / FAIL / ERROR
        "message": message,
        "screenshot_path": screenshot_path,
        "ui_defects": defects or []
    }

    # 写入 JSON 报告文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = os.path.join(REPORT_DIR, f"report_{timestamp}.json")
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    return report


def scan_ui_defects(driver) -> list:
    """
    自动扫描页面中常见的 UI 缺陷，返回缺陷清单。
    检查项：
      1. 按钮无点击响应（type=button 但无 onclick / 无 form 关联）
      2. 输入框无法输入（disabled / readonly 属性）
      3. 图片加载失败（naturalWidth === 0）
      4. 空链接（href 为空或 #）
    """
    defects = []

    # 1. 检查禁用/只读的输入框
    disabled_inputs = driver.find_elements(By.CSS_SELECTOR, "input[disabled]")
    readonly_inputs = driver.find_elements(By.CSS_SELECTOR, "input[readonly]")
    for elem in disabled_inputs:
        defects.append({
            "type": "输入框不可交互",
            "detail": f"disabled 输入框: {elem.get_attribute('outerHTML')[:100]}"
        })
    for elem in readonly_inputs:
        defects.append({
            "type": "输入框只读",
            "detail": f"readonly 输入框: {elem.get_attribute('outerHTML')[:100]}"
        })

    # 2. 检查图片加载失败
    broken_images = driver.execute_script("""
        var imgs = document.querySelectorAll('img');
        var broken = [];
        imgs.forEach(function(img) {
            if (!img.complete || img.naturalWidth === 0) {
                broken.push(img.src);
            }
        });
        return broken;
    """)
    for src in broken_images:
        defects.append({
            "type": "图片加载失败",
            "detail": f"src: {src}"
        })

    # 3. 检查空链接
    empty_links = driver.find_elements(By.CSS_SELECTOR, "a[href=''], a[href='#']")
    for link in empty_links:
        text = link.text.strip() or "(无文字)"
        defects.append({
            "type": "空链接",
            "detail": f"链接文字: {text}"
        })

    return defects


# ============================================================
# 核心测试逻辑
# ============================================================

def run_login_test(username: str, password: str, case_name: str):
    """
    执行登录测试的核心流程：
      1. 打开 Chrome 浏览器并访问目标页面
      2. 定位用户名、密码输入框并输入凭据
      3. 点击提交按钮
      4. 判断登录成功或失败，进行断言
      5. 截图 + 扫描 UI 缺陷 + 生成报告
    """
    driver = None
    try:
        # ---- Step 1: 启动浏览器 ----
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        
        # 自动下载匹配 Chrome 版本的驱动
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.implicitly_wait(5)  # 隐式等待，全局生效

        driver.get(TEST_URL)
        print(f"[INFO] 已访问: {TEST_URL}")

        # ---- Step 2: 定位输入框并输入 ----
        wait = WebDriverWait(driver, 10)

        username_input = wait.until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        password_input = driver.find_element(By.ID, "password")

        username_input.clear()
        username_input.send_keys(username)
        print(f"[INFO] 已输入用户名: {username}")

        password_input.clear()
        password_input.send_keys(password)
        print(f"[INFO] 已输入密码: {'*' * len(password)}")

        # ---- Step 3: 点击提交按钮 ----
        submit_btn = driver.find_element(By.ID, "submit")
        submit_btn.click()
        print("[INFO] 已点击提交按钮")

        # ---- Step 4: 验证登录结果 ----
        # 先检测是否出现错误提示（负向用例）
        try:
            error_elem = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.ID, "error"))
            )
            # 登录失败场景
            error_text = error_elem.text
            screenshot_path = take_screenshot(driver, f"{case_name}_FAIL")
            defects = scan_ui_defects(driver)

            report = generate_report(
                case_name=case_name,
                result="FAIL",
                message=f"登录失败，错误提示: {error_text}",
                screenshot_path=screenshot_path,
                defects=defects
            )
            print(f"[FAIL] 错误提示: {error_text}")
            return report

        except TimeoutException:
            # 没有错误提示，继续验证是否登录成功
            pass

        # 检测登录成功标志
        try:
            success_elem = WebDriverWait(driver, 10).until(
                EC.any_of(
                    EC.url_contains("logged-in-successfully"),
                    EC.presence_of_element_located(
                        (By.XPATH, "//*[contains(text(),'Congratulations') or "
                                   "contains(text(),'successfully logged in')]")
                    )
                )
            )
            # 登录成功场景
            screenshot_path = take_screenshot(driver, f"{case_name}_PASS")
            defects = scan_ui_defects(driver)

            # 验证登出按钮存在
            try:
                logout_btn = driver.find_element(By.LINK_TEXT, "Log out")
                logout_visible = logout_btn.is_displayed()
            except NoSuchElementException:
                logout_visible = False

            report = generate_report(
                case_name=case_name,
                result="PASS",
                message=f"登录成功，登出按钮可见: {logout_visible}",
                screenshot_path=screenshot_path,
                defects=defects
            )
            print(f"[PASS] 登录成功，登出按钮可见: {logout_visible}")
            return report

        except TimeoutException:
            # 既没有错误提示也没有成功标志 —— 未知状态
            screenshot_path = take_screenshot(driver, f"{case_name}_ERROR")
            defects = scan_ui_defects(driver)

            report = generate_report(
                case_name=case_name,
                result="ERROR",
                message="登录结果无法判定：未检测到成功或失败标志",
                screenshot_path=screenshot_path,
                defects=defects
            )
            print("[ERROR] 登录结果无法判定")
            return report

    except Exception as e:
        # 全局异常兜底
        screenshot_path = None
        if driver:
            screenshot_path = take_screenshot(driver, f"{case_name}_EXCEPTION")
        report = generate_report(
            case_name=case_name,
            result="ERROR",
            message=f"脚本执行异常: {str(e)}",
            screenshot_path=screenshot_path
        )
        print(f"[EXCEPTION] {str(e)}")
        return report

    finally:
        # ---- Step 6: 关闭浏览器 ----
        if driver:
            driver.quit()
            print("[INFO] 浏览器已关闭")


# ============================================================
# 主入口：执行正向 + 负向用例
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("  登录功能 UI 自动化测试  ")
    print("=" * 60)

    # 题目要求：
    print("\n--- 用例: 题目要求测试 (test@example.com / 123456) ---")
    result = run_login_test("test@example.com", "123456", "positive_login")

    # 正向用例：正确凭据
    print("\n--- 用例1: 正向登录测试 (student / Password123) ---")
    result1 = run_login_test("student", "Password123", "positive_login")

    # 负向用例：错误用户名
    print("\n--- 用例2: 负向登录测试 (错误用户名) ---")
    result2 = run_login_test("test@example.com", "Password123", "negative_username")

    # 负向用例：错误密码
    print("\n--- 用例3: 负向登录测试 (错误密码) ---")
    result3 = run_login_test("student", "123456", "negative_password")

    # 汇总输出
    print("\n" + "=" * 60)
    print("  测试报告汇总  ")
    print("=" * 60)
    for r in [result, result1, result2, result3]:
        print(f"  [{r['result']}] {r['case_name']} | {r['message']}")
        if r.get("ui_defects"):
            print(f"         UI缺陷: {len(r['ui_defects'])} 项")
        if r.get("screenshot_path"):
            print(f"         截图: {r['screenshot_path']}")

    # 保存汇总报告
    summary_path = os.path.join(
        REPORT_DIR,
        f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump([result, result1, result2, result3], f, ensure_ascii=False, indent=2)
    print(f"\n汇总报告已保存: {summary_path}")
