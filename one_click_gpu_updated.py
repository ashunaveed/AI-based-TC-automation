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
TORCH_VERSION = "2.2.1"
TORCHVISION_VERSION = "0.17.1"
TORCHAUDIO_VERSION = "2.2.1"

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

# CPU capability checks
def cpu_has_avx2():
    try:
        import cpuinfo
        return 'avx2' in cpuinfo.get_cpu_info()['flags']
    except:
        return True

def cpu_has_amx():
    try:
        import cpuinfo
        return 'amx' in cpuinfo.get_cpu_info()['flags']
    except:
        return True

# Function to get PyTorch version
def torch_version():
    try:
        site_packages_path = next((sitedir for sitedir in site.getsitepackages() if "site-packages" in sitedir and conda_env_path in sitedir), None)
        if site_packages_path:
            with open(os.path.join(site_packages_path, 'torch', 'version.py')) as f:
                for line in f:
                    if line.startswith('__version__'):
                        return line.split('=')[1].strip().strip("'")
    except Exception as e:
        print(f"Error in detecting torch version: {e}")
    try:
        from torch import __version__ as torver
        return torver
    except ImportError:
        return "Unknown"

# Check if PyTorch is installed
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

# Clear Conda and pip caches
def clear_cache():
    try:
        run_cmd("conda clean -a -y")
        run_cmd("python -m pip cache purge")
    except Exception as e:
        print(f"Error in clearing cache: {e}")

# Print messages in a formatted way
def print_big_message(message):
    print("\n\n*******************************************************************")
    for line in message.strip().split('\n'):
        print("*", line)
    print("*******************************************************************\n\n")

# Calculate file hash
def calculate_file_hash(file_path):
    try:
        p = os.path.join(script_dir, file_path)
        if os.path.isfile(p):
            with open(p, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        else:
            return ''
    except Exception as e:
        print(f"Error in calculating file hash: {e}")
        return ''

# Run a shell command
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

# Install a Python package
def install_package(package_name):
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "install", package_name], check=True, text=True, capture_output=True)
        print(result.stdout)
        print(f"'{package_name}' installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install '{package_name}'. Error: {e.stderr}")

# Detect GPU type
def detect_gpu():
    try:
        install_package("gputil")
        import GPUtil
        if GPUtil.getGPUs():
            return "NVIDIA"
    except:
        pass
    try:
        if sys.platform in ["linux", "darwin"]:
            result = subprocess.run(["lspci"], stdout=subprocess.PIPE, text=True)
            if "AMD" in result.stdout:
                return "AMD"
    except:
        pass
    try:
        if sys.platform == "darwin":
            result = subprocess.run(["system_profiler", "SPDisplaysDataType"], stdout=subprocess.PIPE, text=True)
            if "Apple M" in result.stdout:
                return "APPLE"
    except:
        pass
    try:
        result = subprocess.run(["lspci"], stdout=subprocess.PIPE, text=True)
        if "Intel" in result.stdout:
            return "INTEL"
    except:
        pass
    return "NONE"

# Install the web UI and PyTorch
def install_webui():
    try:
        selected_gpu = detect_gpu()
        print_big_message(f"Detected GPU: {selected_gpu}")
        use_cuda118 = "N"
        if selected_gpu == "NONE":
            with open(cmd_flags_path, 'a+') as cmd_flags_file:
                cmd_flags_file.seek(0)
                if "--cpu" not in cmd_flags_file.read():
                    print_big_message("Adding the --cpu flag to CMD_FLAGS.txt.")
                    cmd_flags_file.write("\n--cpu\n")
        elif is_windows() and selected_gpu == "AMD":
            print("PyTorch setup on Windows for AMD GPUs is not implemented yet. Exiting...")
            sys.exit(1)
        install_pytorch = f"python -m pip install torch=={TORCH_VERSION} torchvision=={TORCHVISION_VERSION} torchaudio=={TORCHAUDIO_VERSION} "
        if selected_gpu == "NVIDIA":
            install_pytorch += "--index-url https://download.pytorch.org/whl/cu118" if use_cuda118 == 'Y' else "--index-url https://download.pytorch.org/whl/cu121"
        elif selected_gpu == "AMD":
            install_pytorch += "--index-url https://download.pytorch.org/whl/rocm5.6"
        elif selected_gpu in ["APPLE", "NONE"]:
            install_pytorch += "--index-url https://download.pytorch.org/whl/cpu"
        elif selected_gpu == "INTEL":
            install_pytorch = "python -m pip install torch==2.1.0a0 torchvision==0.16.0a0 torchaudio==2.1.0a0 intel-extension-for-pytorch==2.1.10+xpu --extra-index-url https://pytorch-extension.intel.com/release-whl/stable/xpu/us/" if is_linux() else "python -m pip install torch==2.1.0a0 torchvision==0.16.0a0 torchaudio==2.1.0a0 intel-extension-for-pytorch==2.1.10 --extra-index-url https://pytorch-extension.intel.com/release-whl/stable/xpu/us/"
        print_big_message("Installing PyTorch.")
        run_cmd(f"conda install -y -k ninja git && {install_pytorch} && python -m pip install py-cpuinfo==9.0.0", assert_success=True)
        if selected_gpu == "INTEL":
            print_big_message("Installing Intel oneAPI runtime libraries.")
            run_cmd("conda install -y -c intel dpcpp-cpp-rt=2024.0 mkl-dpcpp=2024.0")
            run_cmd("conda install -y libuv")
        update_requirements(initial_installation=True)
    except Exception as e:
        print(f"Error in install_webui: {e}")
        sys.exit(1)

# Update PyTorch
def update_pytorch():
    try:
        print_big_message("Checking for PyTorch updates")
        torver = torch_version()
        is_cuda = '+cu' in torver
        is_cuda118 = '+cu118' in torver
        is_rocm = '+rocm' in torver
        is_intel = '+cxx11' in torver
        is_cpu = '+cpu' in torver
        install_pytorch = f"python -m pip install --upgrade torch=={TORCH_VERSION} torchvision=={TORCHVISION_VERSION} torchaudio=={TORCHAUDIO_VERSION} "
        if is_cuda118:
            install_pytorch += "--index-url https://download.pytorch.org/whl/cu118"
        elif is_cuda:
            install_pytorch += "--index-url https://download.pytorch.org/whl/cu121"
        elif is_rocm:
            install_pytorch += "--index-url https://download.pytorch.org/whl/rocm5.6"
        elif is_cpu:
            install_pytorch += "--index-url https://download.pytorch.org/whl/cpu"
        elif is_intel:
            install_pytorch = "python -m pip install --upgrade torch==2.1.0a0 torchvision==0.16.0a0 torchaudio==2.1.0a0 intel-extension-for-pytorch==2.1.10+xpu --extra-index-url https://pytorch-extension.intel.com/release-whl/stable/xpu/us/" if is_linux() else "python -m pip install --upgrade torch==2.1.0a0 torchvision==0.16.0a0 torchaudio==2.1.0a0 intel-extension-for-pytorch==2.1.10 --extra-index-url https://pytorch-extension.intel.com/release-whl/stable/xpu/us/"
        run_cmd(f"{install_pytorch}", assert_success=True)
    except Exception as e:
        print(f"Error in update_pytorch: {e}")
        sys.exit(1)

# Update requirements
def update_requirements(initial_installation=False):
    try:
        if not initial_installation:
            update_pytorch()
        torver = torch_version()
        is_cuda = '+cu' in torver
        is_cuda118 = '+cu118' in torver
        is_rocm = '+rocm' in torver
        is_intel = '+cxx11' in torver
        is_cpu = '+cpu' in torver
        requirements_file = "requirements_cpu_only.txt" if is_cpu or is_intel else "requirements.txt"
        print_big_message(f"Installing webui requirements from file: {requirements_file}")
        print(f"TORCH: {torver}\n")
        textgen_requirements = open(requirements_file).read().splitlines()
        if is_cuda118:
            textgen_requirements = [req.replace('+cu121', '+cu118').replace('+cu122', '+cu118') for req in textgen_requirements]
        if is_windows() and is_cuda118:
            textgen_requirements = [req for req in textgen_requirements if 'oobabooga/flash-attention' not in req]
        with open('temp_requirements.txt', 'w') as file:
            file.write('\n'.join(textgen_requirements))
        git_requirements = [req for req in textgen_requirements if req.startswith("git+")]
        for req in git_requirements:
            url = req.replace("git+", "")
            package_name = url.split("/")[-1].split("@")[0].rstrip(".git")
            run_cmd(f"python -m pip uninstall -y {package_name}")
            print(f"Uninstalled {package_name}")
        run_cmd("python -m pip install -r temp_requirements.txt --upgrade", assert_success=True)
        os.remove('temp_requirements.txt')
        if not any((is_cuda, is_rocm)) and run_cmd("conda list -f pytorch-cuda | grep pytorch-cuda", capture_output=True).returncode == 1:
            clear_cache()
            return
        if not os.path.exists("repositories/"):
            os.mkdir("repositories")
        clear_cache()
    except Exception as e:
        print(f"Error in update_requirements: {e}")
        sys.exit(1)

# Launch the web UI
def launch_webui():
    try:
        flags = f"{' '.join([flag for flag in sys.argv[1:] if flag != '--update-wizard'])} {CMD_FLAGS}"
        run_cmd(f"python -W ignore tender_scheduler.py {flags}", assert_success=True)
    except Exception as e:
        print(f"Error in launch_webui: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        check_env()
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
