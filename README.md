# Autotests for Radeon ML and Radeon ML performance

## Requirements
* TensorRT v.7.0.0.11 (https://developer.nvidia.com/compute/machine-learning/tensorrt/secure/7.0/7.0.0.11/zips/TensorRT-7.0.0.11.Windows10.x86_64.cuda-10.0.cudnn7.6.zip)
* CUDA v.10.0 (https://developer.nvidia.com/cuda-10.0-download-archive)
* cuDNN v.7.6.x (https://developer.nvidia.com/rdp/cudnn-archive)
* Add <tensorrt_path>/lib in PATH env variable (documentation: https://docs.nvidia.com/deeplearning/tensorrt/archives/tensorrt-700/tensorrt-install-guide/index.html#installing-zip)
* Add <cuDNN>/bin in PATH env variable (documentation: https://docs.nvidia.com/deeplearning/cudnn/install-guide/index.html)
* WinML v.1.2.2 (https://github.com/microsoft/Windows-Machine-Learning/releases/download/v1.2.2/WinMLRunner.zip)
* RadeonML v.0.9.9

## Install
 1. Clone this repo
 2. Get `jobs_launcher` as git submodule, using next commands
 `git submodule init`
 `git submodule update`
 3. Check that `MLAssets` scenes placed in `C:/TestResources`
 4. Run `scripts/run.bat` with customised `--cmd_variables`.