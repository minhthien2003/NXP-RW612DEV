"""Generate a native uVision project from this installed SDK's build metadata.

The generated project builds directly in Keil; Python/west/CMake are needed only
when regenerating after moving or upgrading the SDK. Local board edits survive.
"""
import argparse
import copy
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
MDK = ROOT / "mdk"
NAME = "FRDM_RW612_Test"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sdk", type=Path, default=Path(r"D:\scs\MCUXpresso\mcuxpresso-sdk"))
    parser.add_argument("--keil", type=Path, default=Path(r"C:\Keil_v5"))
    parser.add_argument("--metadata", type=Path, help="Use an existing flash_debug CMake build directory")
    args = parser.parse_args()
    sdk = args.sdk.resolve()
    if (sdk / "mcuxsdk").is_dir():
        sdk /= "mcuxsdk"
    build = args.metadata.resolve() if args.metadata else ROOT / ".build" / "sdk_reference"
    if not args.metadata:
        env = os.environ.copy()
        env["MDK_DIR"] = str(args.keil.resolve())
        subprocess.run([
            "west", "build", "-b", "frdmrw612", "examples/demo_apps/hello_world",
            "--toolchain", "mdk", "--config", "flash_debug", "-d", str(build),
            "--cmake-only", "--", "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
        ], cwd=sdk, env=env, check=True)

    for folder in ("mdk", "board", "config", "linker"):
        (ROOT / folder).mkdir(parents=True, exist_ok=True)
    board = sdk / "examples/_boards/frdmrw612"
    demo = board / "demo_apps/hello_world"
    for origin in [board / f for f in ("board.c", "board.h", "clock_config.c", "clock_config.h")] + [
        demo / f for f in ("pin_mux.c", "pin_mux.h", "hardware_init.c", "app.h")
    ]:
        dest = ROOT / "board" / origin.name
        if not dest.exists():
            shutil.copy2(origin, dest)
    for name in ("mcux_config.h", "mcuxsdk_version.h"):
        shutil.copy2(build / name, ROOT / "config" / name)
    scatter = ROOT / "linker/RW612_flash.scf"
    if not scatter.exists():
        shutil.copy2(sdk / "devices/Wireless/RW/RW612/arm/RW612_flash.scf", scatter)
    shutil.copy2(sdk / "COPYING-BSD-3", ROOT / "NXP-LICENSE.txt")

    def relative(path):
        return os.path.relpath(path, MDK).replace("/", "\\")

    template = sdk / "scripts/guigenerator/templates/mdk/app_frdmrw612"
    tree = ET.parse(template / "app_frdmrw612.uvprojx")
    targets = tree.getroot().find("Targets")
    target = copy.deepcopy(targets.find("Target"))
    targets.clear()
    targets.append(target)

    def set_value(path, value):
        node = target.find(path)
        if node is None:
            raise ValueError(f"Missing template field: {path}")
        node.text = str(value)

    set_value("TargetName", "flash_debug")
    set_value("pCCUsed", "6240000::V6.24::ARMCLANG")
    common = "TargetOption/TargetCommonOption/"
    set_value(common + "PackID", "NXP.RW612_DFP.25.12.00")
    set_value(common + "OutputName", NAME)
    set_value(common + "CreateHexFile", 1)
    set_value(common + "BrowseInformation", 0)
    set_value(common + "SelectedForBatchBuild", 1)
    set_value(common + "AfterMake/RunUserProg1", 1)
    set_value(common + "AfterMake/UserProg1Name", 'fromelf --bincombined --output=".\\Objects\\' + NAME + '.bin" "#L"')

    entries = json.loads((build / "compile_commands.json").read_text())
    command = entries[0]["command"]
    includes = [ROOT / "board", ROOT / "config"]
    for include in re.findall(r"(?:^|\s)-I(\S+)", command):
        path = Path(include)
        if path not in (board, demo):
            includes.append(path)
    include_text = ";".join(relative(p) for p in includes)
    defines = ",".join(re.findall(r"(?:^|\s)-D(\S+)", command))
    arm = "TargetOption/TargetArmAds/"
    flags = '-include "../config/mcux_config.h" -include "../config/mcuxsdk_version.h"'
    set_value(arm + "Cads/VariousControls/Define", defines)
    set_value(arm + "Cads/VariousControls/IncludePath", include_text)
    set_value(arm + "Cads/VariousControls/MiscControls", flags + " -mcpu=cortex-m33+nodsp -mfpu=fpv5-sp-d16 -ffunction-sections -fdata-sections -fno-common -fno-builtin")
    set_value(arm + "Aads/VariousControls/Define", "CPU_RW612ETA2I,RW612_SERIES,MCUXPRESSO_SDK")
    set_value(arm + "Aads/VariousControls/IncludePath", include_text)
    set_value(arm + "Aads/VariousControls/MiscControls", flags + " -mcpu=cortex-m33+nodsp -mfpu=fpv5-sp-d16")
    set_value(arm + "LDads/umfTarg", 0)
    set_value(arm + "LDads/ScatterFile", relative(scatter))
    set_value(arm + "LDads/Misc", "--remove --entry=Reset_Handler --strict --diag_suppress=6314 --cpu=Cortex-M33.no_dsp --fpu=FPv5-SP")

    groups = ET.SubElement(target, "Groups")
    grouped = {}
    for entry in entries:
        path = Path(entry["file"])
        if path.name == "hello_world.c":
            path, group = ROOT / "source/main.c", "Application"
        elif path.parent in (board, demo):
            path, group = ROOT / "board" / path.name, "Board"
        elif "flash_config" in path.parts:
            group = "Boot header"
        elif "components" in path.parts:
            group = "SDK components"
        elif path.name.startswith(("startup_", "system_")):
            group = "Device"
        else:
            group = "SDK drivers"
        if not path.is_file():
            raise FileNotFoundError(path)
        if group not in grouped:
            node = ET.SubElement(groups, "Group")
            ET.SubElement(node, "GroupName").text = group
            grouped[group] = ET.SubElement(node, "Files")
        node = ET.SubElement(grouped[group], "File")
        ET.SubElement(node, "FileName").text = path.name
        ET.SubElement(node, "FileType").text = "2" if path.suffix.lower() == ".s" else "1"
        ET.SubElement(node, "FilePath").text = relative(path)
    ET.indent(tree, space="  ")
    tree.write(MDK / f"{NAME}.uvprojx", encoding="utf-8", xml_declaration=True)

    options = ET.parse(template / "app_frdmrw612.uvoptx")
    optroot = options.getroot()
    for extra in optroot.findall("Target")[1:]:
        optroot.remove(extra)
    opttarget = optroot.find("Target")
    opttarget.find("TargetName").text = "flash_debug"
    # Keep NXP's CMSIS-DAP SWD setup and remove template-specific probe IDs.
    for reg in opttarget.findall(".//SetRegEntry"):
        node = reg.find("Name")
        node.text = re.sub(r'-U\S+\s*', '', node.text or '')
        node.text = re.sub(r'-X"[^"]*"\s*', '', node.text)
    ET.indent(options, space="  ")
    options.write(MDK / f"{NAME}.uvoptx", encoding="utf-8", xml_declaration=True)
    workspace = ET.Element("ProjectWorkspace")
    ET.SubElement(workspace, "SchemaVersion").text = "1.0"
    node = ET.SubElement(workspace, "project")
    ET.SubElement(node, "PathAndName").text = f".\\{NAME}.uvprojx"
    ET.SubElement(node, "NodeIsExpanded").text = "1"
    ET.SubElement(node, "NodeIsCheckedInBatchBuild").text = "1"
    ET.indent(workspace, space="  ")
    ET.ElementTree(workspace).write(MDK / f"{NAME}.uvmpw", encoding="utf-8", xml_declaration=True)
    print(f"Generated {MDK / (NAME + '.uvprojx')} ({len(entries)} source files)")


if __name__ == "__main__":
    main()
