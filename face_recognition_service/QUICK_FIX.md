# Quick Fix: CMake PATH Issue

## Problem
After uninstalling the Python `cmake` package, CMake is no longer in your PATH.

## Solution

### Step 1: Find where CMake is installed
CMake is usually installed in one of these locations:
- `C:\Program Files\CMake\bin\cmake.exe`
- `C:\Program Files (x86)\CMake\bin\cmake.exe`
- Or check: `C:\Users\YourUsername\AppData\Local\Programs\CMake\bin\cmake.exe`

### Step 2: Add CMake to PATH temporarily (for this session)
```powershell
$env:Path += ";C:\Program Files\CMake\bin"
```

Replace the path with your actual CMake installation path.

### Step 3: Verify CMake works
```powershell
cmake --version
```

### Step 4: Install dlib
```powershell
pip install dlib
```

### Step 5: Add CMake to PATH permanently
1. Press `Win + X` and select "System"
2. Click "Advanced system settings"
3. Click "Environment Variables"
4. Under "System variables", find and select "Path", then click "Edit"
5. Click "New" and add: `C:\Program Files\CMake\bin` (or your CMake path)
6. Click "OK" on all dialogs
7. Restart your terminal

## Next Step: Install Visual Studio Build Tools

CMake is now working, but you also need **Visual Studio Build Tools with C++ support**:

1. Download from: https://visualstudio.microsoft.com/downloads/
2. Scroll down and download "Build Tools for Visual Studio"
3. Run installer and select **"Desktop development with C++"** workload
4. Install (this may take 10-20 minutes)
5. **Restart your terminal**
6. Run: `pip install dlib`

The build process will take 10-30 minutes.

