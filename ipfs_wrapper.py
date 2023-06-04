import os
import subprocess
import platform
from tkinter import messagebox
from io import BytesIO


class IPFSWrapper:
    def __init__(self):
        self.ipfs_process = None
        self.status = "IPFS Stopped"

    def add(self, file_path):
        try:
            result = subprocess.run(['ipfs', 'add', file_path], capture_output=True, text=True)
            if result.returncode != 0:
                self.error_reporting(result.stderr)
                return None
            lines = result.stdout.strip().split('\n')
            last_line = lines[-1]
            ipfs_hash = last_line.split()[1]
            print(f"File {file_path} added to IPFS with hash {ipfs_hash}")
            return ipfs_hash
        except Exception as e:
            self.error_reporting("Add to IPFS failed.", e)
            return None

    def error_reporting(self, message, e=None):
        if e:
            message += f": {str(e)}"
        print(message)
        messagebox.showerror("IPFS Error", message)

    def cat_file(self, ipfs_hash):
        try:
            result = subprocess.run(['ipfs', 'cat', ipfs_hash], capture_output=True)
            if result.returncode != 0:
                self.error_reporting(result.stderr)
                return None
            file_bytes = BytesIO(result.stdout)
            return file_bytes
        except Exception as e:
            self.error_reporting("Error: Could not get file from IPFS.", e)
            return None

    def get_status(self):
        return "IPFS Stopped" if self.ipfs_process is None else "IPFS Running"

    def pin_add(self, ipfs_hash):
        result = subprocess.run(['ipfs', 'pin', 'add', ipfs_hash], capture_output=True, text=True)
        if result.returncode != 0:
            self.error_reporting(result.stderr)
            return None
        pinned_hash = ipfs_hash
        print(f"File with IPFS hash {ipfs_hash} pinned")
        return pinned_hash

    def pin_rm(self, ipfs_hash):
        result = subprocess.run(['ipfs', 'pin', 'rm', ipfs_hash], capture_output=True, text=True)
        if result.returncode != 0:
            self.error_reporting(result.stderr)
            return None
        unpinned_hash = ipfs_hash
        print(f"File with IPFS hash {ipfs_hash} unpinned")
        return unpinned_hash

    def start_daemon(self):
        if self.ipfs_process is None:
            with open(os.devnull, 'w') as devnull:
                if platform.system() == 'Windows':
                    self.ipfs_process = subprocess.Popen('start /B ipfs daemon > NUL 2>&1', shell=True, stdout=devnull, stderr=devnull)
                else:
                    self.ipfs_process = subprocess.Popen(['ipfs', 'daemon'], stdout=devnull, stderr=devnull, preexec_fn=os.setpgrp)
            print("IPFS daemon started")
            self.get_status()

    def stop_daemon(self):
        if self.ipfs_process is not None:
            if platform.system() == 'Windows':
                subprocess.call('ipfs shutdown', shell=True)
            else:
                subprocess.call(['ipfs', 'shutdown'])
            self.ipfs_process.wait()
            self.ipfs_process = None
            print("IPFS daemon stopped")
            self.get_status()


if __name__ == '__main__':
    ipfs_wrapper = IPFSWrapper()
