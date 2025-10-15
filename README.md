# WinRunner - Windows Program Runner

Windowsで複数のプログラムを管理・起動・停止するためのGUIツールです。

## 機能

- 複数のプログラムを設定ファイルで管理
- GUI による直感的な操作
- プログラムの起動・停止・状態監視
- 定期的なプロセス状態チェック
- ログ出力機能

## 必要な環境

- Python 3.7 以上
- Windows OS

## インストール

1. リポジトリをクローンまたはダウンロード
2. 依存関係をインストール:
   ```bash
   pip install -r requirements.txt
   ```

## 使用方法

1. `config.json` ファイルを編集して、管理したいプログラムを設定
2. アプリケーションを起動:
   ```bash
   python main.py
   ```

## 設定ファイル (config.json)

```json
{
  "settings": {
    "monitor_interval_seconds": 2,
    "log_directory": "./logs"
  },
  "programs": [
    {
      "name": "プログラム名",
      "working_directory": "C:\\path\\to\\program",
      "executable": "program.exe",
      "arguments": ["--arg1", "value1"]
    }
  ]
}
```

### 設定項目

- `monitor_interval_seconds`: プロセス状態チェックの間隔（秒）
- `log_directory`: ログファイルの出力先ディレクトリ
- `name`: プログラムの表示名
- `working_directory`: プログラムの作業ディレクトリ
- `executable`: 実行ファイル名（パスが通っている場合はファイル名のみ）
- `arguments`: プログラムに渡す引数の配列

## プロジェクト構造

```
winrunner/
├── main.py                 # メインエントリーポイント
├── config.json            # 設定ファイル
├── requirements.txt       # 依存関係
├── README.md             # このファイル
└── src/
    ├── __init__.py
    ├── config_manager.py  # 設定ファイル管理
    ├── process_manager.py # プロセス管理
    └── gui.py            # GUI インターフェース
```

## 機能詳細

### プログラム管理
- 設定ファイルで定義されたプログラムを一覧表示
- 各プログラムの起動・停止ボタン
- リアルタイムな状態表示（実行中/停止中）

### プロセス監視
- 設定可能な間隔でのプロセス状態チェック
- プロセスの異常終了の検出
- GUI への状態反映

### ログ機能
- プログラムの起動・停止ログ
- エラーログ
- 設定可能なログ出力先

## 注意事項

- 初回起動時に `config.json` が存在しない場合、サンプル設定ファイルが自動作成されます
- プログラムの強制終了は、まず正常終了を試行し、3秒後に強制終了します
- ログディレクトリが存在しない場合、自動作成されます

## ライセンス

このプロジェクトは MIT ライセンスの下で公開されています。
