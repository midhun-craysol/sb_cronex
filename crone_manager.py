import json
import os
import time
import threading
import socket
from datetime import datetime, timedelta
import urllib.request
from urllib.error import URLError
from colorama import init,Fore,Style
init(autoreset=True)
CONFIG_FILE = "crone.json"

def log(msg,color=None):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if color:
        print(f"{ts} : {color}{msg}{Style.RESET_ALL}", flush=True)
    else:
        print(f"{ts} : {msg}", flush=True)


def load_config():
    if not os.path.exists(CONFIG_FILE):
        log("Config file not found.Stopping the program.",Fore.RED)
        return None
    log("Config File Found")
    log("Reading Config file")
    try:
        with open(CONFIG_FILE, "r") as f:
            configs = json.load(f)
        log(f"{len(configs)} URLS found")
        return configs
    except Exception as e:
        log(f"Failed to read config: {e}")
        return []

def call_url(url, method="GET",timeout=30):
    req = urllib.request.Request(url=url, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp

def cron_worker(thread_id, cfg):
    url = cfg.get("url")
    method = cfg.get("method", "GET")
    interval = cfg.get("CallIntervalSeconds", 60)
    fail_retry = cfg.get("FailReryIntervalSeconds", 10)
    skip_count = cfg.get("SkipCallOnFailCount", 3)
    timeout = cfg.get("TimeoutSeconds", 30)
    fail_attempts = 0
    attempt = 0
    log(f"Thread {thread_id} : URL - {url}")
    log(f"Thread {thread_id} : Interval : {interval} sec , FailAttempts : {fail_attempts}")
    log(f"Thread {thread_id} : SkipCallOnFailCount : {skip_count}")
    while True:
        attempt += 1
        log("-" * 50)
        log(f"Thread {thread_id} : Attempt {attempt}")
        log(f"Thread {thread_id} : Calling URL {attempt} - {url}")
        try:
            response_obj = call_url(url, method, timeout)
            status_code = response_obj.status       
            reason = response_obj.reason        
            log(f"Thread {thread_id} : Call OK (HTTP {status_code} ) ",Fore.GREEN)
            fail_attempts = 0
            next_call = datetime.now() + timedelta(seconds=interval)
            log(f"Thread {thread_id} : Next Call at {next_call.strftime('%Y-%m-%d %H:%M:%S')}")
            time.sleep(interval)
        except socket.timeout:
            fail_attempts += 1
            log(f"Thread {thread_id} : Request timed out after {timeout} seconds",Fore.YELLOW)
            if fail_attempts <= skip_count:
                log(f"Thread {thread_id} : Waiting {fail_retry} seconds before retry")
                time.sleep(fail_retry)
            else:
                log(f"Thread {thread_id} : Skipping Call")
                fail_attempts = 0
                attempt = 0
                time.sleep(interval)
        # except URLError as e:
        #     fail_attempts += 1
        #     log(f"Thread {thread_id} : URL Error , {e.reason}")
        #     if fail_attempts <= skip_count:
        #         log(f"Thread {thread_id} : Waiting {fail_retry} seconds before retry")
        #         time.sleep(fail_retry)
        #     else:
        #         log(f"Thread {thread_id} : Skipping Call")
        #         fail_attempts = 0
        #         attempt = 0
        #         time.sleep(interval)
        except Exception as e:
            fail_attempts += 1
            log(f"Thread {thread_id} : Call Fail , {e.reason}",Fore.RED)
            if fail_attempts <= skip_count:
                log(f"Thread {thread_id} : Waiting {fail_retry} seconds before retry")
                time.sleep(fail_retry)
            else:
                log(f"Thread {thread_id} : Skipping Call")
                fail_attempts = 0
                attempt = 0
                time.sleep(interval)

def start_threads(configs):
    log("Creating threads for each URL")
    threads = []
    for index, cfg in enumerate(configs, start=1):
        log(f"Thread {index} : Config - {cfg}")
        t = threading.Thread(target=cron_worker, args=(index, cfg), daemon=True)
        t.start()
        threads.append(t)
    log(f"{len(threads)} Threads Created")
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        log("Cron manager stopped by user.")

def main():
    configs = load_config()
    if not configs:
        log("No URLs to process. Exiting.",Fore.RED)
        return
    start_threads(configs)
    
if __name__ == "__main__":
    main()