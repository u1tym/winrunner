"""WinRunner - Windows Program Runner のメインエントリーポイント"""

import sys
import os
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.gui import WinRunnerGUI


def main() -> None:
    """メイン関数"""
    try:
        app = WinRunnerGUI()
        app.run()
    except Exception as e:
        print(f"アプリケーションの起動に失敗しました: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
