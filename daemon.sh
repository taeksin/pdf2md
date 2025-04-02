#!/bin/sh

# 설정
APP_NAME="pdf2md"                      # 실행할 Python 파일 이름

DAEMON_HOME=$(cd "`dirname $0`" >/dev/null; pwd)
PYTHON_SCRIPT="$APP_NAME.py"           # 실행할 Python 파일 이름
PID_FILE="$DAEMON_HOME/$APP_NAME.pid"    # PID 파일 경로
LOG_FILE="$DAEMON_HOME/log/$APP_NAME.log"  # 로그 파일 경로

# 데몬이 실행 중인지 확인 (PID 파일 이용)
get_daemon_pid() {
    if [ -f "$PID_FILE" ]; then
        pid=$(cat "$PID_FILE")
        if kill -0 "$pid" >/dev/null 2>&1; then
            echo "$pid"
            return 0
        else
            # 프로세스가 존재하지 않는다면 스테일 PID 파일 제거
            rm -f "$PID_FILE"
        fi
    fi
    return 1
}

# 데몬 실행 함수
run_daemon() {
    pid=$(get_daemon_pid)
    if [ -n "$pid" ]; then
        echo "Daemon is already running (pid: $pid)."
        return 0
    fi

    echo "Starting daemon..."
    nohup python "$PYTHON_SCRIPT" > "$LOG_FILE" 2>&1 &
    new_pid=$!
    # 새 PID를 PID 파일에 기록
    echo "$new_pid" > "$PID_FILE"
    sleep 1
    if kill -0 "$new_pid" >/dev/null 2>&1; then
        echo "Daemon started successfully (pid: $new_pid)."
    else
        echo "Failed to start daemon."
        rm -f "$PID_FILE"
    fi
}

# 데몬 정지 함수
stop_daemon() {
    if [ ! -f "$PID_FILE" ]; then
        echo "Daemon is not running."
        return 0
    fi

    pid=$(cat "$PID_FILE")
    if kill -0 "$pid" >/dev/null 2>&1; then
        echo "Stopping daemon (pid: $pid)..."
        kill -TERM "$pid"

        count=1
        TOTAL_WAIT_TIME=30
        while kill -0 "$pid" >/dev/null 2>&1 && [ "$count" -le "$TOTAL_WAIT_TIME" ]; do
            echo "Waiting for daemon to stop... ($count/$TOTAL_WAIT_TIME)"
            sleep 1
            count=$((count+1))
        done

        if kill -0 "$pid" >/dev/null 2>&1; then
            echo "Daemon did not stop in $TOTAL_WAIT_TIME seconds, killing forcefully..."
            kill -KILL "$pid"
            sleep 1
        fi

        echo "Daemon stopped."
        rm -f "$PID_FILE"
    else
        echo "PID file exists but process is not running. Removing stale PID file."
        rm -f "$PID_FILE"
    fi
}

# 스크립트 인자에 따른 동작 선택
case $1 in
    start)
        run_daemon
        ;;
    stop)
        stop_daemon
        ;;
    restart)
        stop_daemon
        echo
        run_daemon
        ;;
    status)
        pid=$(get_daemon_pid)
        if [ -n "$pid" ]; then
            echo "Daemon is running (pid: $pid)."
        else
            echo "Daemon is not running."
        fi
        ;;
    log)
        tail -f "$LOG_FILE"
        ;;
    *)
        echo "Usage: $(basename $0) {start|stop|restart|status|log}"
        exit 1
        ;;
esac

exit 0
