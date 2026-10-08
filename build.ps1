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

# license texts of python and every runtime package (the pyproject dependencies and what they pull in)
# qt wheels only ship the commercial license text, they are used under lgpl-3.0 here, so they get pynput's copy of it
$licenses = @'
import importlib.metadata as md, re, shutil, sys, tomllib
from pathlib import Path
from packaging.requirements import Requirement

out = Path(sys.argv[1])
shutil.rmtree(out, ignore_errors = True)
todo = tomllib.load(open("pyproject.toml", "rb"))["project"]["dependencies"]
seen = {}

while todo:
    req = Requirement(todo.pop())
    if req.marker and not req.marker.evaluate({"extra": ""}):
        continue

    try:
        dist = md.distribution(req.name)
    except md.PackageNotFoundError:
        continue

    key = dist.metadata["Name"]
    if key not in seen:
        seen[key] = dist
        todo += dist.requires or []

lgpl = None
for name, dist in sorted(seen.items()):
    files = [f for f in dist.files or [] if ".dist-info" in str(f) and re.search("LICEN[CS]E|COPYING|NOTICE|AUTHORS", f.name, re.I) and "Commercial" not in f.name]
    for f in files:
        rel = Path(*f.parts[1:])  # drop the dist-info folder, keep nested paths so same-named files don't clash
        rel = Path(*rel.parts[1:]) if rel.parts[0] == "licenses" and len(rel.parts) > 1 else rel
        (out / name / rel).parent.mkdir(parents = True, exist_ok = True)
        shutil.copy(f.locate(), out / name / rel)
        lgpl = f.locate() if f.name == "COPYING.LGPL" else lgpl

for name in seen:
    if re.sub("[-_.]", "", name).lower() in ("pyside6essentials", "shiboken6") and lgpl:
        (out / name).mkdir(parents = True, exist_ok = True)
        shutil.copy(lgpl, out / name / "LGPL-3.0.txt")

(out / "Python").mkdir(parents = True, exist_ok = True)
shutil.copy(Path(sys.base_prefix) / "LICENSE.txt", out / "Python" / "LICENSE.txt")
print(f"licenses of {len(seen) + 1} packages")
'@
$licenses | & .venv\Scripts\python.exe - "dist\Handing\licenses"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "built dist\Handing\Handing.exe ($version)"
