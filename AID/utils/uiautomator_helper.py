# utils/uiautomator_helper.py
import uiautomator2 as u2
import time
import os
import logging
from utils.adb_utils import AdbUtils
from config.device_config import CAMERA_APP_ACTIVITY, DATA_PATH, OUTPUT_PATH

WAIT = 2

# 日志配置
logger = logging.getLogger("UIAutomatorHelper")
logger.setLevel(logging.DEBUG)  # 控制日志最低级别

# 控制台输出
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# 文件输出（保存到 logs/uiautomator.log）
os.makedirs("logs", exist_ok=True)
file_handler = logging.FileHandler("logs/uiautomator.log", encoding="utf-8")
file_handler.setLevel(logging.DEBUG)

# 日志格式
formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s", 
    datefmt="%Y-%m-%d %H:%M:%S"
)
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# 避免重复添加 handler
if not logger.handlers:
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

#id
pic_vid_button = "com.android.camera:id/snap_layout"
more_mode_button = "com.android.camera:id/menu_indicator"
#text


class UIAutomatorHelper:
    def __init__(self, device_id=None):
        self.device = u2.connect(device_id) if device_id else u2.connect()
        self.device_id = self.device.serial
        self.adb = AdbUtils(device_id or self.device.serial)
        logger.info(f"已连接设备: {self.device_id}")


    def open_camera(self):
        """打开相机应用"""
        logger.info("正在打开相机应用...")
        self.device.press("home")
        time.sleep(1)
        os.system(f"adb -s {self.device_id} shell am start -S -W -n {CAMERA_APP_ACTIVITY}")
        time.sleep(5)
        logger.debug("相机应用已启动")


    def take_picture(self, loops):
        """拍照"""
        logger.info("正在拍照...")
        for i in range(loops):
            logger.info(f"......loop {i+1}......")
            self.device(resourceId=pic_vid_button).click()
            time.sleep(WAIT)
        logger.debug("拍照完成")


    def back_to_home(self):
        """返回主屏幕"""
        logger.info("返回主屏幕")
        self.device.press("home")
        time.sleep(WAIT)


    def start_recording(self):
        """开始录像"""
        logger.info("开始录像...")
        if self.device(resourceId=pic_vid_button).exists:
            self.device(resourceId=pic_vid_button).click()
        else:
            logger.error("未找到录像开始按钮")
            raise RuntimeError("未找到录像开始按钮")


    def stop_recording(self):
        """停止录像"""
        logger.info("停止录像...")
        if self.device(resourceId=pic_vid_button).exists:
            self.device(resourceId=pic_vid_button).click()
        else:
            logger.error("未找到录像停止按钮")
            raise RuntimeError("未找到录像停止按钮")


    def switch_video_mode(self):
        """切换视频模式"""
        logger.info("切换视频模式")
        if self.device(text="录像").exists:
            self.device(text="录像").click()
        else:
            logger.error("未找到视频按钮")
            raise RuntimeError("未找到视频按钮")
        time.sleep(5)


    def switch_camera_mode(self):
        """切换拍照模式"""
        logger.info("切换拍照模式")
        if self.device(text="拍照").exists:
            self.device(text="拍照").click()
        else:
            logger.error("未找到拍照按钮")
            raise RuntimeError("未找到拍照按钮")
        time.sleep(5)


    def switch_protrait_mode(self):
        """切换人像模式"""
        logger.info("切换人像模式")
        if self.device(text="人像").exists:
            self.device(text="人像").click()
            time.sleep(WAIT)
        else:
            logger.error("未找到人像按钮")
            raise RuntimeError("未找到人像按钮")
        time.sleep(5)


    def switch_more_mode(self):
        """切换到功能菜单"""
        logger.info("切换到功能菜单")
        if self.device(resourceId=more_mode_button).exists:
            self.device(resourceId=more_mode_button).click()
            time.sleep(WAIT)
        else:
            logger.error("未找到功能菜单按钮")
            raise RuntimeError("未找到功能菜单按钮")
        time.sleep(3)


    def set_live_photo(self, enable=None):
        """
        控制动态照片Live Photo开关
        """
        btn_off = self.device(description="动态照片，关闭状态")
        btn_on = self.device(description="动态照片，开启状态")

        # --- 读取当前状态 ---
        if btn_off.exists:
            current_state = False
        elif btn_on.exists:
            current_state = True
        else:
            logger.error("未找到动态照片按钮")
            raise RuntimeError("未找到动态照片按钮")

        # --- live photo auto ---
        if enable is None:
            logger.info("自动切换 Live Photo 状态")
            (btn_off if btn_off.exists else btn_on).click()
            time.sleep(WAIT)
            return

        # --- live photo on ---
        if enable and not current_state:
            logger.info("开启 Live Photo")
            btn_off.click()
            time.sleep(WAIT)
            return

        # --- live photo off ---
        if not enable and current_state:
            logger.info("关闭 Live Photo")
            btn_on.click()
            time.sleep(WAIT)
            return


    def set_zoom(self, zoom_level):
        """
        切换zoom倍率
        """
        try:
            zoom_str = f"{float(zoom_level):.1f}"
        except:
            raise ValueError(f"zoom_level 参数无效：{zoom_level}")

        target_desc = f"{zoom_str}倍变焦"

        logger.info(f"切换到Zoom: {target_desc}")

        node = self.device(description=target_desc)

        if node.exists:
            node.click()
            time.sleep(1)
            return True
        else:
            time.sleep(1)
            if node.exists:
                node.click()
                logger.info(f"Zoom 设置成功(第2次): {target_desc}")
                return True

            logger.error(f"未找到 Zoom UI 元素：{target_desc}")
            raise RuntimeError(f"找不到 zoom UI:{target_desc}")
        
    def set_ratio(self, ratio: str = "3:4"):
        """
        切换画幅
        ratio: 支持 "1:1", "3:4", "16:9", "full"
            默认 "3:4"
        """
        ratio_map = {
            "1:1": "画幅一比一",
            "3:4": "画幅三比四",
            "9:16": "画幅九比十六",
            "full": "画幅全屏"
        }

        if ratio not in ratio_map:
            raise ValueError(f"ratio 参数无效: {ratio}, 仅支持 {list(ratio_map.keys())}")

        target_desc = ratio_map[ratio]

        # 1. 打开更多模式菜单
        self.switch_more_mode()

        # 2. 点击“画幅”按钮
        if not self.device(text="画幅").exists:
            logger.error("未找到画幅入口 UI 元素")
            raise RuntimeError("未找到画幅入口")
        self.device(text="画幅").click()
        time.sleep(WAIT)

        # 3. 点击对应画幅
        logger.info(f"点击画幅选项: {target_desc}")
        el = self.device(description=target_desc)
        if not el.exists:
            logger.error(f"未找到 UI 元素: {target_desc}")
            raise RuntimeError(f"画幅选项不存在: {target_desc}")

        el.click()
        time.sleep(WAIT)
        logger.info(f"画幅切换成功: {ratio}")


    def pull_all_photo(self):
        """拉取所有照片"""
        time.sleep(10)
        logger.info("拉取所有照片...")
        path = self.adb.pull_all_file(DATA_PATH, "jpg", OUTPUT_PATH)
        logger.debug(f"照片已保存到: {path}")
        return path

    def pull_all_video(self):
        """拉取所有视频"""
        time.sleep(10)
        logger.info("拉取所有视频...")
        path = self.adb.pull_all_file(DATA_PATH, "mp4", OUTPUT_PATH)
        logger.debug(f"视频已保存到: {path}")
        return path