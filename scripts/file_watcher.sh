#!/bin/bash

# 📂 ファイル監視システム - Claude Code ↔ tmux 間接的連携
# 
# 機能:
# - instructions/commands.txt の変更を監視
# - 新しい指示を自動検出・解析・実行
# - tmux ペインへのコマンド配信
# - Agent間メッセージング機能

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
WATCH_DIR="$PROJECT_ROOT/instructions"
COMMAND_FILE="$WATCH_DIR/commands.txt"
PROCESSED_FILE="$WATCH_DIR/processed.log"
LOG_FILE="$WATCH_DIR/watcher.log"

# ディレクトリとファイルの初期化
mkdir -p "$WATCH_DIR"
touch "$COMMAND_FILE"
touch "$LOG_FILE"

# ログ関数
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# tmux セッション確認
check_tmux_session() {
    if ! tmux has-session -t "multagent" 2>/dev/null; then
        log_message "❌ エラー: tmux セッション 'multagent' が見つかりません"
        log_message "📋 ヒント: ./create_multiagent_tmux.sh を実行してセッションを作成してください"
        return 1
    fi
    return 0
}

# ペイン番号マッピング (4x4グリッド)
get_pane_numbers() {
    local target="$1"
    case "$target" in
        "all")
            echo "0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15"
            ;;
        "boss")
            echo "0 4 8 12"  # boss01-04
            ;;
        "worker-a")
            echo "1 5 9 13"  # a01-04
            ;;
        "worker-b") 
            echo "2 6 10 14" # b01-04
            ;;
        "worker-c")
            echo "3 7 11 15" # c01-04
            ;;
        "boss01") echo "0" ;;
        "boss02") echo "4" ;;
        "boss03") echo "8" ;;
        "boss04") echo "12" ;;
        "a01") echo "1" ;;
        "a02") echo "5" ;;
        "a03") echo "9" ;;
        "a04") echo "13" ;;
        "b01") echo "2" ;;
        "b02") echo "6" ;;
        "b03") echo "10" ;;
        "b04") echo "14" ;;
        "c01") echo "3" ;;
        "c02") echo "7" ;;
        "c03") echo "11" ;;
        "c04") echo "15" ;;
        *)
            log_message "⚠️  警告: 不明なターゲット '$target'"
            echo ""
            ;;
    esac
}

# tmux ペインにコマンド送信
send_to_tmux() {
    local command="$1"
    local target="$2"
    
    if ! check_tmux_session; then
        return 1
    fi
    
    local pane_numbers
    pane_numbers=$(get_pane_numbers "$target")
    
    if [[ -z "$pane_numbers" ]]; then
        log_message "❌ エラー: 無効なターゲット '$target'"
        return 1
    fi
    
    for pane in $pane_numbers; do
        if tmux list-panes -t "multagent:0" | grep -q "^$pane:"; then
            tmux send-keys -t "multagent:0.$pane" "$command" C-m
            log_message "📤 送信完了: ペイン$pane ← '$command'"
        else
            log_message "⚠️  警告: ペイン$pane が存在しません"
        fi
    done
}

# Claude Codeに直接コマンド送信
send_claude_command() {
    local command="$1"
    local target="$2"
    
    if ! check_tmux_session; then
        return 1
    fi
    
    local pane_numbers
    pane_numbers=$(get_pane_numbers "$target")
    
    if [[ -z "$pane_numbers" ]]; then
        log_message "❌ エラー: 無効なターゲット '$target'"
        return 1
    fi
    
    for pane in $pane_numbers; do
        if tmux list-panes -t "multagent:0" | grep -q "^$pane:"; then
            # Claude Codeのプロンプトをクリアしてコマンドを入力
            tmux send-keys -t "multagent:0.$pane" C-c  # 現在の入力をキャンセル
            sleep 0.2
            tmux send-keys -t "multagent:0.$pane" "$command"  # コマンド入力
            sleep 0.1
            tmux send-keys -t "multagent:0.$pane" C-m  # エンター押下
            log_message "🤖 Claude実行: ペイン$pane ← '$command' (エンター送信)"
        else
            log_message "⚠️  警告: ペイン$pane が存在しません"
        fi
    done
}

# メッセージ表示
send_message() {
    local from="$1"
    local to="$2" 
    local message="$3"
    
    local display_command="echo '📨 [$from → $to]: $message'"
    send_to_tmux "$display_command" "$to"
    log_message "📨 メッセージ: $from → $to: $message"
}

# 指示解析・実行
process_commands() {
    if [[ ! -f "$COMMAND_FILE" ]]; then
        log_message "❌ エラー: $COMMAND_FILE が見つかりません"
        return 1
    fi
    
    local line_count=0
    local processed_count=0
    
    while IFS= read -r line; do
        ((line_count++))
        
        # 空行・コメント行をスキップ
        if [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]]; then
            log_message "🔍 スキップ: '$line'"
            continue
        fi
        
        ((processed_count++))
        log_message "🔄 処理中($processed_count): $line"
        
        # コマンド形式の解析
        log_message "🔍 解析対象: '$line'"
        if [[ "$line" =~ ^CLAUDE:([^:]+):(.+)$ ]]; then
            # CLAUDE:target:command 形式 (Claude Codeに直接コマンド送信)
            local target="${BASH_REMATCH[1]}"
            local cmd="${BASH_REMATCH[2]}"
            log_message "🤖 Claude指示: '$target' → '$cmd'"
            send_claude_command "$cmd" "$target"
            
        elif [[ "$line" =~ ^BROADCAST:([^:]+):(.+)$ ]]; then
            # BROADCAST:target:command 形式
            local target="${BASH_REMATCH[1]}"
            local cmd="${BASH_REMATCH[2]}"
            log_message "📢 ブロードキャスト: '$target' → '$cmd'"
            send_to_tmux "$cmd" "$target"
            
        elif [[ "$line" =~ ^MESSAGE:([^:]+):([^:]+):(.+)$ ]]; then
            # MESSAGE:from:to:message 形式
            local from="${BASH_REMATCH[1]}"
            local to="${BASH_REMATCH[2]}"
            local msg="${BASH_REMATCH[3]}"
            send_message "$from" "$to" "$msg"
            
        else
            # 通常コマンド（全ペインに送信）
            log_message "📤 全ペイン送信: '$line'"
            send_to_tmux "$line" "all"
        fi
        
    done < "$COMMAND_FILE"
    
    if [[ $processed_count -gt 0 ]]; then
        log_message "✅ 処理完了: $processed_count個の指示を実行しました"
    fi
}

# メイン監視ループ
main() {
    log_message "🚀 ファイル監視システム開始"
    log_message "📂 監視対象: $COMMAND_FILE"
    log_message "📋 使用方法: Claude Code で $COMMAND_FILE に指示を書き込んでください"
    
    # 初期セッション確認
    if ! check_tmux_session; then
        log_message "💡 tmux セッションを作成してから再実行してください"
        exit 1
    fi
    
    log_message "✅ tmux セッション 'multagent' を検出しました"
    
    while true; do
        # ファイル更新をチェック
        if [[ "$COMMAND_FILE" -nt "$PROCESSED_FILE" ]]; then
            log_message "🔔 新しい指示を検出しました"
            
            if process_commands; then
                # 処理済みマーク
                touch "$PROCESSED_FILE"
                log_message "✅ 指示処理完了 - 次の指示を待機中..."
            else
                log_message "❌ 指示処理中にエラーが発生しました"
            fi
        fi
        
        # 2秒間隔で監視
        sleep 2
    done
}

# スクリプト終了時のクリーンアップ
cleanup() {
    log_message "🛑 ファイル監視システム終了"
    exit 0
}

# シグナルハンドリング
trap cleanup SIGINT SIGTERM

# メイン実行
main "$@"