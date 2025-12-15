# tests/conftest.py
import pytest
import os
import logging
from utils.adb_utils import AdbUtils
from config.device_config import DATA_PATH, DEVICE_ID, OUTPUT_PATH, REPORT_XLSX, REPORT_HTML,FAIL_DIR

logger = logging.getLogger("conftest")

@pytest.fixture(autouse=True, scope="function")
def clear_camera_files():
    """每条 case 执行前：保持亮屏 + 清理相机目录"""
    adb = AdbUtils(device_id=DEVICE_ID)  # 可以改成读取环境变量
    adb.shell("root")
    adb.shell("remount")

    # 设置充电时保持亮屏
    adb.keep_screen_on_while_charging(True)

    # 清理手机端和本地端的jpg/mp4
    adb.clear_media_files(remote_dir=DATA_PATH)
    yield

def pytest_sessionstart(session):
    """pytest 启动时执行，清理旧的测试报告和失败图片"""
    # 清理失败图片目录
    try:
        # 清理手机端和本地端的jpg/mp4
        adb = AdbUtils(device_id=DEVICE_ID)
        adb.clear_media_files(local_dir=OUTPUT_PATH)
        if os.path.exists(FAIL_DIR):
            for filename in os.listdir(FAIL_DIR):
                if filename.lower().endswith((".jpg", ".mp4")):
                    file_path = os.path.join(FAIL_DIR, filename)
                    try:
                        os.remove(file_path)
                        logger.info(f"[pytest] 已删除旧的失败文件: {file_path}")
                    except Exception as e:
                        logger.warning(f"[pytest] 删除 {file_path} 失败: {e}")
    except Exception as e:
        logger.warning(f"[pytest] 清理 {FAIL_DIR} 失败: {e}")