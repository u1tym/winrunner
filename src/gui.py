"""GUI インターフェースを提供するモジュール"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from typing import Dict, List, Optional
from .config_manager import ConfigManager, ProgramConfig
from .process_manager import ProcessManager


class WinRunnerGUI:
    """WinRunner のメインGUIクラス"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("WinRunner - Program Manager")
        self.root.geometry("800x600")

        # 設定とプロセス管理の初期化
        self.config_manager = ConfigManager()
        self.process_manager: Optional[ProcessManager] = None

        # GUI要素
        self.program_frames: Dict[str, ttk.Frame] = {}
        self.status_labels: Dict[str, ttk.Label] = {}
        self.start_buttons: Dict[str, ttk.Button] = {}
        self.stop_buttons: Dict[str, ttk.Button] = {}

        # 監視スレッド
        self.monitor_thread: Optional[threading.Thread] = None
        self.monitoring = False

        self._setup_gui()
        self._load_config()

    def _setup_gui(self) -> None:
        """GUIの初期設定を行う"""
        # メインフレーム
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # タイトル
        title_label = ttk.Label(main_frame, text="WinRunner - Program Manager",
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        # 設定ボタン
        settings_frame = ttk.Frame(main_frame)
        settings_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))

        ttk.Button(settings_frame, text="設定を再読み込み",
                  command=self._reload_config).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(settings_frame, text="全停止",
                  command=self._stop_all_programs).pack(side=tk.LEFT)

        # プログラム一覧のフレーム
        self.programs_frame = ttk.Frame(main_frame)
        self.programs_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))

        # スクロールバー付きのキャンバス
        self.canvas = tk.Canvas(self.programs_frame, bg="white")
        self.scrollbar = ttk.Scrollbar(self.programs_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # ステータスバー
        self.status_var = tk.StringVar()
        self.status_var.set("準備完了")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var,
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))

        # グリッドの重み設定
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)

    def _load_config(self) -> None:
        """設定ファイルを読み込む"""
        if not self.config_manager.load_config():
            messagebox.showerror("エラー", "設定ファイルの読み込みに失敗しました。\nデフォルト設定ファイルが作成されました。")
            return

        settings = self.config_manager.settings
        if settings is None:
            messagebox.showerror("エラー", "設定の読み込みに失敗しました。")
            return

        # プロセス管理の初期化
        self.process_manager = ProcessManager(settings.log_directory)

        # プログラム一覧の作成
        self._create_program_list()

        # 監視の開始
        self._start_monitoring(settings.monitor_interval_seconds)

        self.status_var.set(f"設定を読み込みました - {len(self.config_manager.programs)}個のプログラム")

    def _create_program_list(self) -> None:
        """プログラム一覧のGUIを作成"""
        # 既存の要素をクリア
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        self.program_frames.clear()
        self.status_labels.clear()
        self.start_buttons.clear()
        self.stop_buttons.clear()

        # ヘッダー
        header_frame = ttk.Frame(self.scrollable_frame)
        header_frame.grid(row=0, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 10))

        ttk.Label(header_frame, text="プログラム名", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=(0, 20))
        ttk.Label(header_frame, text="状態", font=("Arial", 10, "bold")).grid(row=0, column=1, padx=(0, 20))
        ttk.Label(header_frame, text="操作", font=("Arial", 10, "bold")).grid(row=0, column=2, padx=(0, 20))

        # 各プログラムの行を作成
        for i, program in enumerate(self.config_manager.programs):
            self.process_manager.add_program(program)
            self._create_program_row(program, i + 1)

    def _create_program_row(self, program: ProgramConfig, row: int) -> None:
        """個別のプログラム行を作成"""
        frame = ttk.Frame(self.scrollable_frame, relief=tk.RAISED, borderwidth=1)
        frame.grid(row=row, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=2, padx=5)
        frame.columnconfigure(1, weight=1)

        # プログラム名
        name_label = ttk.Label(frame, text=program.name, font=("Arial", 9))
        name_label.grid(row=0, column=0, padx=(10, 20), pady=5, sticky=tk.W)

        # 状態表示
        status_label = ttk.Label(frame, text="停止中", foreground="red")
        status_label.grid(row=0, column=1, padx=(0, 20), pady=5, sticky=tk.W)

        # ボタンフレーム
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=0, column=2, padx=(0, 10), pady=5)

        # 起動ボタン
        start_btn = ttk.Button(button_frame, text="起動",
                              command=lambda p=program: self._start_program(p))
        start_btn.grid(row=0, column=0, padx=(0, 5))

        # 停止ボタン
        stop_btn = ttk.Button(button_frame, text="停止",
                             command=lambda p=program.name: self._stop_program(p),
                             state=tk.DISABLED)
        stop_btn.grid(row=0, column=1)

        # 詳細情報
        detail_text = f"実行ファイル: {program.executable}\n作業ディレクトリ: {program.working_directory}"
        if program.arguments:
            detail_text += f"\n引数: {' '.join(program.arguments)}"

        detail_label = ttk.Label(frame, text=detail_text, font=("Arial", 8),
                                foreground="gray")
        detail_label.grid(row=1, column=0, columnspan=3, padx=10, pady=(0, 5), sticky=tk.W)

        # 辞書に保存
        self.program_frames[program.name] = frame
        self.status_labels[program.name] = status_label
        self.start_buttons[program.name] = start_btn
        self.stop_buttons[program.name] = stop_btn

    def _start_program(self, program: ProgramConfig) -> None:
        """プログラムを起動"""
        if self.process_manager is None:
            return

        def start_thread():
            success = self.process_manager.start_program(program)
            if success:
                self.root.after(0, lambda: self._update_program_status(program.name))
            else:
                self.root.after(0, lambda: messagebox.showerror("エラー",
                    f"プログラム '{program.name}' の起動に失敗しました。"))

        threading.Thread(target=start_thread, daemon=True).start()

    def _stop_program(self, program_name: str) -> None:
        """プログラムを停止"""
        if self.process_manager is None:
            return

        def stop_thread():
            success = self.process_manager.stop_program(program_name)
            if success:
                self.root.after(0, lambda: self._update_program_status(program_name))
            else:
                self.root.after(0, lambda: messagebox.showerror("エラー",
                    f"プログラム '{program_name}' の停止に失敗しました。"))

        threading.Thread(target=stop_thread, daemon=True).start()

    def _stop_all_programs(self) -> None:
        """全プログラムを停止"""
        if self.process_manager is None:
            return

        if messagebox.askyesno("確認", "全てのプログラムを停止しますか？"):
            for program_name in self.process_manager.processes:
                self.process_manager.stop_program(program_name)
            self._update_all_status()

    def _update_program_status(self, program_name: str) -> None:
        """個別プログラムの状態を更新"""
        if self.process_manager is None or program_name not in self.status_labels:
            return

        is_running = self.process_manager.is_running(program_name)
        status_label = self.status_labels[program_name]
        start_btn = self.start_buttons[program_name]
        stop_btn = self.stop_buttons[program_name]

        if is_running:
            status_label.config(text="実行中", foreground="green")
            start_btn.config(state=tk.DISABLED)
            stop_btn.config(state=tk.NORMAL)
        else:
            status_label.config(text="停止中", foreground="red")
            start_btn.config(state=tk.NORMAL)
            stop_btn.config(state=tk.DISABLED)

    def _update_all_status(self) -> None:
        """全プログラムの状態を更新"""
        if self.process_manager is None:
            return

        for program_name in self.status_labels:
            self._update_program_status(program_name)

    def _start_monitoring(self, interval_seconds: int) -> None:
        """監視スレッドを開始"""
        if self.monitoring:
            return

        self.monitoring = True

        def monitor():
            while self.monitoring:
                if self.process_manager:
                    self.process_manager.update_status()
                    self.root.after(0, self._update_all_status)
                time.sleep(interval_seconds)

        self.monitor_thread = threading.Thread(target=monitor, daemon=True)
        self.monitor_thread.start()

    def _stop_monitoring(self) -> None:
        """監視スレッドを停止"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)

    def _reload_config(self) -> None:
        """設定を再読み込み"""
        self._stop_monitoring()
        self._load_config()

    def run(self) -> None:
        """GUIを開始"""
        try:
            self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
            self.root.mainloop()
        except KeyboardInterrupt:
            self._on_closing()

    def _on_closing(self) -> None:
        """アプリケーション終了時の処理"""
        if messagebox.askokcancel("終了", "WinRunnerを終了しますか？\n起動中のプログラムは停止されます。"):
            self._stop_monitoring()
            if self.process_manager:
                for program_name in self.process_manager.processes:
                    self.process_manager.stop_program(program_name)
            self.root.destroy()
