"""断语 prompt demo —— 已收口到 `python -m tyche reading`,此处仅薄封装。

安装后(pip install -e .)运行 `python scripts/reading.py <args>` 等价于 `python -m tyche reading <args>`。
"""

import sys

from tyche.__main__ import main

if __name__ == "__main__":
    main(["reading", *sys.argv[1:]])
