# builds dist\Handing\Handing.exe (standalone folder, no console)
# usage: .\build.ps1          first build downloads a c compiler if none is found
# nuitka prints progress on stderr, powershell 5.1 would treat that as an error with "Stop", so only the exit code is checked
# matplotlib and sounddevice stay in: mediapipe's package __init__ files import them
Set-Location $PSScriptRoot

# a short cache path, deep ones push gcc's include paths past the 260 char limit
if (-not $env:NUITKA_CACHE_DIR) { $env:NUITKA_CACHE_DIR = "C:\nuitka-cache" }

$version = (Select-String -Path pyproject.toml -Pattern '^version = "(.+)"').Matches[0].Groups[1].Value

& .venv\Scripts\python.exe -m nuitka `
    --mode=standalone `
    --output-dir=build `
    --output-filename=Handing.exe `
    --enable-plugin=pyside6 `
    --include-qt-plugins=sensible,imageformats,iconengines `
    --include-package=handing `
    --include-package-data=mediapipe `
    --include-data-dir=assets=assets `
    --include-data-dir=src/handing/gui/icons=handing/gui/icons `
    --nofollow-import-to=sklearn,scipy,pytest,tkinter,IPython `
    --windows-console-mode=disable `
    --windows-icon-from-ico=assets/icon/handing.ico `
    --product-name=Handing `
    --file-description="Control your PC with hand gestures" `
    --product-version=$version `
    --file-version=$version `
    --assume-yes-for-downloads `
    src/handing

if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# nuitka names the folder after the package: build\handing.dist
Remove-Item -Recurse -Force dist\Handing -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force dist | Out-Null
Move-Item build\handing.dist dist\Handing

# mediapipe loads its core with ctypes at runtime, nuitka cannot see that, so copy it by hand
$core = "mediapipe\tasks\c\libmediapipe.dll"
New-Item -ItemType Directory -Force (Split-Path "dist\Handing\$core") | Out-Null
Copy-Item ".venv\Lib\site-packages\$core" "dist\Handing\$core"
Write-Host "built dist\Handing\Handing.exe ($version)"
