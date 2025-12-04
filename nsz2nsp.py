#!/usr/bin/env python3
import os
import sys
import subprocess
try:
    from tkinter import Tk, filedialog
except Exception:
    Tk = None
    filedialog = None

def convert_nsz_to_nsp(directory, show_progress=False):
    """
    将指定目录下的所有 .nsz 文件转换为 .nsp 文件。

    :param directory: 存放 .nsz 文件的目录路径
    """
    import importlib.util, shutil, sysconfig

    def resolve_nsz_bin():
        # 1) 优先使用 PATH 中的 nsz，但需排除坏解释器（例如断链到不存在的 Homebrew Python）
        path_bin = shutil.which("nsz")
        def bad_interpreter(script_path):
            try:
                if not script_path or not os.path.exists(script_path):
                    return True
                with open(script_path, "rb") as f:
                    first = f.readline().decode("utf-8", errors="ignore").strip()
                if first.startswith("#!"):
                    interp = first[2:].split()[0]
                    return not os.path.exists(interp)
                return False
            except Exception:
                return False

        if path_bin and not bad_interpreter(path_bin):
            return path_bin

        # 2) 查找当前解释器的 scripts 目录中的 nsz（pip 安装的位置）
        scripts_dir = sysconfig.get_path("scripts")
        if scripts_dir:
            candidate = os.path.join(scripts_dir, "nsz")
            if os.path.exists(candidate) and os.access(candidate, os.X_OK) and not bad_interpreter(candidate):
                return candidate

        return None

    nsz_bin = resolve_nsz_bin()
    # 如果既没有可用的 nsz 命令，也找不到 nsz 包，提示安装
    if nsz_bin is None and importlib.util.find_spec("nsz") is None:
        print("未检测到可用的 nsz。请执行：python3 -m pip install nsz")
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

    # 统一存放源 .nsz 的目录（位于当前工作目录）
    stash_root = os.path.join(os.getcwd(), "nsz_sources")
    os.makedirs(stash_root, exist_ok=True)

    def move_to_stash(src_path):
        # 保留相对结构，并处理重名冲突
        rel = os.path.relpath(src_path, directory)
        dest = os.path.join(stash_root, rel)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        final_dest = dest
        if os.path.exists(dest):
            base, ext = os.path.splitext(dest)
            idx = 1
            final_dest = f"{base}.dup{idx}{ext}"
            while os.path.exists(final_dest):
                idx += 1
                final_dest = f"{base}.dup{idx}{ext}"
        import shutil as _sh2
        _sh2.move(src_path, final_dest)
        return final_dest

    # 遍历目录下的所有文件
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".nsz"):
                nsz_file = os.path.join(root, file)
                nsp_file = os.path.splitext(nsz_file)[0] + ".nsp"

                # 检查是否已经存在对应的 .nsp 文件
                if os.path.exists(nsp_file):
                    dest = move_to_stash(nsz_file)
                    print(f"已存在对应的 .nsp 文件，源文件已移至：{dest}")
                    continue

                try:
                    import shutil as _sh
                    import time, threading
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
                    cmd = [nsz_bin, "-D", nsz_file] if nsz_bin else None
                    # 由于 nsz 包不保证支持 `python -m nsz`，我们仅在检测到可靠的控制台脚本时执行
                    if not cmd:
                        print("未找到可用的 nsz 控制台脚本。请将 Python 的 scripts 目录添加到 PATH 或重新安装 nsz。")
                        raise subprocess.CalledProcessError(127, "nsz")

                    # 启动前记录时间并实时打印用时
                    start_time = time.time()
                    stop_event = threading.Event()
                    def _tick():
                        while not stop_event.is_set():
                            elapsed = int(time.time() - start_time)
                            try:
                                # 动态单行计时写入 stderr，使用回车覆盖行，避免刷屏
                                sys.stderr.write(f"用时: {elapsed} 秒\r")
                                sys.stderr.flush()
                            except Exception:
                                pass
                            time.sleep(1)
                    t = threading.Thread(target=_tick, daemon=True)
                    t.start()

                    try:
                        if show_progress:
                            # 继承终端输出，nsz 将显示原生进度条
                            p = subprocess.Popen(cmd, env=env)
                        else:
                            # 捕获输出，仅打印关键的 Decompress 行
                            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env, text=True, bufsize=1)
                    except (FileNotFoundError, OSError):
                        # 外部 nsz 命令无法启动（坏解释器或断链）
                        print("检测到无效的 nsz 命令，请修复 PATH 或重新安装 nsz。")
                        raise subprocess.CalledProcessError(127, cmd)
                    if not show_progress:
                        for line in p.stdout:
                            s = line.strip()
                            if s.startswith("Decompress"):
                                print(s)
                    rc = p.wait()
                    # 停止计时并输出完成用时
                    stop_event.set()
                    try:
                        # 打印换行，结束动态覆盖行
                        sys.stderr.write("\n")
                        sys.stderr.flush()
                    except Exception:
                        pass
                    duration = time.time() - start_time
                    print(f"转换完成: {os.path.basename(nsz_file)} 用时: {duration:.1f} 秒")
                    if rc != 0:
                        raise subprocess.CalledProcessError(rc, cmd)
                    dest = move_to_stash(nsz_file)
                    print(f"源文件已移至：{dest}")
                except subprocess.CalledProcessError:
                    pass

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="将指定目录下的所有 .nsz 文件转换为 .nsp 文件")
    parser.add_argument("directory", nargs="?", help="存放 .nsz 文件的目录路径")
    parser.add_argument("--progress", action="store_true", help="显示 nsz 原生进度条（继承终端输出）")
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
        convert_nsz_to_nsp(target_directory, show_progress=args.progress)
    else:
        print("请提供有效目录路径，例如：python nsz2nsp.py /path/to/dir")
