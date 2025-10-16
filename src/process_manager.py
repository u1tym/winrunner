"""プロセスの起動・停止・監視を行うモジュール"""

import subprocess
import psutil
import os
import time
import logging
from typing import Dict, Optional, List
from dataclasses import dataclass
from .config_manager import ProgramConfig


@dataclass
class ProcessInfo:
    """プロセス情報を表すデータクラス"""
    name: str
    process: Optional[subprocess.Popen] = None
    pid: Optional[int] = None
    is_running: bool = False
    start_time: Optional[float] = None


class ProcessManager:
    """プロセスの管理を行うクラス"""

    def __init__(self, log_directory: str = "./logs"):
        self.processes: Dict[str, ProcessInfo] = {}
        self.log_directory = log_directory
        self._setup_logging()

    def _setup_logging(self) -> None:
        """ログ設定を行う"""
        os.makedirs(self.log_directory, exist_ok=True)

        log_file = os.path.join(self.log_directory, "winrunner.log")

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def add_program(self, program_config: ProgramConfig) -> None:
        """プログラムを管理対象に追加"""
        self.processes[program_config.name] = ProcessInfo(name=program_config.name)
        self.logger.info(f"プログラム '{program_config.name}' を管理対象に追加しました")

    def start_program(self, program_config: ProgramConfig) -> bool:
        """プログラムを起動する

        Args:
            program_config: プログラム設定

        Returns:
            bool: 起動成功時True、失敗時False
        """
        try:
            # 既に起動している場合は何もしない
            if self.is_running(program_config.name):
                self.logger.warning(f"プログラム '{program_config.name}' は既に起動しています")
                return True

            # 作業ディレクトリの確認
            if not os.path.exists(program_config.working_directory):
                self.logger.error(f"作業ディレクトリが存在しません: {program_config.working_directory}")
                return False

            # 実行ファイルの確認
            executable_path = os.path.join(program_config.working_directory, program_config.executable)
            if not os.path.exists(executable_path):
                # パスが通っている場合の確認
                if not self._is_executable_in_path(program_config.executable):
                    self.logger.error(f"実行ファイルが見つかりません: {executable_path}")
                    return False

            # プロセス起動
            cmd = [program_config.executable] + program_config.arguments
            process = subprocess.Popen(
                cmd,
                cwd=program_config.working_directory,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )

            # プロセス情報を更新
            process_info = self.processes[program_config.name]
            process_info.process = process
            process_info.pid = process.pid
            process_info.is_running = True
            process_info.start_time = time.time()

            self.logger.info(f"プログラム '{program_config.name}' を起動しました (PID: {process.pid})")
            return True

        except Exception as e:
            self.logger.error(f"プログラム '{program_config.name}' の起動に失敗しました: {e}")
            return False

    def stop_program(self, program_name: str) -> bool:
        """プログラムを停止する

        Args:
            program_name: プログラム名

        Returns:
            bool: 停止成功時True、失敗時False
        """
        try:
            if program_name not in self.processes:
                self.logger.error(f"プログラム '{program_name}' が見つかりません")
                return False

            process_info = self.processes[program_name]

            if not process_info.is_running or process_info.process is None:
                self.logger.warning(f"プログラム '{program_name}' は起動していません")
                return True

            # 正常終了を試行
            try:
                process_info.process.terminate()
                process_info.process.wait(timeout=3)
                self.logger.info(f"プログラム '{program_name}' を正常終了しました")
            except subprocess.TimeoutExpired:
                # 強制終了
                process_info.process.kill()
                process_info.process.wait()
                self.logger.info(f"プログラム '{program_name}' を強制終了しました")

            # プロセス情報を更新
            process_info.process = None
            process_info.pid = None
            process_info.is_running = False
            process_info.start_time = None

            return True

        except Exception as e:
            self.logger.error(f"プログラム '{program_name}' の停止に失敗しました: {e}")
            return False

    def is_running(self, program_name: str) -> bool:
        """プログラムが起動しているかチェックする

        Args:
            program_name: プログラム名

        Returns:
            bool: 起動中の場合True
        """
        if program_name not in self.processes:
            return False

        process_info = self.processes[program_name]

        if process_info.process is None:
            return False

        # プロセスが実際に存在するかチェック
        try:
            # subprocess.Popenのpoll()でチェック
            poll_result = process_info.process.poll()
            if poll_result is not None:
                # プロセスが終了している
                self.logger.info(f"プログラム '{program_name}' が終了しました (終了コード: {poll_result})")
                process_info.is_running = False
                process_info.process = None
                process_info.pid = None
                return False

            # Windowsの場合、psutilでより詳細なチェック
            if os.name == 'nt' and process_info.pid:
                try:
                    psutil_process = psutil.Process(process_info.pid)
                    # プロセスが実際に存在し、実行中かチェック
                    if psutil_process.is_running():
                        return True
                    else:
                        # プロセスが存在するが実行中でない
                        self.logger.info(f"プログラム '{program_name}' のプロセスが実行中ではありません")
                        process_info.is_running = False
                        process_info.process = None
                        process_info.pid = None
                        return False
                except psutil.NoSuchProcess:
                    self.logger.info(f"プログラム '{program_name}' のプロセスが見つかりません")
                    process_info.is_running = False
                    process_info.process = None
                    process_info.pid = None
                    return False

            return True

        except Exception as e:
            self.logger.error(f"プロセス状態のチェックに失敗しました: {e}")
            return False

    def update_status(self) -> None:
        """全プログラムの状態を更新する"""
        for program_name in self.processes:
            self.is_running(program_name)

    def get_running_programs(self) -> List[str]:
        """起動中のプログラム名リストを取得"""
        running = []
        for program_name, process_info in self.processes.items():
            if self.is_running(program_name):
                running.append(program_name)
        return running

    def _is_executable_in_path(self, executable: str) -> bool:
        """実行ファイルがパスに存在するかチェック"""
        try:
            subprocess.run([executable, '--version'],
                         capture_output=True, timeout=1)
            return True
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
            return False
