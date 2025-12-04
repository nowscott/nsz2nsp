#!/usr/bin/env python3
import os
import sys
import subprocess
try:
    from tkinter import Tk, filedialog
except Exception:
    Tk = None
    filedialog = None

def convert_nsz_to_nsp(directory):
    """
    将指定目录下的所有 .nsz 文件转换为 .nsp 文件。

    :param directory: 存放 .nsz 文件的目录路径
    """
    import importlib.util, shutil
    nsz_bin = shutil.which("nsz")
    if nsz_bin is None and importlib.util.find_spec("nsz") is None:
        print("请先安装 nsz 工具：pip install nsz")
        return

    def resolve_keyset(base_dir):
        env_path = os.environ.get("NSZ_KEYSET")
        candidates = []
        if env_path:
            candidates.append(os.path.expanduser(env_path))
        candidates.append(os.path.expanduser("~/.switch/prod.keys"))
        candidates.append(os.path.join(os.getcwd(), ".switch", "prod.keys"))
        candidates.append(os.path.join(base_dir, "keys.txt"))
        candidates.append(os.path.join(os.getcwd(), "keys.txt"))
        for p in candidates:
            if p and os.path.exists(p):
                return p
        return None

    keyset = resolve_keyset(directory)
    if not keyset:
        print("未找到密钥文件。请将 prod.keys 放在 ~/.switch/prod.keys，或将 keys.txt 放在目录，或设置环境变量 NSZ_KEYSET 指向密钥文件路径。")
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

                try:
                    import shutil as _sh
                    env = os.environ.copy()
                    home_override = None
                    if keyset.endswith("/.switch/prod.keys"):
                        home_override = os.path.dirname(os.path.dirname(keyset))
                    else:
                        target_home = os.getcwd()
                        target_switch = os.path.join(target_home, ".switch")
                        os.makedirs(target_switch, exist_ok=True)
                        dest = os.path.join(target_switch, "prod.keys")
                        if os.path.abspath(keyset) != os.path.abspath(dest):
                            _sh.copyfile(keyset, dest)
                        home_override = target_home
                    if home_override:
                        env["HOME"] = home_override
                    cmd = [nsz_bin, "-D", nsz_file] if nsz_bin else [sys.executable, "-m", "nsz", "-D", nsz_file]
                    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env, text=True, bufsize=1)
                    for line in p.stdout:
                        s = line.strip()
                        if s.startswith("Decompress"):
                            print(s)
                    rc = p.wait()
                    if rc != 0:
                        raise subprocess.CalledProcessError(rc, cmd)
                    os.remove(nsz_file)
                except subprocess.CalledProcessError:
                    pass

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="将指定目录下的所有 .nsz 文件转换为 .nsp 文件")
    parser.add_argument("directory", nargs="?", help="存放 .nsz 文件的目录路径")
    args = parser.parse_args()

    target_directory = args.directory
    if not target_directory:
        if Tk and filedialog:
            try:
                Tk().withdraw()
                target_directory = filedialog.askdirectory(title="请选择存放 .nsz 文件的目录")
            except Exception:
                target_directory = None

    if target_directory and os.path.isdir(target_directory):
        convert_nsz_to_nsp(target_directory)
    else:
        print("请提供有效目录路径，例如：python nsz2nsp.py /path/to/dir")
