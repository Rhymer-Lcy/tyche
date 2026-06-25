"""排盘 demo —— 已收口到 `python -m tyche chart`,此处仅薄封装(保持旧用法可用)。

安装后(pip install -e .)运行 `python scripts/demo.py <args>` 等价于 `python -m tyche chart <args>`。
"""

import sys

from tyche.__main__ import main

if __name__ == "__main__":
    main(["chart", *sys.argv[1:]])
