#!/bin/bash

# 📡 tmux ブロードキャストユーティリティ
# file_watcher.sh の補助スクリプト - 直接実行も可能

SCRIPT_NAME="$(basename "$0")"
SESSION_NAME="multagent"

# 使用方法表示
show_usage() {
    cat << EOF
📡 tmux ブロードキャストユーティリティ

使用方法:
  $SCRIPT_NAME "コマンド" [ターゲット]

引数:
  コマンド    送信するコマンド (必須)
  ターゲット  送信先ペイン (省略時: all)

ターゲット一覧:
  all         全ペイン (0-15)
  boss        boss01-04 (0,4,8,12)
  worker-a    a01-04 (1,5,9,13) - Agent1-4
  worker-b    b01-04 (2,6,10,14) - Agent5-8  
  worker-c    c01-04 (3,7,11,15) - 予備
  boss01-04   個別bossペイン (0,4,8,12)
  a01-04      個別aペイン (1,5,9,13)
  b01-04      個別bペイン (2,6,10,14)
  c01-04      個別cペイン (3,7,11,15)

使用例:
  $SCRIPT_NAME "clear"                          # 全ペインクリア
  $SCRIPT_NAME "git status" "worker-a"          # Agent1-4でgit status
  $SCRIPT_NAME "python benchmark.py" "boss"     # Bossペインでベンチマーク
  $SCRIPT_NAME "echo 'テスト中'" "a01"          # a01ペインにメッセージ

Agent開発例:
  $SCRIPT_NAME "claude 'Agent1 Presentationとして...'" "a01"
  $SCRIPT_NAME "claude 'Agent6 Cacheとして...'" "b01"
EOF
}

# エラー出力
error_exit() {
    echo "❌ エラー: $1" >&2
    echo "💡 使用方法: $SCRIPT_NAME --help" >&2
    exit 1
}

# tmux セッション確認
check_tmux_session() {
    if ! tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
        error_exit "tmux セッション '$SESSION_NAME' が見つかりません。./create_multiagent_tmux.sh を実行してください"
    fi
}

# ペイン番号マッピング
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
            echo "1 5 9 13"  # a01-04 (Agent1-4)
            ;;
        "worker-b") 
            echo "2 6 10 14" # b01-04 (Agent5-8)
            ;;
        "worker-c")
            echo "3 7 11 15" # c01-04 (予備)
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
            error_exit "不明なターゲット '$target'"
            ;;
    esac
}

# ペイン存在確認
pane_exists() {
    local pane_num="$1"
    tmux list-panes -t "$SESSION_NAME:0" 2>/dev/null | grep -q "^$pane_num:"
}

# コマンド送信メイン関数
send_command() {
    local command="$1"
    local target="${2:-all}"
    
    echo "📡 ブロードキャスト開始"
    echo "📤 コマンド: '$command'"
    echo "🎯 ターゲット: $target"
    
    check_tmux_session
    
    local pane_numbers
    pane_numbers=$(get_pane_numbers "$target")
    
    local sent_count=0
    local error_count=0
    
    for pane in $pane_numbers; do
        if pane_exists "$pane"; then
            if tmux send-keys -t "$SESSION_NAME:0.$pane" "$command" C-m; then
                echo "✅ ペイン$pane: 送信成功"
                ((sent_count++))
            else
                echo "❌ ペイン$pane: 送信失敗"
                ((error_count++))
            fi
        else
            echo "⚠️  ペイン$pane: 存在しません"
            ((error_count++))
        fi
    done
    
    echo ""
    echo "📊 送信結果:"
    echo "   ✅ 成功: $sent_count個"
    echo "   ❌ 失敗: $error_count個"
    
    if [[ $error_count -gt 0 ]]; then
        echo "⚠️  一部のペインで送信に失敗しました"
        return 1
    else
        echo "🎉 全ペインへの送信が完了しました"
        return 0
    fi
}

# メイン処理
main() {
    # 引数チェック
    case "${1:-}" in
        "--help"|"-h"|"")
            show_usage
            exit 0
            ;;
        *)
            if [[ $# -eq 0 ]]; then
                error_exit "コマンドが指定されていません"
            fi
            ;;
    esac
    
    local command="$1"
    local target="${2:-all}"
    
    send_command "$command" "$target"
}

# スクリプト実行
main "$@"