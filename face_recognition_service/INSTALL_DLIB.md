# Installing dlib on Windows

dlib requires CMake to be installed on your system. Here are the steps:

## ⚠️ Important: Remove Python cmake package first!

If you have the Python `cmake` package installed, it will interfere with the actual CMake executable:

```bash
pip uninstall cmake -y
```

## Option 1: Install CMake Properly (Recommended)

1. **Download CMake:**
   - Go to https://cmake.org/download/
   - Download the Windows x64 Installer (e.g., `cmake-3.xx.x-windows-x86_64.msi`)

2. **Install CMake:**
   - Run the installer
   - **CRITICAL:** During installation, select "Add CMake to system PATH for all users" or "Add CMake to system PATH for current user"
   - Complete the installation

3. **Restart your terminal/PowerShell** (or close and reopen)

4. **Verify CMake is installed:**
   ```bash
   cmake --version
   ```
   You should see something like: `cmake version 3.xx.x`

5. **Install dlib:**
   ```bash
   pip install dlib
   ```

## Option 2: Install CMake via Chocolatey (If you have Chocolatey)

```bash
choco install cmake
```

Then restart your terminal and install dlib:
```bash
pip install dlib
```

## Option 3: Use Pre-built dlib (If available)

Try installing a pre-built wheel (may not be available for all Python versions):

```bash
pip install dlib-binary
```

## Option 2: Install CMake and Build dlib (Full Setup)

### Prerequisites Required:
1. **CMake** (found at `E:\Program Files\CMake\bin\cmake.exe`)
2. **Visual Studio Build Tools with C++ support**

### Step-by-Step:

1. **Install Visual Studio Build Tools:**
   - Download from: https://visualstudio.microsoft.com/downloads/
   - Scroll down and download "Build Tools for Visual Studio"
   - Run the installer
   - **Select "Desktop development with C++" workload**
   - This includes:
     - MSVC v143 - VS 2022 C++ x64/x86 build tools
     - Windows 10/11 SDK
     - CMake tools for Windows
   - Click "Install"

2. **Add CMake to PATH (if not already there):**
   ```powershell
   # Temporarily for this session:
   $env:Path += ";E:\Program Files\CMake\bin"
   
   # Or permanently via System Properties > Environment Variables
   ```

3. **Restart your terminal/command prompt** (important after installing Visual Studio Build Tools)

4. **Verify CMake is accessible:**
   ```bash
   cmake --version
   ```

5. **Install dlib:**
   ```bash
   pip install dlib
   ```

**Note:** Building dlib can take 10-30 minutes depending on your system.

## Option 3: Use Conda (If you have Anaconda/Miniconda)

```bash
conda install -c conda-forge dlib
```

## Alternative: Use face-recognition without dlib

If you continue having issues, you can modify the service to use OpenCV's face detection instead of face_recognition library, though it won't have the same recognition capabilities.

