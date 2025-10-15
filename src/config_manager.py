"""設定ファイルの管理を行うモジュール"""

import json
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class ProgramConfig:
    """プログラム設定を表すデータクラス"""
    name: str
    working_directory: str
    executable: str
    arguments: List[str]


@dataclass
class AppSettings:
    """アプリケーション設定を表すデータクラス"""
    monitor_interval_seconds: int
    log_directory: str


class ConfigManager:
    """設定ファイルの読み込み・管理を行うクラス"""

    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self._settings: Optional[AppSettings] = None
        self._programs: List[ProgramConfig] = []

    def load_config(self) -> bool:
        """設定ファイルを読み込む

        Returns:
            bool: 読み込み成功時True、失敗時False
        """
        try:
            if not os.path.exists(self.config_path):
                self._create_default_config()
                return False

            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            # 設定の読み込み
            settings_data = config_data.get('settings', {})
            self._settings = AppSettings(
                monitor_interval_seconds=settings_data.get('monitor_interval_seconds', 2),
                log_directory=settings_data.get('log_directory', './logs')
            )

            # プログラム設定の読み込み
            self._programs = []
            for program_data in config_data.get('programs', []):
                program = ProgramConfig(
                    name=program_data.get('name', ''),
                    working_directory=program_data.get('working_directory', ''),
                    executable=program_data.get('executable', ''),
                    arguments=program_data.get('arguments', [])
                )
                self._programs.append(program)

            return True

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"設定ファイルの読み込みエラー: {e}")
            return False

    def _create_default_config(self) -> None:
        """デフォルト設定ファイルを作成する"""
        default_config = {
            "settings": {
                "monitor_interval_seconds": 2,
                "log_directory": "./logs"
            },
            "programs": [
                {
                    "name": "サンプルプログラム",
                    "working_directory": "C:\\path\\to\\program",
                    "executable": "program.exe",
                    "arguments": []
                }
            ]
        }

        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)

        print(f"デフォルト設定ファイルを作成しました: {self.config_path}")

    @property
    def settings(self) -> Optional[AppSettings]:
        """アプリケーション設定を取得"""
        return self._settings

    @property
    def programs(self) -> List[ProgramConfig]:
        """プログラム設定リストを取得"""
        return self._programs

    def get_program_by_name(self, name: str) -> Optional[ProgramConfig]:
        """名前でプログラム設定を検索"""
        for program in self._programs:
            if program.name == name:
                return program
        return None
