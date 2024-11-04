import argparse
import glob
import hashlib
import os
import platform
import re
import signal
import site
import subprocess
import sys

# Define the required PyTorch version
TORCH_VERSION = "2.5.1"
TORCHVISION_VERSION = "0.20.1"
TORCHAUDIO_VERSION = "2.5.1"

# Environment
script_dir = os.path.dirname(os.path.abspath(__file__))
conda_env_path = os.path.join(script_dir, "installer_files", "env")

# Command-line flags
cmd_flags_path = os.path.join(script_dir, "CMD_FLAGS.txt")
if os.path.exists(cmd_flags_path):
    with open(cmd_flags_path, 'r') as f:
        CMD_FLAGS = ' '.join(line.strip().rstrip('\\').strip() for line in f if line.strip().rstrip('\\').strip() and not line.strip().startswith('#'))
else:
    CMD_FLAGS = ''

# Signal handler to handle interruption
def signal_handler(sig, frame):
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

# Platform checks
def is_linux():
    return sys.platform.startswith("linux")

def is_windows():
    return sys.platform.startswith("win")

def is_macos():
    return sys.platform.startswith("darwin")

def is_x86_64():
    return platform.machine() == "x86_64"

def check_and_install_requirements():
    try:
        with open('requirements.txt', 'r') as req_file:
            packages = req_file.read().splitlines()
        
        missing_packages = []
        for package in packages:
            package_name = package.split('=')[0].strip()  # Extract package name without version
            try:
                __import__(package_name)
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            print("Installing missing packages from requirements.txt...")
            for package in missing_packages:
                install_package(package)
        else:
            print("All packages in requirements.txt are already installed.")
        package_name = "llama_cpp_python"
        cuda_package_url = "https://github.com/abetlen/llama-cpp-python/releases/download/v0.2.90-cu124/llama_cpp_python-0.2.90-cp311-cp311-win_amd64.whl"
        cpu_package_url = "https://github.com/abetlen/llama-cpp-python/releases/download/v0.2.90/llama_cpp_python-0.2.90-cp311-cp311-win_amd64.whl"
        # Main logic
        if is_package_installed(package_name):
            print(f"{package_name} is already installed.")
        else:
            # Check for CUDA capability
            if has_cuda():
                print(f"CUDA detected. Installing {package_name} with CUDA support.")
                install_package(cuda_package_url)
            else:
                print(f"No CUDA detected. Installing {package_name} CPU-only version.")
                install_package(cpu_package_url)
        


    except FileNotFoundError:
        print("requirements.txt file not found.")
        sys.exit(1)

def run_cmd(cmd, assert_success=False, capture_output=False, env=None):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=capture_output, text=True, env=env)
        if assert_success and result.returncode != 0:
            print(f"Command '{cmd}' failed with exit status {result.returncode}.")
            print(f"Error: {result.stderr}")
            sys.exit(1)
        return result
    except Exception as e:
        print(f"Error running command: {cmd}. Exception: {e}")
        sys.exit(1)
def is_installed():
    try:
        site_packages_path = next((sitedir for sitedir in site.getsitepackages() if "site-packages" in sitedir and conda_env_path in sitedir), None)
        if site_packages_path:
            return os.path.isfile(os.path.join(site_packages_path, 'torch', '__init__.py'))
        else:
            return os.path.isdir(conda_env_path)
    except Exception as e:
        print(f"Error in checking installation: {e}")
        return False
def launch_webui():
    try:
        flags = f"{' '.join([flag for flag in sys.argv[1:] if flag != '--update-wizard'])} {CMD_FLAGS}"
        run_cmd(f"python -W ignore tender_scheduler.py {flags}", assert_success=True)
    except Exception as e:
        print(f"Error in launch_webui: {e}")
        sys.exit(1)


# Check Conda environment
def check_env():
    try:
        result = run_cmd("conda", capture_output=True)
        if result.returncode != 0:
            print("Conda is not installed or not found in PATH. Exiting...")
            sys.exit(1)
        if os.environ.get("CONDA_DEFAULT_ENV") == "base":
            print("Please create and activate a specific environment for this project. Exiting...")
            sys.exit(1)
    except Exception as e:
        print(f"Error in checking environment: {e}")
        sys.exit(1)

# Install a Python package
def install_package(package_name):
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "install", package_name], check=True, text=True, capture_output=True)
        print(result.stdout)
        print(f"'{package_name}' installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install '{package_name}'. Error: {e.stderr}")

import subprocess
import sys

def is_package_installed(package_name):
    """Check if a package is installed."""
    try:
        import pkg_resources
        pkg_resources.get_distribution(package_name)
        return True
    except pkg_resources.DistributionNotFound:
        return False

def has_cuda():
    """Check if CUDA is available by running 'nvidia-smi'."""
    try:
        subprocess.run(["nvidia-smi"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def install_package(package_url):
    """Install the package using pip."""
    subprocess.run([sys.executable, "-m", "pip", "install", package_url])

# Package name and URLs for conditional installation




# Main execution logic
if __name__ == "__main__":
    try:
        check_and_install_requirements()  # Ensure packages from requirements.txt are installed
        check_env()  # Rest of the script execution
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument('--update-wizard', action='store_true', help='Launch a menu with update options.')
        args, _ = parser.parse_known_args()
        
        if not is_installed():
            install_webui()
            os.chdir(script_dir)
            if os.environ.get("LAUNCH_AFTER_INSTALL", "").lower() in ("no", "n", "false", "0", "f", "off"):
                print_big_message("Will now exit due to LAUNCH_AFTER_INSTALL.")
                sys.exit()
            if '--model-dir' in sys.argv:
                flags_list = re.split(' +(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)|=', ' '.join(sys.argv))
                model_dir = next((flags_list[flags_list.index(flag) + 1].strip('"\'') for flag in flags_list if flag == '--model-dir'), 'models')
            else:
                model_dir = 'models'
            if len([item for item in glob.glob(f'{model_dir}/*') if not item.endswith(('.txt', '.yaml'))]) == 0:
                print_big_message("You haven't downloaded any model yet.\nOnce the web UI launches, head over to the \"Model\" tab and download one.")
            conda_path_bin = os.path.join(conda_env_path, "bin")
            if not os.path.exists(conda_path_bin):
                os.mkdir(conda_path_bin)
            launch_webui()
        else:
            print("Web UI is already installed. Launching the web UI.")
            launch_webui()
    except Exception as e:
        print(f"Unhandled exception: {e}")
        sys.exit(1)
