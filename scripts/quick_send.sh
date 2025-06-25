#!/bin/bash

# 🚀 クイック送信 - Boss01からAgent各ペインへの直接送信

show_usage() {
    cat << EOF
🚀 クイック送信コマンド

使用方法:
  $0 [ペイン] [メッセージ]

ペイン指定:
  a01, a02, a03, a04  - Agent1-4 (Presentation, Application, Domain, Infrastructure)
  b01, b02, b03, b04  - Agent5-8 (DataBus, Cache, Persistence, Monitoring)  
  c01, c02, c03, c04  - 予備ペイン
  boss01, boss02, boss03, boss04 - Bossペイン

使用例:
  $0 a01 "Agent1 Presentationとして開発開始"
  $0 b02 "Agent6 Cacheとしてキャッシュ最適化"
  $0 a01 "hello"
EOF
}

# ペイン番号マッピング
get_pane_number() {
    case "$1" in
        "boss01") echo "0" ;;
        "a01") echo "1" ;;
        "b01") echo "2" ;;
        "c01") echo "3" ;;
        "boss02") echo "4" ;;
        "a02") echo "5" ;;
        "b02") echo "6" ;;
        "c02") echo "7" ;;
        "boss03") echo "8" ;;
        "a03") echo "9" ;;
        "b03") echo "10" ;;
        "c03") echo "11" ;;
        "boss04") echo "12" ;;
        "a04") echo "13" ;;
        "b04") echo "14" ;;
        "c04") echo "15" ;;
        *) echo "" ;;
    esac
}

# メイン処理
main() {
    if [[ $# -lt 2 ]]; then
        show_usage
        exit 1
    fi
    
    local target="$1"
    local message="$2"
    
    local pane_num
    pane_num=$(get_pane_number "$target")
    
    if [[ -z "$pane_num" ]]; then
        echo "❌ エラー: 不明なペイン '$target'"
        show_usage
        exit 1
    fi
    
    # tmuxセッション確認
    if ! tmux has-session -t "multagent" 2>/dev/null; then
        echo "❌ エラー: tmux セッション 'multagent' が見つかりません"
        exit 1
    fi
    
    # Claude Code対応メッセージ送信
    echo "📤 送信中: $target (ペイン$pane_num) ← '$message'"
    
    # Claude Codeのプロンプトをクリア
    tmux send-keys -t "multagent:0.$pane_num" C-c
    sleep 0.3
    
    # メッセージ送信
    tmux send-keys -t "multagent:0.$pane_num" "$message"
    sleep 0.1
    
    # エンター押下
    tmux send-keys -t "multagent:0.$pane_num" C-m
    
    echo "✅ 送信完了（Claude Code対応）"
}

main "$@"