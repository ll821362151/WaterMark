--------------------------------------------------------------------------------------

1、开发环境
ffmpeg_path = r"F:\ffmpeg-master-latest-win64-gpl-shared\bin\ffmpeg.exe"
ffprobe_path = r"F:\ffmpeg-master-latest-win64-gpl-shared\bin\ffprobe.exe"
字体路径：r'C:/Windows/Fonts/simsun.ttc'

--------------------------------------------------------------------------------------

方法参数说明：
方法名：process_directory,参数解释如下：

    :param out_date_format: 输出时间格式；0=2025年1月1日；1=2025-01-01；2=2025/1/1
    :param h_padding:水印添加位置的垂直内边距
    :param root_dir: 源文件根路径
    :param out_path: 输出根路径
    :param out_file_name: 对输出文件进行重命名
    :param is_add_video_water: 是否对视频添加水印
    :param font_size: 水印字体大小，视频和图片文字大小不一致，稍微有区别
    :param txt_position: 水印添加的位置； 0=左下角，1右下角，2左上角，3右上角，其他默认左下角
    :param padding: 水印添加位置的水平内边距
    :return: 处理是否成功

get_video_creation_date 参数解释如下：

    """
    获取视频的拍摄时间
    :param video_path:视频的路径
    :param out_date_format: 输出时间格式；0=2025年1月1日；1=2025-01-01；2=2025/1/1
    :return: 时间
    """

--------------------------------------------------------------------------------------

使用示例如下：

    if __name__ == '__main__':
        root_directory = r"D:\2024巡检"
        out_directory = r"D:\2025巡检"
        file_name = r"2025春季巡检"
        process_directory(r"D:\A", None, file_name, True)

--------------------------------------------------------------------------------------
python脚本打包指令

    #将ffmpeg打包到可执行文件中
    pyinstaller --onefile --add-data "F:\ffmpeg-master-latest-win64-gpl-shared;ffmpeg" --noconsole watermark_gui.py

    #将icon和ffmpeg打包   
    pyinstaller --onefile -w --add-data "F:\ffmpeg-master-latest-win64-gpl-shared;ffmpeg" --noconsole -i logo.ico watermark_gui.py

--------------------------------------------------------------------------------------

我用夸克网盘分享了「批量加水印.exe」，点击链接即可保存。打开「夸克APP」，无需下载在线播放视频，畅享原画5倍速，支持电视投屏。
链接：https://pan.quark.cn/s/ff0c9198021a
