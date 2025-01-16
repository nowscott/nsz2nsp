import os
import subprocess
from tkinter import Tk, filedialog

def convert_nsz_to_nsp(directory):
    """
    将指定目录下的所有 .nsz 文件转换为 .nsp 文件。

    :param directory: 存放 .nsz 文件的目录路径
    """
    # 确保 nsz 工具已经安装
    try:
        subprocess.run(["nsz", "--help"], check=True, stdout=subprocess.DEVNULL)
    except FileNotFoundError:
        print("请先安装 nsz 工具：pip install nsz")
        return

    # 遍历目录下的所有文件
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".nsz"):
                nsz_file = os.path.join(root, file)
                nsp_file = os.path.splitext(nsz_file)[0] + ".nsp"

                # 检查是否已经存在对应的 .nsp 文件
                if os.path.exists(nsp_file):
                    print(f"已存在对应的 .nsp 文件，删除原文件：{nsz_file}")
                    os.remove(nsz_file)
                    continue

                print(f"正在转换：{nsz_file}")
                try:
                    # 调用 nsz 工具解压缩
                    subprocess.run(["nsz", "-D", nsz_file], check=True)
                    print(f"转换成功：{nsz_file}")
                    # 删除原文件
                    os.remove(nsz_file)
                except subprocess.CalledProcessError as e:
                    print(f"转换失败：{nsz_file}，错误：{e}")

if __name__ == "__main__":
    # 创建一个文件选择对话框
    Tk().withdraw()  # 隐藏主窗口
    target_directory = filedialog.askdirectory(title="请选择存放 .nsz 文件的目录")
    
    if target_directory and os.path.isdir(target_directory):
        convert_nsz_to_nsp(target_directory)
    else:
        print("未选择有效目录，请检查后重试。")
