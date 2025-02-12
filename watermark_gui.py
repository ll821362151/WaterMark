import os
import sys
import threading
from datetime import datetime
from tkinter.font import Font
from tkinter.ttk import Button, Entry, Label, Checkbutton, Scrollbar

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


def add_watermark_ffmpeg(src_path, dst_path, watermark_text, font_size=40, txt_position=0, padding=20, h_padding=40,
                         text_color_hex=None, font_type='simsun.ttc'):
    try:
        if not os.path.exists(src_path):
            return False
        font_path = rf'C:/Windows/Fonts/{font_type}'
        if not os.path.exists(font_path):
            return False
        if getattr(sys, 'frozen', False):
            ffmpeg_dir = resource_path('ffmpeg')
            ffmpeg_path = os.path.join(ffmpeg_dir, 'bin', 'ffmpeg.exe')
        else:
            ffmpeg_path = r"F:\ffmpeg-master-latest-win64-gpl-shared\bin\ffmpeg.exe"
        if not os.path.exists(ffmpeg_path):
            return False
        h_padding = int(h_padding * 0.7)
        x = f'{padding}'
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
        print(f"{command_str}")
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
        logging.error(f"详细错误信息：{str(e)}")
        return False


def process_directory(root_dir, out_path=None, out_file_name=None, is_add_video_water=False, out_date_format=0,
                      font_size=40, txt_position=0, padding=20, h_padding=40, log_func=None, text_color_hex=None,
                      insert_watermark=None, font_type='simsun.ttc'):
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
            if file_name.lower().endswith(('png', 'jpg', 'jpeg')):
                os.makedirs(save_dir, exist_ok=True)
                output_image_path = os.path.join(save_dir, new_file_name)
                if insert_watermark is None:
                    create_date = get_photo_capture_time(input_image_path, out_date_format)
                    if create_date:
                        mark_text = f"{create_date}\n{watermark_text}"
                success = add_text_watermark2(input_image_path, output_image_path, mark_text, font_size,
                                              txt_position, padding, h_padding, 0, text_color_hex, font_type)
            elif file_name.lower().endswith('mp4'):
                os.makedirs(save_dir, exist_ok=True)
                output_image_path = os.path.join(save_dir, new_file_name)
                if is_add_video_water:
                    if insert_watermark is None:
                        create_date = get_video_creation_date(input_image_path, out_date_format)
                        if create_date:
                            mark_text = f"{create_date}\n{watermark_text}"
                    success = add_watermark_ffmpeg(input_image_path, output_image_path, mark_text, font_size,
                                                   txt_position, padding, h_padding, text_color_hex, font_type)
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
        self.font_type = None
        self.master = master
        master.title("图片和视频加文字水印工具")

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

        # 日期格式和水印位置映射
        self.date_format_map = {
            "Y年M月D日": 0,
            "Y-M-D": 1,
            "Y/M/D": 2
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
        Label(master, text="选择目录(*):", foreground="red").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        Entry(master, textvariable=self.root_dir_var, width=50).grid(row=0, column=1, padx=5, pady=5)
        Button(master, text="浏览", command=self.browse_root_dir).grid(row=0, column=2, padx=5, pady=5)

        Label(master, text="输出目录(*):", foreground="red").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        Entry(master, textvariable=self.out_path_var, width=50).grid(row=1, column=1, padx=5, pady=5)
        Button(master, text="浏览", command=self.browse_out_path).grid(row=1, column=2, padx=5, pady=5)

        Label(master, text="文字水印:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        PlaceholderEntry(master, textvariable=self.insert_watermark_var, width=50,
                         placeholder="默认使用文件夹名称").grid(row=2, column=1, padx=5, pady=5)

        Label(master, text="输出文件名:").grid(row=3, column=0, sticky="e", padx=5, pady=5)
        PlaceholderEntry(master, textvariable=self.out_file_name_var, width=50, placeholder="默认使用原文件名",
                         placeholder_color='grey').grid(row=3, column=1, padx=5, pady=5)
        Checkbutton(master, variable=self.is_add_video_water_var,
                    text="视频添加水印").grid(row=4, column=2, sticky="w", padx=5, pady=5)

        # 日期格式和水印位置
        Label(master, text="水印字体:").grid(row=4, column=0, sticky="e", pady=5)
        OptionMenu(master, tk.StringVar(value="宋体"), *self.font_map.keys(),
                   command=self.set_font_type).grid(row=4, column=1, sticky="w", padx=5, pady=5)
        # 字体颜色（HEX）和字体大小
        Label(master, text="文字颜色:").grid(row=5, column=0, sticky="e", padx=5, pady=5)
        Entry(master, textvariable=self.text_color_hex_var, width=10).grid(row=5, column=1, sticky="w", padx=5, pady=5)

        Label(master, text="水印位置:").grid(row=5, column=1, sticky="e", padx=5, pady=5)
        OptionMenu(master, tk.StringVar(value="左下角"), *self.txt_position_map.keys(),
                   command=self.set_txt_position).grid(row=5, column=2, sticky="w", padx=5, pady=5)

        Label(master, text="字体大小:").grid(row=6, column=0, sticky="e", padx=5, pady=5)
        Entry(master, textvariable=self.font_size_var, width=10).grid(row=6, column=1, sticky="w", padx=5, pady=5)

        # 水平边距和垂直边距
        Label(master, text="水平边距:").grid(row=6, column=1, sticky="e", padx=5, pady=5)
        Entry(master, textvariable=self.padding_var, width=10).grid(row=6, column=2, sticky="w", padx=5, pady=5)
        # 日期格式和水印位置
        Label(master, text="日期格式:").grid(row=7, column=0, sticky="e", padx=5, pady=5)
        OptionMenu(master, tk.StringVar(value="Y年M月D日"), *self.date_format_map.keys(),
                   command=self.set_date_format).grid(row=7, column=1, sticky="w", padx=5, pady=5)
        Label(master, text="垂直边距:").grid(row=7, column=1, sticky="e", padx=5, pady=5)
        Entry(master, textvariable=self.h_padding_var, width=10).grid(row=7, column=2, sticky="w", padx=5, pady=5)

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
        # 定义清除日志文本框内容的函数

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
            if not is_color(self.text_color_hex_var.get()):
                self.log("\n错误: 字体颜色不合法\n", "red")
                self.master.after(0, lambda: self.start_button.config(state=NORMAL))
                return
            font_path = rf'C:/Windows/Fonts/{self.font_type}'
            if not os.path.exists(font_path):
                self.log("\n提示: 系统没有安装该字体\n", "red")
                self.master.after(0, lambda: self.start_button.config(state=NORMAL))
                return False
            self.log("==================================", "green")
            self.log("      处理已经开始，请稍候...", "green")
            self.log("==================================", "green")
            text_color = convert_color_to_numeric(self.text_color_hex_var.get())
            out_file_name = self.out_file_name_var.get()
            if self.out_file_name_var.get() == '默认使用原文件名':
                out_file_name = None
            insert_watermark = self.insert_watermark_var.get()
            if insert_watermark == '默认使用文件夹名称':
                insert_watermark = None
            print(self.font_type)
            process_directory(root_dir, out_path, out_file_name, is_add_video_water, self.out_date_format,
                              font_size, self.txt_position, padding, h_padding, self.log, text_color,
                              insert_watermark, self.font_type)
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
    app = App(root)
    root.mainloop()
