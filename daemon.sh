#!/bin/sh

# 설정
APP_NAME="pdf2md"   # 실행할 Python 파일 이름

DAEMON_HOME=$(cd "`dirname $0`" >/dev/null; pwd)
PYTHON_SCRIPT="$APP_NAME.py"  # 실행할 Python 파일 이름
PID_FILE="$DAEMON_HOME/$APP_NAME.pid"    # PID 파일 이름
LOG_FILE="$DAEMON_HOME/log/$APP_NAME.log"      # 로그 파일 이름


daemon_pid() {
    local process_pid=$(ps -eaf | grep "python $PYTHON_SCRIPT" | grep -v grep | awk '{print $2}')
    if [ -n "${process_pid}" ]; then
        echo "${process_pid}"
    fi
}


run_daemon() {
    local pid=$(daemon_pid)
    if [ -n "${pid}" ]; then
        echo "Daemon is already running."
    else
        nohup python $PYTHON_SCRIPT > $LOG_FILE 2>&1 &
        sleep 1;
        local started_daemon_pid=$(daemon_pid)
        if [ -n "${started_daemon_pid}" ]; then
            echo "Daemon is started. (pid: ${started_daemon_pid})"
        else
            echo "Daemon is not started."
        fi
    fi
}

stop_daemon() {
    local pid=$(daemon_pid)
    if [ -n "${pid}" ]; then
        echo "Stoping daemon ..."
        kill -TERM ${pid}

        local count=1
        local count_by=1
        local TOTAL_WAIT_TIME=30

        # 1초 sleep
        sleep ${count_by}

        until [ ${count} -gt ${TOTAL_WAIT_TIME} ]
        do
            if [ `ps -p ${pid} | grep -c ${pid}` = '0' ]; then
                break;
            fi

            echo "Waiting for processes to exit. Timeout before we kill the pid: ${count}/${TOTAL_WAIT_TIME}"
            sleep ${count_by}
            let count=${count}+${count_by};
        done

        if [ ${count} -gt ${TOTAL_WAIT_TIME} ]; then
            echo "Killing processes which didn't stop after ${TOTAL_WAIT_TIME} seconds"
            kill -SIGKILL ${pid}
            exit 1
        fi

        echo "Daemon is stopped. (pid: ${pid})"
    else
        echo "Daemon is not running"
    fi
}

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
        pid=$(daemon_pid)
        if [ -n "${pid}" ]; then
            echo "Daemon is running with pid: ${pid}"
        else
            echo "Daemon is not running"
        fi
        ;;
    log)
        tail -f $LOG_FILE
        ;;
    *)
        echo "Usage: `basename $0` {start|stop|restart|status|log}"
        exit 1
        ;;
esac

exit 0

