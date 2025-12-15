import cv2
import numpy as np
import logging, os, shutil
from glob import glob
from config.device_config import FAIL_DIR

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


class OpenCVUtils:

    @staticmethod
    def _load_image(image_path):
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"The image does not exist: {image_path}")
        img = cv2.imread(image_path)
        if img is None:
            raise RuntimeError(f"Unable to read image: {image_path}")
        return img

    # -------------------------------------------------------
    # 图片基础检查
    # -------------------------------------------------------

    @staticmethod
    def check_3a(image_path, brightness_range=(50, 200), wb_tolerance=25, sharpness_threshold=80):
        img = OpenCVUtils._load_image(image_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # AE
        brightness = float(np.mean(gray))
        exposure_ok = brightness_range[0] <= brightness <= brightness_range[1]

        # AWB
        mean_b, mean_g, mean_r = cv2.mean(img)[:3]
        wb_ok = (abs(mean_r - mean_g) < wb_tolerance and
                 abs(mean_g - mean_b) < wb_tolerance and
                 abs(mean_r - mean_b) < wb_tolerance)

        # AF
        laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        focus_ok = laplacian_var >= sharpness_threshold

        metrics = {
            "brightness": round(brightness, 2),
            "rgb_means": (round(mean_r, 2), round(mean_g, 2), round(mean_b, 2)),
            "sharpness": round(laplacian_var, 2)
        }

        return {
            "path": image_path,
            "exposure": exposure_ok,
            "white_balance": wb_ok,
            "focus": focus_ok,
            "metrics": metrics
        }

    @staticmethod
    def check_abnormal_image(image_path, brightness_threshold=30, color_ratio=1.5):
        img = OpenCVUtils._load_image(image_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        brightness = float(np.mean(gray))
        mean_b, mean_g, mean_r = cv2.mean(img)[:3]

        abnormal = None

        if brightness < brightness_threshold:
            abnormal = "black"
        elif mean_g > mean_r * color_ratio and mean_g > mean_b * color_ratio:
            abnormal = "green"
        elif (mean_r + mean_b) / 2 > mean_g * color_ratio:
            abnormal = "purple"

        return abnormal

    # -------------------------------------------------------
    # 视频检查
    # -------------------------------------------------------

    @staticmethod
    def check_video_basic(video_path):
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video does not exist: {video_path}")

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return {
                "path": video_path,
                "open_ok": False,
                "read_ok": False,
                "fps": 0,
                "frame_count": 0,
                "width": 0,
                "height": 0
            }

        fps = cap.get(cv2.CAP_PROP_FPS) or 0
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        ret, frame = cap.read()
        read_ok = ret and frame is not None

        cap.release()

        return {
            "path": video_path,
            "open_ok": True,
            "read_ok": read_ok,
            "fps": fps,
            "frame_count": frame_count,
            "width": width,
            "height": height
        }

    # -------------------------------------------------------
    # 失败统一处理
    # -------------------------------------------------------

    @staticmethod
    def _handle_fail(f, fail_dir, failures, reason):
        filename = os.path.basename(f)
        new_f = os.path.join(fail_dir, filename)
        os.makedirs(fail_dir, exist_ok=True)

        if os.path.exists(f):
            shutil.move(f, new_f)

        failures.append(f"{reason}: {new_f}")
        return new_f

    # -------------------------------------------------------
    # 核心入口：自动识别图片/视频并执行检查
    # -------------------------------------------------------

    @staticmethod
    def validate_and_collect(
            image_path,
            fail_dir=FAIL_DIR,
            check_3a=True,
            check_ae=True,
            check_awb=True,
            check_af=True,
            check_abnormal=True,
            check_video=True,
            **kwargs
    ):
        results = []
        os.makedirs(fail_dir, exist_ok=True)

        # ---------------- 文件发现逻辑 ----------------
        if os.path.isfile(image_path):
            files = [image_path]

        elif os.path.isdir(image_path):

            jpg_files = sorted(glob(os.path.join(image_path, "*.jpg")))

            video_files = []
            for ext in ["*.mp4", "*.mov", "*.avi", "*.mkv"]:
                video_files.extend(glob(os.path.join(image_path, ext)))

            files = jpg_files + video_files

            if not files:
                raise FileNotFoundError(f"No images or videos found in: {image_path}")

        else:
            raise FileNotFoundError(f"Invalid path: {image_path}")

        failures = []

        # -------------------------------------------------------
        # 遍历所有图片/视频
        # -------------------------------------------------------

        for f in files:
            original_f = f
            img_failed = False
            result = {"path": f}

            is_image = f.lower().endswith(".jpg")
            is_video = f.lower().endswith((".mp4", ".mov", ".avi", ".mkv"))

            # ---------------- 图片检查 ----------------
            if is_image:

                # --- 3A ---
                if check_3a:
                    r3a = OpenCVUtils.check_3a(f, **kwargs)
                    result.update(r3a)

                    if check_ae and not r3a["exposure"]:
                        f = OpenCVUtils._handle_fail(
                            f, fail_dir, failures,
                            f"AE FAIL (brightness={r3a['metrics']['brightness']})"
                        )
                        img_failed = True

                    if check_awb and not r3a["white_balance"]:
                        f = OpenCVUtils._handle_fail(
                            f, fail_dir, failures,
                            f"AWB FAIL (rgb={r3a['metrics']['rgb_means']})"
                        )
                        img_failed = True

                    if check_af and not r3a["focus"]:
                        f = OpenCVUtils._handle_fail(
                            f, fail_dir, failures,
                            f"AF FAIL (sharpness={r3a['metrics']['sharpness']})"
                        )
                        img_failed = True

                # --- 异常图 ---
                if check_abnormal:
                    abnormal = OpenCVUtils.check_abnormal_image(f)
                    result["abnormal"] = abnormal
                    if abnormal:
                        f = OpenCVUtils._handle_fail(
                            f, fail_dir, failures,
                            f"Abnormal FAIL ({abnormal})"
                        )
                        img_failed = True

            # ---------------- 视频检查 ----------------
            if is_video and check_video:
                v = OpenCVUtils.check_video_basic(f)

                if not v["open_ok"]:
                    failures.append(f"VIDEO FAIL: cannot open → {f}")

                if not v["read_ok"]:
                    failures.append(f"VIDEO FAIL: cannot read first frame → {f}")

                result["video"] = v

            results.append(result)

        # -------------------------------------------------------
        # 最终结果
        # -------------------------------------------------------
        if failures:
            return "FAIL", ";".join(failures)
        else:
            return "PASS", ""
