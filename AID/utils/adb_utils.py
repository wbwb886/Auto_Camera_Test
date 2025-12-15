# utils/adb_utils.py
import os
import logging

logger = logging.getLogger("AdbUtils")
class AdbUtils:
    def __init__(self, device_id: str):
        self.device_id = device_id

    def pull_all_file(self, remote_dir: str, extension: str, local_dir: str) -> str:
        """
        从指定目录中拉取最新的文件到本地
        :param remote_dir: 手机中的目录，例如 /sdcard/DCIM/Camera
        :param extension: 文件扩展名，例如 'jpg' 或 'mp4'
        :param local_dir: 本地保存目录
        :return: 本地文件路径
        """
        cmd = f"adb -s {self.device_id} shell ls {remote_dir}/*.{extension}"
        result = os.popen(cmd).read().strip()

        if not result:
            raise FileNotFoundError(f"未找到 {remote_dir} 下的 {extension} 文件")

        remote_files = result.splitlines()
        os.makedirs(local_dir, exist_ok=True)

        local_files = []
        for remote_file in remote_files:
            filename = os.path.basename(remote_file)
            local_path = os.path.join(local_dir, filename)
            logger.info(f"拉取文件: {remote_file} -> {local_path}")
            os.system(f"adb -s {self.device_id} pull {remote_file} {local_path}")
            if os.path.exists(local_path):
                local_files.append(local_path)
            else:
                logger.warning(f"文件拉取失败: {remote_file}")

        return local_files
    
    def clear_files(self, remote_dir: str, extension: str):
        """
        删除手机端指定目录下的某类文件
        """
        cmd = f"adb -s {self.device_id} shell rm {remote_dir}/*.{extension}"
        os.system(cmd)

    def clear_local_files(self, local_dir: str, extensions=("jpg", "mp4")):
        """
        删除本地目录下的指定类型文件
        """
        if os.path.exists(local_dir):
            for filename in os.listdir(local_dir):
                if filename.lower().endswith(tuple(extensions)):
                    file_path = os.path.join(local_dir, filename)
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        logger.warning(f"删除 {file_path} 失败: {e}")

    def clear_media_files(self, remote_dir=None, local_dir=None, extensions=("jpg", "mp4")):
        """
        清理手机端和/或本地的 jpg/mp4 文件
        :param remote_dir: 手机端路径，如 /sdcard/DCIM/Camera
        :param local_dir: 本地路径，如 /home/wangbo/AID/output
        """
        if remote_dir:
            for ext in extensions:
                self.clear_files(remote_dir, ext)
        if local_dir:
            self.clear_local_files(local_dir, extensions)

    def shell(self, cmd: str):
        """执行 adb shell 命令"""
        os.system(f"adb -s {self.device_id} shell {cmd}")

    def keep_screen_on_while_charging(self, enable=True):
        """
        设置充电时是否保持亮屏
        :param enable: True 开启, False 关闭
        """
        value = 3 if enable else 0
        self.shell(f"settings put global stay_on_while_plugged_in {value}")
