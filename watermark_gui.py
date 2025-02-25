import json
import os
import re
import sys
import threading
from datetime import datetime
from tkinter.font import Font
from tkinter.ttk import Button, Entry, Label, Checkbutton, Scrollbar, Radiobutton, Spinbox

import pytz
from PIL import Image, ImageDraw, ImageFont
from PIL.ExifTags import TAGS
import subprocess
import logging
import shutil
import tkinter as tk
from tkinter import filedialog, StringVar, IntVar, OptionMenu, END, NORMAL, DISABLED

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def get_photo_capture_time(image_path, out_date_format=0):
    try:
        image = Image.open(image_path)
        exif_data = image.getexif()
        if exif_data:
            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)
                if tag == "DateTime":
                    date_format = "%Y:%m:%d %H:%M:%S"
                    date_time_obj = datetime.strptime(value, date_format)
                    if out_date_format == 1:
                        formatted = r"%Y-%m-%d"
                    elif out_date_format == 2:
                        formatted = r"%Y/%m/%d"
                    else:
                        formatted = r"%Y年%m月%d日"
                    formatted_date_str = date_time_obj.strftime(formatted)
                    return formatted_date_str
    except Exception as e:
        print(f"无法读取照片信息：{e}")
    return None


def is_color(color_str):
    try:
        if color_str is None or not isinstance(color_str, str):
            return False
        # 去除 '#' 和 '0x' 前缀
        cleaned = color_str.lstrip('#').lstrip('0x')
        # 检查是否只包含16进制字符
        if not all(c in "0123456789abcdefABCDEF" for c in cleaned):
            return False

        # 确保长度符合要求（6位RGB或8位RGBA）
        if len(cleaned) == 6 or len(cleaned) == 8:
            return True
        else:
            return False
    except Exception as e:
        print(f"err:{e}")
        return False


def convert_color_to_numeric(color_str):
    """
    将颜色字符串转换为纯数字表示。
    支持的格式包括：233D9E64、3D9E64、#3D9E64、#233D9E64、0x233D9E64、0x3D9E64
    如果输入无效，则返回白色 (#FFFFFFFF) 的数值表示。
    """
    try:
        if color_str is None or not isinstance(color_str, str):
            return "FFFFFFFF"
        # 去除 '#' 和 '0x' 前缀
        cleaned = color_str.lstrip('#').lstrip('0x')

        # 检查是否只包含16进制字符
        if not all(c in "0123456789abcdefABCDEF" for c in cleaned):
            raise ValueError("Invalid character found in color string.")

        # 确保长度符合要求（6位RGB或8位RGBA）
        if len(cleaned) == 6 or len(cleaned) == 8:
            return cleaned
        else:
            raise ValueError("Color string must be either 6 (for RGB) or 8 (for RGBA) hexadecimal digits long.")
    except Exception as e:
        print(f"Error with '{color_str}': {e}")
        # 返回白色 (#FFFFFFFF) 的数值表示
        return "FFFFFFFF"


def add_text_watermark2(input_image_path, output_image_path, watermark_text, font_size=40, txt_position=0,
                        txt_padding=20, h_padding=40, bg_alpha=0, text_color_hex="FFFFFF", font_type='simsun.ttc'):
    try:
        base_image = Image.open(input_image_path).convert("RGBA")
        watermark = Image.new("RGBA", base_image.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(watermark)
        min_plex = min(base_image.size[0], base_image.size[1])
        size = max(int(min_plex / 24 * font_size / 40), 6)  # 根据图像宽度设置字体大小
        font = ImageFont.truetype(font_type, size)  # 替换为你的字体文件路径
        bbox = draw.textbbox((0, 0), watermark_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        width, height = base_image.size
        padding = int(text_height * txt_padding / 40)
        h_padding = int(text_height * h_padding / 40)
        if watermark_text.find("\n") != -1:
            h_padding = int(h_padding / 2)
            padding = int(text_height * txt_padding / 80)
        position = (padding, height - text_height - h_padding)
        if txt_position == 0:
            position = (padding, height - text_height - h_padding)
        elif txt_position == 1:
            position = (width - text_width - padding, height - text_height - h_padding)
        elif txt_position == 2:
            position = (padding, h_padding)
        elif txt_position == 3:
            position = (width - text_width - padding, h_padding)
        bg_color = (0, 0, 0, bg_alpha)
        bg_position = (
            position[0] - 12, position[1] - 12, position[0] + text_width + 12, position[1] + text_height + 20)
        draw.rectangle(bg_position, fill=bg_color)
        text_color = "#" + text_color_hex
        draw.text(position, watermark_text, font=font, fill=text_color)
        combined = Image.alpha_composite(base_image, watermark)
        combined = combined.convert("RGB")
        combined.save(output_image_path)
        return True
    except Exception as e:
        print(f"err:{e}")
        return False


def get_video_creation_date(video_path, out_date_format=0):
    try:
        if getattr(sys, 'frozen', False):
            ffmpeg_dir = resource_path('ffmpeg')
            ffprobe_path = os.path.join(ffmpeg_dir, 'bin', 'ffprobe.exe')
        else:
            ffprobe_path = r"F:\ffmpeg-master-latest-win64-gpl-shared\bin\ffprobe.exe"
        command = [
            ffprobe_path,
            '-v', 'quiet',
            '-select_streams', 'v:0',
            '-show_entries', 'stream_tags=creation_time',
            '-of', 'default=nw=1:nk=1',
            video_path
        ]
        startupinfo = None
        if hasattr(subprocess, 'STARTUPINFO'):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8',
                                startupinfo=startupinfo)
        if result.returncode != 0:
            logging.error(f"错误信息：{result.stderr}")
            return None
        creation_time_str = result.stdout.strip()
        if not creation_time_str:
            return None
        creation_time_utc = datetime.strptime(creation_time_str, '%Y-%m-%dT%H:%M:%S.%fZ')
        utc_timezone = pytz.timezone('UTC')
        creation_time_utc = utc_timezone.localize(creation_time_utc)
        china_timezone = pytz.timezone('Asia/Shanghai')
        creation_time_cst = creation_time_utc.astimezone(china_timezone)
        if out_date_format == 1:
            formatted = r"%Y-%m-%d"
        elif out_date_format == 2:
            formatted = r"%Y/%m/%d"
        else:
            formatted = r"%Y年%m月%d日"
        creation_date_cst = creation_time_cst.strftime(formatted)
        return creation_date_cst
    except Exception as e:
        logging.error(f"详细错误信息：{str(e)}")
        return None


def copy_video_and_rename(src_path, dst_path):
    try:
        shutil.copy(src_path, dst_path)
        return True
    except Exception as e:
        print(f"发生了一个错误: {e}")
        return False


def get_video_dimensions(video_path):
    default_width = 720
    default_height = 1280
    try:
        # 执行 ffmpeg -i 命令
        command = ['ffmpeg', '-i', video_path]
        # 执行命令并获取输出
        startupinfo = None
        if hasattr(subprocess, 'STARTUPINFO'):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
        # 将字节类型的 stderr 解码为字符串
        output = result.stderr.decode()
        # 使用正则表达式匹配宽高信息
        # 匹配视频流信息中的宽高，确保匹配到的是视频流部分的宽高
        match = re.search(r'Stream #0:0.*?\s+(\d+)x(\d+)\s+\[', output)
        if match:
            width = int(match.group(1))
            height = int(match.group(2))
            return width, height
    except subprocess.CalledProcessError as e:
        print(f"警告: 执行 ffmpeg 命令失败: {e.stderr.decode()}")
    except Exception as e:
        print(f"警告: 获取视频尺寸时发生未知错误: {str(e)}")
    return default_width, default_height


def add_watermark_ffmpeg(src_path, dst_path, watermark_text, font_size=40, txt_position=0, padding=20, h_padding=40,
                         text_color_hex=None, font_type='simsun.ttc', watermark_type='text', watermark_image_path=None,
                         watermark_width=0, watermark_height=0):
    try:
        if getattr(sys, 'frozen', False):
            ffmpeg_dir = resource_path('ffmpeg')
            ffmpeg_path = os.path.join(ffmpeg_dir, 'bin', 'ffmpeg.exe')
        else:
            ffmpeg_path = r"F:\ffmpeg-master-latest-win64-gpl-shared\bin\ffmpeg.exe"
        if not os.path.exists(ffmpeg_path):
            return False
        x = f'{padding}'
        if watermark_type == 'text':
            h_padding = int(h_padding * 0.7)
            font_path = rf'C:/Windows/Fonts/{font_type}'
            if not os.path.exists(font_path):
                return False
            y = f'(h - text_h)-{h_padding}'
            if txt_position == 0:
                x = f'{padding}'
                y = f'(h - text_h)-{h_padding}'
            elif txt_position == 1:
                x = f'(w - text_w)-{padding}'
                y = f'(h - text_h)-{h_padding}'
            elif txt_position == 2:
                x = f'{padding}'
                y = f'{padding}'
            elif txt_position == 3:
                x = f'(w - text_w)-{padding}'
                y = f'{h_padding}'
            text_color = convert_color_to_numeric(text_color_hex)
            command_str = rf'{ffmpeg_path} -y -i "{src_path}" -vf "drawtext=fontfile=\'{font_path}\':text=\'{watermark_text}\':fontsize={int(font_size * 0.8)}:fontcolor={text_color}:box=1:boxcolor=black@0:boxborderw=5:x={x}:y={y}" -c:a copy "{dst_path}"'
        else:
            watermark = Image.open(watermark_image_path).convert("RGBA")
            wm_width, wm_height = watermark.size
            video_width, video_height = get_video_dimensions(src_path)
            print(f"video_width:{video_width};video_height:{video_height}")
            if watermark_width > 0 and watermark_height > 0:
                w_width = watermark_width
                w_height = watermark_height
            elif watermark_width == 0 and watermark_height > 0:
                w_width = int(wm_width / wm_height * watermark_height)
                w_height = watermark_height
            elif watermark_width > 0 and watermark_height == 0:
                w_width = wm_width
                w_height = int(watermark_width / wm_width * wm_height)
            else:
                w_width = int(wm_width * 0.4)
                w_height = int(wm_height * 0.4)
            y = video_height - w_height - h_padding
            if txt_position == 0:
                x = padding
                y = video_height - w_height - h_padding
            elif txt_position == 1:
                x = video_width - w_width - padding
                y = video_height - w_height - h_padding
            elif txt_position == 2:
                x = padding
                y = h_padding
            elif txt_position == 3:
                x = video_width - w_width - padding
                y = h_padding
            command_str = rf'{ffmpeg_path} -y -i "{src_path}" -i "{watermark_image_path}"  -filter_complex  "[1:v]scale={w_width}:{w_height}[wm];[0:v][wm]overlay={x}:{y}" -c:a copy "{dst_path}"'
        print(command_str)
        # 使用CREATE_NO_WINDOW标志来隐藏CMD窗口
        startupinfo = None
        if hasattr(subprocess, 'STARTUPINFO'):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        result = subprocess.run(command_str, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
        if result.returncode == 0:
            print(f"视频处理成功：{src_path} -> {dst_path}")
            return True
        else:
            return False
    except subprocess.CalledProcessError as e:
        logging.error(f"FFmpeg 错误信息：{e.stderr.decode()}")
        return False
    except Exception as e:
        logging.error(f"FFmpeg {src_path} 错误信息： {str(e)}")
        return False


def add_image_watermark(input_image_path, output_image_path, watermark_image_path, img_position=0, watermark_width=0,
                        watermark_height=0, w_padding=20, h_padding=20):
    try:
        base_image = Image.open(input_image_path).convert("RGBA")
        watermark = Image.open(watermark_image_path).convert("RGBA")
        # 获取水印图像的宽度和高度
        wm_width, wm_height = watermark.size
        # 确定水印位置，默认为左上角
        width, height = base_image.size
        # 调整水印大小（如果需要）
        if watermark_width > 0 and watermark_height > 0 and wm_width < width and wm_height < height:
            watermark = watermark.resize((watermark_width, watermark_height))
        elif watermark_width == 0 and watermark_height > 0:
            watermark = watermark.resize((int(wm_width / wm_height * watermark_height), watermark_height))
        elif watermark_width > 0 and watermark_height == 0:
            watermark = watermark.resize((wm_width, int(watermark_width / wm_width * wm_height)))
        elif watermark_width > width or watermark_height > height:
            watermark = watermark.resize((wm_width, wm_height))
        elif wm_width > width or wm_height > height:
            watermark = watermark.resize((width, height))
        else:
            watermark = watermark.resize((wm_width, wm_height))
        # 获取截取尺寸的尺寸
        wm_width, wm_height = watermark.size
        # 水印位置
        if img_position == 3:
            position = (width - wm_width - w_padding, h_padding)
        elif img_position == 2:
            position = (w_padding, h_padding)
        elif img_position == 1:
            position = (width - wm_width - w_padding, height - wm_height - h_padding)
        else:
            position = (w_padding, height - wm_height - h_padding)
        # 创建一个新的透明图层
        transparent = Image.new('RGBA', base_image.size, (0, 0, 0, 0))
        # 将水印粘贴到透明图层上
        transparent.paste(base_image, (0, 0))
        transparent.paste(watermark, position, mask=watermark)
        # 转换回RGB并保存结果
        final_image = transparent.convert("RGB")
        final_image.save(output_image_path)
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


def is_valid_watermark_image(watermark_image_path):
    # 检查文件是否存在
    if not os.path.exists(watermark_image_path):
        print(f"Error: File does not exist: {watermark_image_path}")
        return False
    try:
        # 尝试打开并验证图像
        with Image.open(watermark_image_path) as img:
            img.verify()  # 验证图像完整性
            # 再次打开图像以进行进一步的检查
            img = Image.open(watermark_image_path).convert("RGBA")
            # 检查图像尺寸
            width, height = img.size
            if width == 0 or height == 0:
                print(f"Error: Invalid image size: {width}x{height}")
                return False
            # 检查图像模式
            if img.mode not in ["RGB", "RGBA"]:
                print(f"Error: Unsupported image mode: {img.mode}")
                return False
            # 可选：检查文件大小（例如不超过5MB）
            file_size = os.path.getsize(watermark_image_path)
            max_size_bytes = 5 * 1024 * 1024  # 5 MB
            if file_size > max_size_bytes:
                print(f"Error: File too large: {file_size / (1024 * 1024):.2f} MB")
                return False
            return True
    except IOError as e:
        print(f"Error: Not a valid image file: {e}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False


def process_directory(root_dir, out_path=None, out_file_name=None, is_add_video_water=False, out_date_format=0,
                      font_size=40, txt_position=0, padding=20, h_padding=40, log_func=None, text_color_hex=None,
                      insert_watermark=None, font_type='simsun.ttc', watermark_type='text', watermark_image_path=None,
                      watermark_width=0, watermark_height=0):
    # 边距仅对文字水印有效，图片水印不在针对不同尺寸的照片进行相关尺寸自适应适配
    if watermark_type == 'text':
        if font_size < 1 or font_size > 100:
            font_size = 40
        if padding < 0 or padding > 200:
            padding = 20
        if h_padding < 0 or h_padding > 200:
            h_padding = 40
    for subdir, dirs, files in os.walk(root_dir):
        if insert_watermark:
            watermark_text = insert_watermark
        else:
            watermark_text = ''.join([char for char in os.path.basename(subdir) if '\u4e00' <= char <= '\u9fff'])
        file_counter = 1
        for file_name in files:
            mark_text = watermark_text
            base_name, ext = os.path.splitext(file_name)
            if out_file_name is None:
                new_file_name = file_name
            else:
                new_file_name = f"{out_file_name}_{file_counter}{ext}"
            input_image_path = os.path.join(subdir, file_name)
            if out_path is None:
                out_dir = f"{root_dir}_out"
                relative_path = os.path.relpath(subdir, root_dir)
                save_dir = os.path.join(out_dir, relative_path)
            else:
                relative_path = os.path.relpath(subdir, root_dir)
                save_dir = os.path.join(out_path, relative_path)
            # 照片添加水印
            if file_name.lower().endswith(('png', 'jpg', 'jpeg')):
                os.makedirs(save_dir, exist_ok=True)
                output_image_path = os.path.join(save_dir, new_file_name)
                if watermark_type == 'text':
                    if insert_watermark is None:
                        create_date = get_photo_capture_time(input_image_path, out_date_format)
                        if create_date:
                            mark_text = f"{create_date}\n{watermark_text}"
                    success = add_text_watermark2(input_image_path, output_image_path, mark_text, font_size,
                                                  txt_position, padding, h_padding, 0, text_color_hex, font_type)
                else:
                    success = add_image_watermark(input_image_path, output_image_path, watermark_image_path,
                                                  txt_position,
                                                  watermark_width, watermark_height, padding, h_padding)
            # 视频添加水印
            elif file_name.lower().endswith('mp4'):
                os.makedirs(save_dir, exist_ok=True)
                output_image_path = os.path.join(save_dir, new_file_name)
                if is_add_video_water:
                    if watermark_type == 'text':
                        if insert_watermark is None:
                            create_date = get_video_creation_date(input_image_path, out_date_format)
                            if create_date:
                                mark_text = f"{create_date}\n{watermark_text}"
                    success = add_watermark_ffmpeg(input_image_path, output_image_path, mark_text, font_size,
                                                   txt_position, padding, h_padding, text_color_hex, font_type,
                                                   watermark_type, watermark_image_path, watermark_width,
                                                   watermark_height)
                else:
                    success = copy_video_and_rename(input_image_path, output_image_path)
            else:
                continue
            if success:
                if log_func:
                    log_func(f"已处理: {input_image_path} -> {output_image_path}", "gray")  # 中间信息使用灰色字体
                file_counter += 1
            else:
                if log_func:
                    log_func(f"处理失败: {input_image_path}", "red")  # 错误信息使用红色字体


def quality_percentage_to_qv(percentage):
    """
    将压缩质量百分比转换为 -q:v 参数值。
    :param percentage: 质量百分比 (0-100)
    :return: 对应的 -q:v 参数值
    """
    if percentage < 0 or percentage > 100:
        percentage = 75
    # 计算 -q:v 值，假设100%对应-q:v 1, 0%对应-q:v 31
    qv_value = 32 - (percentage / 100) * 31
    return round(qv_value)  # 四舍五入取整


def compress_ratio_to_crf(compress_ratio):
    """
    将压缩比例（0% 到 100%）映射到 -crf 参数（0 到 51）。
    """
    if not (0 <= compress_ratio <= 100):
        compress_ratio = 80
    # 线性映射
    crf_value = 18 + (100 - compress_ratio) / 100 * 31
    return round(crf_value)


def compress_process_directory(root_dir, out_path, out_file_name, is_add_video_water, log_func=None, quality=75,
                               photo_format=0, video_format=0, deal_size_way="original_size", scale=100, width=1080,
                               height=1920, crop_center=0, crop_width=720, crop_height=720):
    for subdir, dirs, files in os.walk(root_dir):
        file_counter = 1
        for file_name in files:
            base_name, ext = os.path.splitext(file_name)
            if out_file_name is None:
                new_file_name = file_name
            else:
                new_file_name = f"{out_file_name}_{file_counter}{ext}"
            input_image_path = os.path.join(subdir, file_name)
            if out_path is None:
                out_dir = f"{root_dir}_out"
                relative_path = os.path.relpath(subdir, root_dir)
                save_dir = os.path.join(out_dir, relative_path)
            else:
                relative_path = os.path.relpath(subdir, root_dir)
                save_dir = os.path.join(out_path, relative_path)
            success = False
            output_image_path = None
            # 照片压缩
            if file_name.lower().endswith(('png', 'jpg', 'jpeg', 'webp')):
                os.makedirs(save_dir, exist_ok=True)
                extensions = {1: 'png', 2: 'jpeg', 3: 'webp'}
                if photo_format in extensions:
                    output_image_path = "{}.{}".format(os.path.join(save_dir, new_file_name), extensions[photo_format])
                else:
                    output_image_path = os.path.join(save_dir, new_file_name)
                photo_scale = 'scale=iw*1:ih*1'
                if deal_size_way == "scale_size":
                    photo_scale = f'scale=iw*{scale / 100}:ih*{scale / 100}'
                elif deal_size_way == "specify_size":
                    photo_scale = f'scale={width}:{height}'
                elif deal_size_way == "crop_size":
                    if crop_center == 1:
                        photo_scale = f'crop=min({crop_width}\\, in_w):min({crop_height}\\, in_h):0:0'
                    elif crop_center == 2:
                        photo_scale = f'crop=min({crop_width}\\, in_w):min({crop_height}\\, in_h):(in_w-min({crop_width}\\, in_w)):0'
                    elif crop_center == 3:
                        photo_scale = f'crop=min({crop_width}\\, in_w):min({crop_height}\\, in_h):0:(in_h-min({crop_height}\\, in_h))'
                    elif crop_center == 4:
                        photo_scale = f'crop=min({crop_width}\\, in_w):min({crop_height}\\, in_h):(in_w-min({crop_width}\\, in_w)):(in_h-min({crop_height}\\, in_h))'
                    else:
                        photo_scale = f'crop=min(iw\\,{crop_width}):min(ih\\,{crop_height}):(iw-min(iw\\,{crop_width}))/2:(ih-min(ih\\,{crop_height}))/2'

                command_str = rf'ffmpeg -y -i "{input_image_path}" -vf "{photo_scale}" -q:v {quality_percentage_to_qv(quality)} -update 1 "{output_image_path}"'
                print(command_str)
                startupinfo = None
                if hasattr(subprocess, 'STARTUPINFO'):
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                result = subprocess.run(command_str, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                        startupinfo=startupinfo)
                success = result.returncode == 0
            # 视频压缩
            elif file_name.lower().endswith(('mp4', 'avi', 'mov', 'flv', 'wmv', 'mpeg', 'mpg')):
                os.makedirs(save_dir, exist_ok=True)
                output_image_path = os.path.join(save_dir, new_file_name)
                if is_add_video_water:
                    extensions = {1: 'mp4', 2: 'avi', 3: 'mov', 4: 'flv', 5: 'wmv', 6: 'mpeg', 7: 'mpg'}
                    if video_format in extensions:
                        output_image_path = "{}.{}".format(os.path.join(save_dir, new_file_name),
                                                           extensions[video_format])
                    command_str = rf'ffmpeg -y -i "{input_image_path}" -crf {compress_ratio_to_crf(quality)} -b:v 500k -r 24 -b:a 128k "{output_image_path}"'
                    print(command_str)
                    startupinfo = None
                    if hasattr(subprocess, 'STARTUPINFO'):
                        startupinfo = subprocess.STARTUPINFO()
                        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    result = subprocess.run(command_str, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                            startupinfo=startupinfo)
                    success = result.returncode == 0
                else:
                    success = copy_video_and_rename(input_image_path, output_image_path)
            if success:
                if log_func:
                    log_func(f"已处理: {input_image_path} -> {output_image_path}", "gray")  # 中间信息使用灰色字体
                file_counter += 1
            else:
                if log_func:
                    log_func(f"处理失败: {input_image_path}", "red")  # 错误信息使用红色字体


def is_integer(value):
    """
    判断一个值是否为整型。
    支持 int、float（整数值）、和可转换为整数的字符串。
    """
    if isinstance(value, int):
        return True
    elif isinstance(value, float):
        return value.is_integer()
    elif isinstance(value, str):
        try:
            float_value = float(value)
            return float_value.is_integer()
        except ValueError:
            return False
    else:
        try:
            int(value)
            return True
        except (ValueError, TypeError):
            return False


class PlaceholderEntry(Entry):
    def __init__(self, master=None, placeholder="请输入内容", placeholder_color='grey', **kwargs):
        super().__init__(master, **kwargs)
        self.placeholder = placeholder
        self.placeholder_color = placeholder_color
        self.default_fg_color = self['foreground']

        self.bind("<FocusIn>", self.foc_in)
        self.bind("<FocusOut>", self.foc_out)

        self.put_placeholder()

    def put_placeholder(self):
        self.delete('0', 'end')
        self.insert(0, self.placeholder)
        self['foreground'] = self.placeholder_color

    def foc_in(self, *args):
        if self.get() == self.placeholder:
            self.delete('0', 'end')
            self['foreground'] = self.default_fg_color

    def foc_out(self, *args):
        if not self.get():
            self.put_placeholder()


class App:
    def __init__(self, master):
        self.txt_position = None
        self.out_date_format = None
        self.out_photo_format = None
        self.out_video_format = None
        self.font_type = None
        self.crop_center = None
        self.master = master
        master.title("批量加水印工具")

        # 初始化变量
        self.root_dir_var = tk.StringVar()
        self.out_path_var = tk.StringVar()
        self.out_file_name_var = tk.StringVar()
        self.is_add_video_water_var = tk.IntVar(value=0)
        self.font_size_var = tk.IntVar(value=40)
        self.padding_var = tk.IntVar(value=20)
        self.h_padding_var = tk.IntVar(value=40)
        self.text_color_hex_var = tk.StringVar(value="#FFFFFFFF")
        self.insert_watermark_var = tk.StringVar()
        self.watermark_type = tk.StringVar(value="text")
        self.img_water_width = tk.IntVar(value=0)
        self.img_water_height = tk.IntVar(value=0)
        self.size_process = tk.StringVar(value="original_size")
        self.spinbox_quality = tk.IntVar(value=75)
        self.spinbox_scale = tk.IntVar(value=80)
        self.size_width = tk.IntVar(value=1080)
        self.size_height = tk.IntVar(value=1920)
        self.crop_width = tk.IntVar(value=720)
        self.crop_height = tk.IntVar(value=720)
        # 日期格式和水印位置映射
        self.date_format_map = {
            "Y年M月D日": 0,
            "Y-M-D": 1,
            "Y/M/D": 2
        }
        self.photo_format_map = {
            "原始格式": 0,
            "png": 1,
            "jpeg": 2,
            "webp": 3
        }
        self.video_format_map = {
            "原始格式": 0,
            'mp4': 1,
            'avi': 2,
            'mov': 3,
            'flv': 4,
            'wmv': 5,
            'mpeg': 6,
            'mpg': 7
        }
        self.crop_center_map = {
            "居中": 0,
            "左上角": 1,
            "右上角": 2,
            "左下角": 3,
            "右下角": 4,
        }
        self.font_map = {
            "仿宋": 'simfang.ttf',  # 仿宋字体
            "宋体": 'simsun.ttc',  # 宋体
            "黑体": 'simhei.ttf',  # 黑体
            "微软雅黑": 'msyh.ttc',  # 微软雅黑
            "楷体": 'simkai.ttf',  # 楷体
            "等线": 'Deng.ttf',  # 等线
            "Arial": 'arial.ttf',  # Arial
            "Calibri": 'calibri.ttf',  # Calibri
            "Cambria": 'cambria.ttc',  # Cambria
            "Verdana": 'verdana.ttf',  # Verdana
            "Tahoma": 'tahoma.ttf',  # Tahoma
            "Segoe UI": 'segoeui.ttf',  # Segoe UI
            "Consolas": 'consola.ttf',  # Consolas
            "Georgia": 'georgia.ttf',  # Georgia
            "Impact": 'impact.ttf',  # Impact
            "Symbol": 'symbol.ttf',  # Symbol
            "Webdings": 'webdings.ttf',  # Webdings
            "Wingdings": 'wingding.ttf',  # Wingdings
        }
        self.txt_position_map = {
            "左上角": 2,
            "右上角": 3,
            "左下角": 0,
            "右下角": 1
        }

        # 界面布局
        Label(master, text="导入目录(*):", foreground="red").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        Entry(master, textvariable=self.root_dir_var, width=50).grid(row=0, column=1, padx=5, pady=5)
        Button(master, text="浏览", command=self.browse_root_dir).grid(row=0, column=2, padx=5, pady=5)

        Label(master, text="导出目录(*):", foreground="red").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        Entry(master, textvariable=self.out_path_var, width=50).grid(row=1, column=1, padx=5, pady=5)
        Button(master, text="浏览", command=self.browse_out_path).grid(row=1, column=2, padx=5, pady=5)

        Label(master, text="操作类型:", foreground="blue").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        Radiobutton(master, text="文字水印", variable=self.watermark_type, value="text",
                    command=self.update_widgets).grid(row=2, column=1, sticky="w", padx=5, pady=5)
        Radiobutton(master, text="图像水印", variable=self.watermark_type, value="image",
                    command=self.update_widgets).grid(row=2, column=1, sticky="e", padx=5, pady=5)
        Radiobutton(master, text="压缩优化", variable=self.watermark_type, value="compress",
                    command=self.update_widgets).grid(row=3, column=1, sticky="w", padx=5, pady=5)

        """
        文字水印选项内容
        """
        self.text_watermark_frame = tk.LabelFrame(master, text="文字水印选项", pady=5, foreground='green')
        self.text_watermark_frame.grid(row=4, column=0, columnspan=4, padx=5, pady=5, sticky="ew")
        Label(self.text_watermark_frame, text="水印文字:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        PlaceholderEntry(self.text_watermark_frame, textvariable=self.insert_watermark_var, width=48,
                         placeholder="默认使用文件夹名称").grid(row=0, column=1, padx=5, pady=5)
        # 字体颜色（HEX）和字体大小
        Label(self.text_watermark_frame, text="文字颜色:").grid(row=0, column=2, sticky="e", padx=5, pady=5)
        Entry(self.text_watermark_frame, textvariable=self.text_color_hex_var,
              width=10).grid(row=0, column=3, sticky="w", padx=5, pady=5)
        Label(self.text_watermark_frame, text="水印字体:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        OptionMenu(self.text_watermark_frame, tk.StringVar(value="宋体"), *self.font_map.keys(),
                   command=self.set_font_type).grid(row=1, column=1, sticky="w", padx=5, pady=5)
        Label(self.text_watermark_frame, text="字体大小:").grid(row=1, column=2, sticky="e", padx=5, pady=5)
        Entry(self.text_watermark_frame, textvariable=self.font_size_var, width=10).grid(row=1, column=3, sticky="w",
                                                                                         padx=5, pady=5)
        Label(self.text_watermark_frame, text="若获取到拍摄时间，则自动添加；否则不添加。",
              foreground="green").grid(
            row=2, column=0, columnspan=3, sticky="w", padx=5, pady=5)
        """
        图像水印选项内容
        """
        self.image_watermark_frame = tk.LabelFrame(master, text="图像水印选项", pady=5, foreground='green')
        self.image_watermark_frame.grid(row=4, column=0, columnspan=4, padx=5, pady=5, sticky="ew")
        Label(self.image_watermark_frame, text="水印图片路径:", foreground="red").grid(row=0, column=0, padx=5, pady=5)
        self.image_entry = Entry(self.image_watermark_frame, width=50)
        self.image_entry.grid(row=0, column=1, padx=5, pady=5)
        Button(self.image_watermark_frame, command=self.browse_image_path,
               text="浏览").grid(row=0, column=2, padx=5, pady=5)
        Label(self.image_watermark_frame, text="水印宽度:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        Entry(self.image_watermark_frame, textvariable=self.img_water_width,
              width=10).grid(row=1, column=1, sticky="w", padx=5, pady=5)
        Label(self.image_watermark_frame, text="水印高度:").grid(row=1, column=1, sticky="e", padx=5, pady=5)
        Entry(self.image_watermark_frame, textvariable=self.img_water_height,
              width=10).grid(row=1, column=2, sticky="w", padx=5, pady=5)
        Label(self.image_watermark_frame, text="默认设置下，图片水印使用原尺寸，视频水印则采用原尺寸的40%。",
              foreground="green").grid(
            row=2, column=0, columnspan=3, sticky="w", padx=5, pady=5)

        """
        添加水印公共部分
        """
        self.watermark_common = tk.LabelFrame(master)
        self.watermark_common.grid(row=5, column=0, columnspan=4, padx=5, pady=5, sticky="ew")

        Label(self.watermark_common, text="水印位置:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        OptionMenu(self.watermark_common, tk.StringVar(value="左下角"), *self.txt_position_map.keys(),
                   command=self.set_txt_position).grid(row=0, column=1, sticky="w", padx=5, pady=5)
        Label(self.watermark_common, text="", width=20).grid(row=0, column=2, sticky="w", padx=5, pady=5)
        # 水平边距和垂直边距
        Label(self.watermark_common, text="水平边距:").grid(row=0, column=3, sticky="w", padx=5, pady=5)
        Entry(self.watermark_common, textvariable=self.padding_var, width=10).grid(row=0, column=4, sticky="w", padx=5,
                                                                                   pady=5)
        # 日期格式和水印位置
        Label(self.watermark_common, text="日期格式:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        OptionMenu(self.watermark_common, tk.StringVar(value="Y年M月D日"), *self.date_format_map.keys(),
                   command=self.set_date_format).grid(row=1, column=1, sticky="w", padx=5, pady=5)
        Label(self.watermark_common, text="垂直边距:").grid(row=1, column=3, sticky="w", padx=5, pady=5)
        Entry(self.watermark_common, textvariable=self.h_padding_var, width=10).grid(row=1, column=4, sticky="w",
                                                                                     padx=5, pady=5)

        """
        压缩优化
        """
        self.compress_frame = tk.LabelFrame(master, text="压缩优化选项", foreground='green', pady=5)
        self.compress_frame.grid(row=6, column=0, columnspan=4, padx=5, pady=5, sticky="ew")
        Label(self.compress_frame, text="压缩质量:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.spinbox = Spinbox(self.compress_frame, from_=0, to=100, width=5, increment=10,
                               textvariable=self.spinbox_quality)
        self.spinbox.grid(row=0, column=1, sticky="w", padx=5, pady=5)
        Label(self.compress_frame, text="%(原质量)").grid(row=0, column=1, sticky="w", padx=(60, 5), pady=5)
        # 输出格式
        Label(self.compress_frame, text="输出格式:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        Label(self.compress_frame, text="图片").grid(row=1, column=1, sticky="w", pady=5, padx=5)
        self.photo_format_menu = OptionMenu(self.compress_frame, tk.StringVar(value="原始格式"),
                                            *self.photo_format_map.keys(), command=self.set_photo_format)
        self.photo_format_menu.grid(row=1, column=1, sticky="e", pady=5, padx=(34, 0))
        self.photo_format_menu.config(width=6)
        Label(self.compress_frame, text="视频").grid(row=1, column=2, sticky="w", padx=(25, 5), pady=5)
        self.video_format_menu = OptionMenu(self.compress_frame, tk.StringVar(value="原始格式"),
                                            *self.video_format_map.keys(), command=self.set_video_format)
        self.video_format_menu.grid(row=1, column=2, sticky="w", pady=5, padx=(56, 0), columnspan=2)
        self.video_format_menu.config(width=6)
        # 尺寸处理
        Label(self.compress_frame, text="图片处理:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        Radiobutton(self.compress_frame, text="原尺寸", variable=self.size_process, value="original_size",
                    ).grid(row=2, column=1, sticky="w", padx=5, pady=5)
        Radiobutton(self.compress_frame, text="百分比缩放", variable=self.size_process, value="scale_size",
                    ).grid(row=3, column=1, sticky="w", padx=5, pady=5, )
        self.spinbox2 = Spinbox(self.compress_frame, from_=0, to=100, width=5, increment=10,
                                textvariable=self.spinbox_scale)
        self.spinbox2.grid(row=3, column=6, sticky="w", padx=5, pady=5)
        Radiobutton(self.compress_frame, text=" 非等比例缩放", variable=self.size_process, value="specify_size"
                    ).grid(row=4, column=1, sticky="w", padx=5, pady=5, )
        Label(self.compress_frame, text="宽").grid(row=4, column=2, sticky="e", padx=5, pady=5)
        Entry(self.compress_frame, textvariable=self.size_width, width=8).grid(row=4, column=3, sticky="w", pady=5)
        Label(self.compress_frame, text="高").grid(row=4, column=4, sticky="e", padx=5, pady=5)
        Entry(self.compress_frame, textvariable=self.size_height, width=8).grid(row=4, column=5, sticky="w",
                                                                                pady=5)
        Radiobutton(self.compress_frame, text=" 尺寸裁剪", variable=self.size_process, value="crop_size"
                    ).grid(row=5, column=1, sticky="w", padx=5, pady=5, )
        Label(self.compress_frame, text="参考点").grid(row=5, column=2, sticky="e", padx=(15, 5), pady=5)
        self.crop_center_menu = OptionMenu(self.compress_frame, tk.StringVar(value="居中"),
                                           *self.crop_center_map.keys(), command=self.set_crop_center)
        self.crop_center_menu.grid(row=5, column=3, sticky="e", pady=5)
        self.crop_center_menu.config(width=4)
        Label(self.compress_frame, text="宽").grid(row=5, column=4, sticky="e", padx=(20, 5), pady=5)
        Entry(self.compress_frame, textvariable=self.crop_width, width=8).grid(row=5, column=5, sticky="w", pady=5)
        Label(self.compress_frame, text="高").grid(row=5, column=6, sticky="w", pady=5, padx=(10, 0))
        Entry(self.compress_frame, textvariable=self.crop_height, width=8).grid(row=5, column=6, sticky="w", padx=30,
                                                                                pady=5)

        """
        处理
        """
        Label(master, text="设置输出文件名称:").grid(row=7, column=0, sticky="e", padx=5, pady=5)
        PlaceholderEntry(master, textvariable=self.out_file_name_var, width=50,
                         placeholder="默认使用原文件名",
                         placeholder_color='grey').grid(row=7, column=1, padx=5, pady=5)
        Checkbutton(master, variable=self.is_add_video_water_var,
                    text="同时处理视频").grid(row=7, column=2, columnspan=2, sticky="w", padx=5, pady=5)

        self.start_button = Button(master, text="开始处理", command=self.start_processing_thread)
        self.start_button.grid(row=9, column=0, columnspan=4, pady=10)
        Button(master, text="清除日志", command=self.clear_log).grid(row=9, column=2, columnspan=2)

        # 添加日志文本框
        self.log_text = tk.Text(master, wrap='word', height=14, width=80)
        self.log_text.grid(row=10, column=0, columnspan=4, padx=10, pady=10)
        log_font = Font(family="simsun.ttc", size=10)
        self.log_text.config(font=log_font, state=tk.DISABLED)  # 禁止用户编辑

        self.log_text.tag_configure("green", foreground="green")
        self.log_text.tag_configure("black", foreground="black")
        self.log_text.tag_configure("red", foreground="red")

        # 添加滚动条
        scroll = Scrollbar(master, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scroll.set)
        scroll.grid(row=10, column=4, sticky='ns')

        # Initially hide the image watermark options
        self.image_watermark_frame.grid_remove()

        # Update widgets based on initial watermark type
        self.update_widgets()

    def clear_log(self):
        self.log_text.config(state=tk.NORMAL)  # 更改状态为可编辑
        self.log_text.delete(1.0, tk.END)  # 清除内容
        self.log_text.config(state=tk.DISABLED)  # 恢复不可编辑状态

    def log(self, message, color='gray'):
        """向日志文本框中添加消息"""
        self.log_text.config(state=NORMAL)
        self.log_text.insert(END, message + '\n', color)
        self.log_text.see(END)  # 自动滚动到底部
        self.log_text.config(state=DISABLED)

    def set_font_type(self, value):
        self.font_type = self.font_map[value]

    def set_date_format(self, value):
        self.out_date_format = self.date_format_map[value]

    def set_photo_format(self, value):
        self.out_photo_format = self.photo_format_map[value]

    def set_video_format(self, value):
        self.out_video_format = self.video_format_map[value]

    def set_crop_center(self, value):
        self.crop_center = self.crop_center_map[value]

    def set_txt_position(self, value):
        self.txt_position = self.txt_position_map[value]

    def browse_root_dir(self):
        root_dir = filedialog.askdirectory()
        self.root_dir_var.set(root_dir)

    def browse_out_path(self):
        out_path = filedialog.askdirectory()
        self.out_path_var.set(out_path)

    def start_processing_thread(self):
        self.start_button.config(state=DISABLED)
        threading.Thread(target=self.start_processing, daemon=True).start()

    def browse_image_path(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;")])
        if file_path:
            self.image_entry.delete(0, tk.END)
            self.image_entry.insert(0, file_path)

    def update_widgets(self):
        if self.watermark_type.get() == "text":
            self.image_watermark_frame.grid_remove()
            self.compress_frame.grid_remove()
            self.text_watermark_frame.grid()
            self.watermark_common.grid()
        elif self.watermark_type.get() == "image":
            self.text_watermark_frame.grid_remove()
            self.compress_frame.grid_remove()
            self.image_watermark_frame.grid()
            self.watermark_common.grid()
        elif self.watermark_type.get() == "compress":
            self.text_watermark_frame.grid_remove()
            self.image_watermark_frame.grid_remove()
            self.watermark_common.grid_remove()
            self.compress_frame.grid()

    def start_processing(self):
        try:
            root_dir = self.root_dir_var.get()
            out_path = self.out_path_var.get()
            is_add_video_water = bool(self.is_add_video_water_var.get())
            font_size = self.font_size_var.get()
            padding = self.padding_var.get()
            h_padding = self.h_padding_var.get()
            if not root_dir or not out_path:
                self.log("\n错误: 请选择根目录和输出目录\n", "red")
                self.master.after(0, lambda: self.start_button.config(state=NORMAL))
                return
            if root_dir == out_path:
                self.log("\n导出与导入目录不能一致\n", "red")
                self.master.after(0, lambda: self.start_button.config(state=NORMAL))
                return
            font_path = rf'C:/Windows/Fonts/{self.font_type}'
            watermark_type = self.watermark_type.get()
            if watermark_type == "image":
                if not is_valid_watermark_image(self.image_entry.get()):
                    self.log("\n水印图片路径为空或者图片有误。\n", "red")
                    self.master.after(0, lambda: self.start_button.config(state=NORMAL))
                    return
            elif watermark_type == "text":
                if not is_color(self.text_color_hex_var.get()):
                    self.log("\n错误: 字体颜色不合法\n", "red")
                    self.master.after(0, lambda: self.start_button.config(state=NORMAL))
                    return
                if not os.path.exists(font_path):
                    self.log("\n提示: 系统没有安装该字体\n", "red")
                    self.master.after(0, lambda: self.start_button.config(state=NORMAL))
                    return False
            out_file_name = self.out_file_name_var.get()
            if self.out_file_name_var.get() == '默认使用原文件名':
                out_file_name = None
            self.log("==================================", "green")
            self.log("      处理已经开始，请稍候...", "green")
            self.log("==================================", "green")
            if watermark_type == "text" or watermark_type == "image":
                text_color = convert_color_to_numeric(self.text_color_hex_var.get())
                if self.txt_position is None:
                    self.txt_position = 0
                insert_watermark = self.insert_watermark_var.get()
                if insert_watermark == '默认使用文件夹名称':
                    insert_watermark = None
                process_directory(root_dir, out_path, out_file_name, is_add_video_water, self.out_date_format,
                                  font_size, self.txt_position, padding, h_padding, self.log, text_color,
                                  insert_watermark, self.font_type, watermark_type, self.image_entry.get(),
                                  self.img_water_width.get(), self.img_water_height.get())
            elif watermark_type == "compress":
                compress_process_directory(root_dir, out_path, out_file_name, is_add_video_water, self.log,
                                           self.spinbox_quality.get(), self.out_photo_format, self.out_video_format,
                                           self.size_process.get(),
                                           self.spinbox_scale.get(), self.size_width.get(), self.size_height.get(),
                                           self.crop_center, self.crop_width.get(), self.crop_height.get())
            self.log("==================================", "green")
            self.log("              处理完成", "green")
            self.log("==================================\n", "green")
            self.master.after(0, lambda: self.start_button.config(state=NORMAL))
        except Exception as e:
            self.log(f"详细错误信息：{str(e)}", "red")
            self.master.after(0, lambda: self.start_button.config(state=NORMAL))
            pass


if __name__ == "__main__":
    root = tk.Tk()
    root.iconbitmap(resource_path("logo.ico"))
    app = App(root)
    root.mainloop()
