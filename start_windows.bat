@echo off

cd /D "%~dp0"

set PATH=%PATH%;%SystemRoot%\system32

@rem Check if the current directory contains spaces
echo "%CD%" | findstr /C:" " >nul
if %errorlevel% equ 0 (
    echo WARNING: This script relies on Miniconda which may not be silently installed under a path with spaces.
    echo Proceeding with installation. Please ensure to check the installation afterward.
)

@rem Check for special characters in installation path
set "SPCHARMESSAGE=WARNING: Special characters were detected in the installation path! This can cause the installation to fail!"
echo "%CD%" | findstr /R /C:"[!#\$%&()\*+,;<=>?@\[\]\^`{|}~]" >nul && (
    call :PrintBigMessage %SPCHARMESSAGE%
)

@rem Fix failed install when installing to a separate drive
set TMP=%cd%\installer_files
set TEMP=%cd%\installer_files

@rem Deactivate existing conda envs as needed to avoid conflicts
(call conda deactivate && call conda deactivate && call conda deactivate) 2>nul

@rem Configuration
set INSTALL_DIR=%cd%\installer_files
set CONDA_ROOT_PREFIX=%INSTALL_DIR%\conda
set INSTALL_ENV_DIR=%INSTALL_DIR%\env
set MINICONDA_DOWNLOAD_URL=https://repo.anaconda.com/miniconda/Miniconda3-py311_24.3.0-0-Windows-x86_64.exe
set conda_exists=F

@rem Check if conda is already installed
call "%CONDA_ROOT_PREFIX%\_conda.exe" --version >nul 2>&1
if "%ERRORLEVEL%" EQU "0" set conda_exists=T

@rem Download and install Miniconda if not already installed
if "%conda_exists%" == "F" (
    echo Downloading Miniconda from %MINICONDA_DOWNLOAD_URL% to %INSTALL_DIR%\miniconda_installer.exe
    mkdir "%INSTALL_DIR%"
    curl -Lk "%MINICONDA_DOWNLOAD_URL%" -o "%INSTALL_DIR%\miniconda_installer.exe" || (
        echo. 
        echo Miniconda failed to download.
        goto end 
    )

    echo Installing Miniconda to %CONDA_ROOT_PREFIX%
    start /wait "" "%INSTALL_DIR%\miniconda_installer.exe" /InstallationType=JustMe /NoShortcuts=1 /AddToPath=0 /RegisterPython=0 /NoRegistry=1 /S /D=%CONDA_ROOT_PREFIX%

    @rem Test the conda binary
    echo Miniconda version:
    call "%CONDA_ROOT_PREFIX%\_conda.exe" --version || (
        echo. 
        echo Miniconda not found.
        goto end 
    )
)

@rem Remove Intel channel if it exists
call "%CONDA_ROOT_PREFIX%\_conda.exe" config --remove channels intel >nul 2>&1

@rem Create the installer environment
if not exist "%INSTALL_ENV_DIR%" (
    echo Creating conda environment at %INSTALL_ENV_DIR%
    call "%CONDA_ROOT_PREFIX%\_conda.exe" create --no-shortcuts -y -k --prefix "%INSTALL_ENV_DIR%" python=3.11 || (
        echo. 
        echo Conda environment creation failed.
        goto end 
    )
)

@rem Check if conda environment was created
if not exist "%INSTALL_ENV_DIR%\python.exe" (
    echo. 
    echo Conda environment is empty.
    goto end 
)

@rem Environment isolation
set PYTHONNOUSERSITE=1
set PYTHONPATH=
set PYTHONHOME=

@rem Activate installer environment
call "%CONDA_ROOT_PREFIX%\condabin\conda.bat" activate "%INSTALL_ENV_DIR%" || (
    echo. 
    echo Miniconda hook not found.
    goto end 
)

@rem Setup installer environment
call python -W ignore one_click_gpu_updated.py %*

@rem Functions for the script
goto end

:PrintBigMessage
echo. && echo.
echo *******************************************************************
for %%M in (%*) do echo * %%~M
echo *******************************************************************
echo. && echo.
exit /b

:end
pause
