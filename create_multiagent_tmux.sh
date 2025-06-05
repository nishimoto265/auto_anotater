#!/bin/bash

# tmuxで4x4のペイン構成を作成するスクリプト
# セッション名: multagent
# ペイン構成: boss01-04, a01-04, b01-04, c01-04

SESSION_NAME="multagent"

# 既存のセッションがある場合は削除
tmux has-session -t $SESSION_NAME 2>/dev/null && tmux kill-session -t $SESSION_NAME

# 新しいセッションを作成
tmux new-session -d -s $SESSION_NAME

# 最初のペインの名前を設定
tmux rename-window -t $SESSION_NAME:0 "multiagent"

# より確実な4x4グリッド作成方法

# まず横に3回分割して4列にする
tmux split-window -h -t $SESSION_NAME:0.0
tmux split-window -h -t $SESSION_NAME:0.0  
tmux split-window -h -t $SESSION_NAME:0.1

# 各列を縦に3回分割して4行にする
# 1列目を4分割
tmux split-window -v -t $SESSION_NAME:0.0
tmux split-window -v -t $SESSION_NAME:0.0
tmux split-window -v -t $SESSION_NAME:0.1

# 2列目を4分割  
tmux split-window -v -t $SESSION_NAME:0.4
tmux split-window -v -t $SESSION_NAME:0.4
tmux split-window -v -t $SESSION_NAME:0.5

# 3列目を4分割
tmux split-window -v -t $SESSION_NAME:0.8
tmux split-window -v -t $SESSION_NAME:0.8  
tmux split-window -v -t $SESSION_NAME:0.9

# 4列目を4分割
tmux split-window -v -t $SESSION_NAME:0.12
tmux split-window -v -t $SESSION_NAME:0.12
tmux split-window -v -t $SESSION_NAME:0.13

# 各ペインに移動してタイトルを設定
declare -a pane_names=(
    "boss01" "a01" "b01" "c01"
    "boss02" "a02" "b02" "c02"
    "boss03" "a03" "b03" "c03"
    "boss04" "a04" "b04" "c04"
)

# 各ペインにタイトルを設定し、対応するディレクトリに移動
for i in {0..15}; do
    pane_name=${pane_names[$i]}
    
    # ペインにタイトルを設定
    tmux send-keys -t $SESSION_NAME:0.$i "printf '\033]2;${pane_name}\033\\'" C-m
    
    # 対応するディレクトリに移動
    if [[ $pane_name == boss* ]]; then
        tmux send-keys -t $SESSION_NAME:0.$i "cd 01boss" C-m
    elif [[ $pane_name == a* ]]; then
        tmux send-keys -t $SESSION_NAME:0.$i "cd 01worker-a" C-m
    elif [[ $pane_name == b* ]]; then
        tmux send-keys -t $SESSION_NAME:0.$i "cd 01worker-b" C-m
    elif [[ $pane_name == c* ]]; then
        tmux send-keys -t $SESSION_NAME:0.$i "cd 01worker-c" C-m
    fi
    
    # プロンプトに名前を表示
    tmux send-keys -t $SESSION_NAME:0.$i "export PS1='(${pane_name}) \$ '" C-m
    tmux send-keys -t $SESSION_NAME:0.$i "clear" C-m
done

# レイアウトを調整（均等に配置）
tmux select-layout -t $SESSION_NAME:0 tiled

# セッションにアタッチ
tmux attach-session -t $SESSION_NAME

echo "tmuxセッション '$SESSION_NAME' が作成されました"
echo "4x4のペイン構成で以下のようになっています："
echo "  boss01  a01  b01  c01"
echo "  boss02  a02  b02  c02"
echo "  boss03  a03  b03  c03"
echo "  boss04  a04  b04  c04" 