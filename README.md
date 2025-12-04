# NSZ 转 NSP 工具

一个简单的 Python 工具，用于将 Nintendo Switch 的 NSZ 压缩文件批量转换为 NSP 格式。转换成功后会自动删除原始 NSZ。

## 更新内容

- 支持命令行传入目录参数，`tkinter` 仅在可用且未传参时回退
- 兼容 `nsz` 的密钥查找规则，自动准备并覆盖运行环境的 `HOME`，避免交互阻塞
- 仅展示解压进度条，过滤其他冗余输出
- 使用已安装的 `nsz` 控制台可执行或 `python -m nsz`，更稳健

## 系统要求

- Python 3.10 或更高版本（已在 3.14 验证）
- `nsz` 工具（`pip install nsz`）
- 有效的 Switch 密钥文件（`prod.keys`）

## 安装

- 安装 `nsz`：
```bash
python3 -m pip install --upgrade pip
python3 -m pip install nsz
```
- macOS 避免使用系统 `/usr/bin/python3`。若遇到“macOS 26 required”等报错，请安装官方 Python（例如 3.14），并使用其路径：
```bash
/Library/Frameworks/Python.framework/Versions/3.14/bin/python3.14 -V
```
可选：将上述 `bin` 目录加入 `PATH`。

## 密钥准备

`nsz` 会在以下位置查找密钥：
- `~/.switch/prod.keys`
- 当前工作目录的 `./.switch/prod.keys`
- 目标目录或当前目录的 `keys.txt`
- 或通过环境变量指定：`NSZ_KEYSET=/path/to/prod.keys`

建议：
```bash
mkdir -p ~/.switch
cp /path/to/prod.keys ~/.switch/prod.keys
```
密钥为敏感文件，请勿提交到仓库。

## 使用方法

- 命令行运行（推荐）：
```bash
python3 nsz2nsp.py '/绝对或相对路径/包含NSZ的目录'
```
路径包含空格或中括号时请使用引号包裹。

- GUI 回退（未传参且系统有 `tkinter`）：
```bash
python3 nsz2nsp.py
```
弹窗选择目录后开始转换。

## 输出

- 控制台仅展示 `Decompress ...` 进度条行，其余 `nsz` 输出被过滤
- 每个文件成功后删除对应 `.nsz`
- 若对应 `.nsp` 已存在，则跳过转换并删除 `.nsz`

## 示例

```bash
python3 nsz2nsp.py '/Users/你的用户名/Downloads/某个游戏目录'
```

## 注意事项

- 转换成功会删除原始 `.nsz`，请确保有备份
- 保证有足够磁盘空间
- 使用与安装 `nsz` 的同一解释器运行脚本，避免环境不一致

## 常见问题

- 提示“请先安装 nsz 工具”：
```bash
python3 -m pip install nsz
```
- 提示密钥缺失：将 `prod.keys` 放到 `~/.switch/prod.keys`，或设置 `NSZ_KEYSET`，或在工作目录的 `./.switch/prod.keys`，或在目标目录放置 `keys.txt`。

## 许可证

MIT License
