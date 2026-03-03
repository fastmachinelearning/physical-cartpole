"""Helper functions for Step 6 notebook orchestration.

This module keeps notebook cells focused on tutorial flow while preserving the
existing Step 6 behavior, command sequence, and defaults.
"""

from __future__ import annotations

import csv
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


def _run_cmd_live(cmd: list[str], cwd: Path, env: dict[str, str] | None = None) -> None:
    cmd = [str(c) for c in cmd]
    print("$", " ".join(cmd))
    print("cwd:", cwd)
    subprocess.run(cmd, cwd=str(cwd), env=env, check=True)


def _resolve_hls4ml_output_dir(repo: Path, hls_output_abs: Path | None = None) -> Path | None:
    marker_rel = Path("myproject_prj") / "solution1" / "impl" / "vhdl" / "myproject.vhd"

    if hls_output_abs is not None:
        candidate = Path(hls_output_abs)
        if (candidate / marker_rel).exists():
            return candidate

    env_hls_output = os.environ.get("CARTPOLE_HLS_OUTPUT", "").strip()
    if env_hls_output:
        candidate = repo / "HLS4ML" / env_hls_output
        if (candidate / marker_rel).exists():
            return candidate

    markers = sorted(
        (repo / "HLS4ML").glob("*/myproject_prj/solution1/impl/vhdl/myproject.vhd"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if markers:
        return markers[0].parents[4]
    return None


def ensure_notebook_repo_context(
    nb_globals: dict[str, Any],
    missing_repo_message: str = "Run Step 1.1 first so REPO is defined once for this notebook.",
    ensure_sys_path: bool = True,
) -> Path:
    repo = nb_globals.get("REPO")
    if repo is None:
        raise RuntimeError(missing_repo_message)

    repo_path = Path(repo)
    if ensure_sys_path:
        repo_str = str(repo_path)
        if repo_str not in sys.path:
            sys.path.insert(0, repo_str)
    return repo_path


def resolve_selected_model_name(nb_globals: dict[str, Any], default_net_name: str) -> str:
    net_info = nb_globals.get("net_info")
    if net_info is not None and hasattr(net_info, "net_full_name"):
        return str(net_info.net_full_name)
    return str(default_net_name)


def run_step3_launcher(repo: Path, net_name: str | None) -> None:
    script = repo / "step3.sh"
    if not script.exists():
        raise FileNotFoundError(f"Missing simulator launcher: {script}")
    script.chmod(script.stat().st_mode | 0o111)

    args = ["bash", str(script)]
    if net_name:
        args.append(str(net_name))

    print("Notebook CWD:", Path.cwd().resolve())
    print("Repo root:", repo)
    print("Running:", " ".join(args))

    # Run from repo root so relative paths inside step3.sh resolve.
    subprocess.run(args, cwd=str(repo), check=True)


def set_training_experiment_path(cfg_path: Path, active_experiment: Path) -> bool:
    cfg = yaml.safe_load(cfg_path.read_text())

    def set_experiment_path(cfg_obj: Any, new_path: str) -> bool:
        if isinstance(cfg_obj, dict):
            if (
                "paths" in cfg_obj
                and isinstance(cfg_obj["paths"], dict)
                and "path_to_experiment" in cfg_obj["paths"]
            ):
                cfg_obj["paths"]["path_to_experiment"] = new_path
                return True
            if "PATH_TO_EXPERIMENT" in cfg_obj:
                cfg_obj["PATH_TO_EXPERIMENT"] = new_path
                return True
        return False

    ok = set_experiment_path(cfg, str(active_experiment))
    if ok:
        cfg_path.write_text(yaml.safe_dump(cfg, sort_keys=False))
        print("Updated config_training.yml to use:", active_experiment)
    else:
        print("Could not locate experiment path key; set it manually to:", active_experiment)
    return ok


def _normalize_vivado_bin(path_value: str | Path) -> Path:
    p = Path(str(path_value)).expanduser()
    return p if p.name == "bin" else (p / "bin")


def _extract_vivado_version(vivado_exe: Path) -> str:
    out = subprocess.check_output(
        [str(vivado_exe), "-version"],
        text=True,
        stderr=subprocess.STDOUT,
        errors="ignore",
    )
    for line in out.splitlines():
        if "Vivado v" in line:
            return line.strip()
    return out.splitlines()[0].strip() if out.strip() else "<unknown>"


def _resolve_vivado_bin(expected_version: str, cfg_vivado_path: str) -> tuple[Path, str]:
    candidates: list[Path] = []

    vivado_root = os.environ.get("XILINX_VIVADO", "").strip()
    if vivado_root:
        candidates.append(_normalize_vivado_bin(vivado_root))

    if cfg_vivado_path:
        candidates.append(_normalize_vivado_bin(cfg_vivado_path))

    vivado_on_path = shutil.which("vivado")
    if vivado_on_path:
        candidates.append(Path(vivado_on_path).resolve().parent)

    candidates.extend(
        [
            Path(f"/tools/Xilinx/Vivado/{expected_version}/bin"),
            Path(f"/mnt/raid5/fpga/cad/xilinx/Vivado/{expected_version}/bin"),
            Path(f"/fpga_raid5/cad/xilinx/Vivado/{expected_version}/bin"),
            Path(f"/mnt/xilinx/Xilinx/Vivado/{expected_version}/bin"),
        ]
    )

    checked: list[str] = []
    seen: set[str] = set()
    for c in candidates:
        c = Path(c)
        key = str(c)
        if key in seen:
            continue
        seen.add(key)

        vivado_exe = c / "vivado"
        if not vivado_exe.exists():
            checked.append(f"{c} (missing vivado)")
            continue

        try:
            version_line = _extract_vivado_version(vivado_exe)
        except Exception as exc:
            checked.append(f"{vivado_exe} (version check failed: {exc})")
            continue

        checked.append(f"{vivado_exe} -> {version_line}")
        if f"v{expected_version}" in version_line:
            return c, version_line

    raise RuntimeError(
        f"Could not resolve Vivado v{expected_version}. Checked:\n - " + "\n - ".join(checked)
    )


def _resolve_vivado_gcc_bin(vivado_bin: Path) -> Path | None:
    vivado_root = Path(vivado_bin).parent
    candidates = [
        vivado_root / "tps" / "lnx64" / "gcc-6.2.0" / "bin",
        vivado_root / "tps" / "lnx64" / "gcc-9.3.0" / "bin",
        vivado_root / "tps" / "lnx64" / "gcc-10.2.0" / "bin",
        vivado_root / "tps" / "lnx64" / "gcc-11.2.0" / "bin",
    ]
    for c in candidates:
        if (c / "gcc").exists() and (c / "g++").exists():
            return c
    return None


def _write_cosim_gcc_wrapper(wrapper_dir: Path, real_gcc_bin: Path) -> None:
    wrapper_dir = Path(wrapper_dir)
    real_gcc_bin = Path(real_gcc_bin)
    wrapper_dir.mkdir(parents=True, exist_ok=True)

    script_template = """#!/usr/bin/env bash
set -euo pipefail
REAL_COMPILER="__REAL_COMPILER__"
args=()
while (($#)); do
  case "$1" in
    -I)
      if [[ $# -ge 2 && "$2" == "/usr/include/x86_64-linux-gnu" ]]; then
        shift 2
        continue
      fi
      args+=("$1")
      shift
      if (($#)); then
        args+=("$1")
        shift
      fi
      ;;
    -I/usr/include/x86_64-linux-gnu)
      shift
      ;;
    *)
      args+=("$1")
      shift
      ;;
  esac
done
exec "$REAL_COMPILER" "${args[@]}"
"""

    for tool in ("gcc", "g++"):
        wrapper = wrapper_dir / tool
        wrapper.write_text(script_template.replace("__REAL_COMPILER__", str(real_gcc_bin / tool)))
        wrapper.chmod(0o755)


def prepare_hls_toolchain_context(
    repo: Path,
    sim: Path,
    hls_cfg: dict[str, Any],
    hls_models_dir: Path,
    selected_net_name: str,
    xilinx_tool_version: str = "2020.1",
) -> dict[str, Any]:
    run_tag = datetime.now().strftime("%Y%m%d_%H%M%S")

    vivado_bin, vivado_version_line = _resolve_vivado_bin(
        xilinx_tool_version,
        str(hls_cfg.get("path_to_hls_installation", "")).strip(),
    )

    os.environ["XILINX_VIVADO"] = str(vivado_bin.parent)
    os.environ["XILINX_HLS"] = str(vivado_bin.parent)
    os.environ["PATH"] = f"{vivado_bin}:{os.environ.get('PATH', '')}"

    resolved_gcc_bin = _resolve_vivado_gcc_bin(vivado_bin)
    if resolved_gcc_bin is not None:
        # Vivado 2020.1 cosim can pick host GMP headers via /usr include path.
        # Route cosim gcc/g++ through a wrapper that removes that include so
        # Vivado's bundled GMP/MPFR headers are used consistently.
        if xilinx_tool_version == "2020.1":
            gcc_wrapper_dir = repo / ".cache" / f"vivado_gcc_wrapper_{xilinx_tool_version.replace('.', '_')}"
            _write_cosim_gcc_wrapper(gcc_wrapper_dir, resolved_gcc_bin)
            os.environ["AP_GCC_PATH"] = str(gcc_wrapper_dir)
            os.environ["CARTPOLE_REAL_AP_GCC_PATH"] = str(resolved_gcc_bin)
        else:
            os.environ["AP_GCC_PATH"] = str(resolved_gcc_bin)
            os.environ.pop("CARTPOLE_REAL_AP_GCC_PATH", None)

    if not (hls_models_dir / selected_net_name).exists():
        raise FileNotFoundError(
            f"Selected model directory not found: {hls_models_dir / selected_net_name}"
        )

    hls_output_name = os.environ.get("CARTPOLE_HLS_OUTPUT", f"{selected_net_name}_{run_tag}")
    hls_output_abs = repo / "HLS4ML" / hls_output_name
    hls_output_rel = os.path.relpath(hls_output_abs, sim)

    print("Xilinx tool version target:", xilinx_tool_version)
    print("Resolved Vivado bin:", vivado_bin)
    print("Resolved Vivado version:", vivado_version_line)
    print("Resolved AP_GCC_PATH:", os.environ.get("AP_GCC_PATH", "<unset>"))
    if os.environ.get("CARTPOLE_REAL_AP_GCC_PATH"):
        print("Resolved real GCC bin:", os.environ["CARTPOLE_REAL_AP_GCC_PATH"])
    print("Resolved model dir:", hls_models_dir / selected_net_name)
    print("Resolved output dir:", hls_output_abs)
    print("Resolved output rel:", hls_output_rel)

    return {
        "run_tag": run_tag,
        "xilinx_tool_version": xilinx_tool_version,
        "vivado_bin": vivado_bin,
        "vivado_version_line": vivado_version_line,
        "hls_output_name": hls_output_name,
        "hls_output_abs": hls_output_abs,
        "hls_output_rel": hls_output_rel,
    }


def update_hls_config_with_backup(
    hls_config: Path,
    hls_cfg: dict[str, Any],
    vivado_bin: Path,
    hls_models_dir: Path,
    sim: Path,
    selected_net_name: str,
    hls_output_rel: str,
    run_tag: str,
) -> Path:
    backup_path = hls_config.with_suffix(f".yml.bak_{run_tag}")
    shutil.copy2(hls_config, backup_path)

    hls_cfg["path_to_hls_installation"] = str(vivado_bin)
    hls_cfg["path_to_models"] = os.path.relpath(hls_models_dir, sim)
    hls_cfg["net_name"] = selected_net_name
    hls_cfg["output_dir"] = hls_output_rel

    with hls_config.open("w") as f:
        yaml.safe_dump(hls_cfg, f, sort_keys=False)

    print("Backup created:", backup_path)
    print("Updated config:", hls_config)
    return backup_path


def patch_controller_name(repo: Path, apply_controller_patch: bool = True) -> None:
    globals_py = repo / "Driver" / "globals.py"
    text = globals_py.read_text()
    match = re.search(r'^CONTROLLER_NAME\s*=\s*[\'"]([^\'"]+)[\'"]', text, flags=re.M)

    print("globals.py:", globals_py)
    print("Current CONTROLLER_NAME:", match.group(1) if match else "not found")

    new_text, count = re.subn(
        r'^CONTROLLER_NAME\s*=\s*[\'"][^\'"]+[\'"]',
        "CONTROLLER_NAME = 'neural-imitator'",
        text,
        count=1,
        flags=re.M,
    )
    if count != 1:
        raise RuntimeError("Could not patch CONTROLLER_NAME in globals.py")

    if apply_controller_patch:
        globals_py.write_text(new_text)
        print("Patched CONTROLLER_NAME -> neural-imitator")
    else:
        print("Dry run only. Set APPLY_CONTROLLER_PATCH=True to write.")


def patch_manual_serial_override(
    repo: Path,
    serial_port_override: str = "/dev/tty.usbserial-210351B7BD461",
    apply_serial_patch: bool = True,
) -> None:
    interface_py = repo / "Driver" / "DriverFunctions" / "interface.py"
    text = interface_py.read_text()

    print("interface.py:", interface_py)

    if "MANUAL_SERIAL_PORT =" not in text:
        text = text.replace(
            "import pandas as pd\n",
            "import pandas as pd\n\nMANUAL_SERIAL_PORT = None  # e.g. '/dev/tty.usbserial-XXXX'\n",
            1,
        )

    if "Using manual serial port override" not in text:
        marker = "    from serial.tools import list_ports\n"
        text = text.replace(
            marker,
            "    if MANUAL_SERIAL_PORT:\n"
            "        print(f'Using manual serial port override: {MANUAL_SERIAL_PORT}')\n"
            "        return MANUAL_SERIAL_PORT\n\n" + marker,
            1,
        )

    text, n = re.subn(
        r"^MANUAL_SERIAL_PORT\s*=.*$",
        f"MANUAL_SERIAL_PORT = {serial_port_override!r}",
        text,
        count=1,
        flags=re.M,
    )
    if n != 1:
        raise RuntimeError("Could not set MANUAL_SERIAL_PORT")

    if apply_serial_patch:
        interface_py.write_text(text)
        print("Patched manual serial-port override")
    else:
        print("Dry run only. Set APPLY_SERIAL_PATCH=True to write.")


def patch_model_config(
    repo: Path,
    net_name: str = "Dense-7IN-32H1-32H2-1OUT-0",
    path_to_models: str = "./CartPoleSimulation/SI_Toolkit_ASF/Experiments/Experiment-1/Models/",
    apply_model_config_patch: bool = True,
) -> None:
    controllers_yml = repo / "Driver" / "CartPoleSimulation" / "Control_Toolkit_ASF" / "config_controllers.yml"
    cfg = yaml.safe_load(controllers_yml.read_text())
    ni = cfg.setdefault("neural-imitator", {})

    print("config_controllers.yml:", controllers_yml)
    print("Current PATH_TO_MODELS:", ni.get("PATH_TO_MODELS"))
    print("Current net_name:", ni.get("net_name"))
    print("Current input_precision:", ni.get("input_precision"))
    print("Current hls4ml:", ni.get("hls4ml"))

    ni["PATH_TO_MODELS"] = path_to_models
    ni["net_name"] = net_name
    ni["input_precision"] = "float"
    ni["hls4ml"] = False

    if apply_model_config_patch:
        controllers_yml.write_text(yaml.safe_dump(cfg, sort_keys=False))
        print("Patched neural-imitator model configuration")
    else:
        print("Dry run only. Set APPLY_MODEL_CONFIG_PATCH=True to write.")


def set_automation_scripts_executable(repo: Path) -> None:
    for rel in ["install_zybo_board.sh", "generate_bitstream.tcl", "generate_vitis_project.tcl"]:
        path = repo / rel
        path.chmod(path.stat().st_mode | 0o111)
        print("Executable bit set:", path)


def preflight_step6(
    repo: Path,
    expected_vivado_version: str = "2020.1",
    vivado_bin: str | Path | None = None,
) -> dict[str, Any]:
    required = [
        repo / "install_zybo_board.sh",
        repo / "generate_bitstream.tcl",
        repo / "generate_vitis_project.tcl",
        repo / "Firmware" / "create_symlinks_cartpole.sh",
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise FileNotFoundError("Missing required implementation files:\n - " + "\n - ".join(missing))

    if vivado_bin is not None:
        vivado_exe = Path(vivado_bin) / "vivado"
    else:
        vivado_path = shutil.which("vivado")
        if not vivado_path:
            raise RuntimeError("vivado not found in PATH")
        vivado_exe = Path(vivado_path)

    if not vivado_exe.exists():
        raise RuntimeError(f"Vivado executable not found: {vivado_exe}")

    vivado_version_out = subprocess.check_output(
        [str(vivado_exe), "-version"],
        text=True,
        stderr=subprocess.STDOUT,
        errors="ignore",
    )
    vivado_version_line = next(
        (l.strip() for l in vivado_version_out.splitlines() if "Vivado v" in l),
        vivado_version_out.splitlines()[0].strip() if vivado_version_out.strip() else "<unknown>",
    )

    if f"v{expected_vivado_version}" not in vivado_version_line:
        raise RuntimeError(
            f"Vivado version mismatch. Expected {expected_vivado_version}, got: {vivado_version_line}"
        )

    os.environ["PATH"] = f"{vivado_exe.parent}:{os.environ.get('PATH', '')}"

    print("vivado:", vivado_exe)
    print("vivado -version:", vivado_version_line)
    print("xsct:", shutil.which("xsct") or "NOT FOUND in PATH")
    print("Vivado version target:", expected_vivado_version)
    print("Vitis version target: 2020.1")

    return {
        "vivado_exe": vivado_exe,
        "vivado_version_line": vivado_version_line,
        "expected_vivado_version": expected_vivado_version,
    }


def run_step62_symlink_and_permissions_prep(repo: Path) -> None:
    symlink_script = repo / "Firmware" / "create_symlinks_cartpole.sh"
    if symlink_script.exists():
        print("Assuming NeuralImitator symlink block stays disabled; no edits applied.")
    else:
        print(f"Warning: Missing symlink script: {symlink_script}")

    for rel in ["install_zybo_board.sh", "generate_bitstream.tcl", "generate_vitis_project.tcl"]:
        path = repo / rel
        path.chmod(path.stat().st_mode | 0o111)
        print(f"Executable bit set: {path}")


def apply_step63_parameter_patch(
    repo: Path,
    apply_parameter_patch: bool = True,
    new_motor_correction: list[float] | None = None,
    new_angle_hanging_pololu: float = 783.0,
) -> None:
    if new_motor_correction is None:
        new_motor_correction = [0.6310468, 0.0472680, 0.0408973]

    parameters_c = repo / "Firmware" / "Src" / "CartPoleFirmware" / "parameters.c"
    text = parameters_c.read_text()
    block = re.search(r"#elif defined\(ZYNQ\)(.*?)#endif", text, flags=re.S)
    if not block:
        raise RuntimeError("Could not find ZYNQ block in parameters.c")

    curr = block.group(1)
    print(
        "Current MOTOR_CORRECTION:",
        re.search(r"MOTOR_CORRECTION\[3\]\s*=\s*\{([^}]*)\};", curr).group(1).strip(),
    )
    print(
        "Current ANGLE_HANGING_POLOLU:",
        re.search(r"ANGLE_HANGING_POLOLU\s*=\s*([0-9eE+\-.]+);", curr).group(1).strip(),
    )

    patched = re.sub(
        r"float\s+MOTOR_CORRECTION\[3\]\s*=\s*\{[^}]*\};",
        f"float MOTOR_CORRECTION[3] = {{{', '.join(f'{v:.7f}' for v in new_motor_correction)}}};",
        curr,
        count=1,
    )
    patched = re.sub(
        r"float\s+ANGLE_HANGING_POLOLU\s*=\s*[0-9eE+\-.]+;",
        f"float ANGLE_HANGING_POLOLU = {float(new_angle_hanging_pololu):.4f};",
        patched,
        count=1,
    )

    if apply_parameter_patch:
        text = text[: block.start(1)] + patched + text[block.end(1) :]
        parameters_c.write_text(text)
        print("Updated parameters.c")
    else:
        print("Dry run only. Set APPLY_PARAMETER_PATCH=True to write.")


def _first_existing(paths: list[Path]) -> Path | None:
    for p in paths:
        if p.exists():
            return p
    return None


def _load_csv_vector(path: Path) -> list[float]:
    if not path.exists():
        raise FileNotFoundError(f"Missing CSV: {path}")
    vals = [float(x) for row in csv.reader(path.open()) for x in row if x.strip()]
    if not vals:
        raise ValueError(f"No numeric values in {path}")
    return vals


def apply_step63_normalization_patch(
    repo: Path,
    apply_normalization_patch: bool = True,
    update_network_header: bool = True,
    model_dir: Path | None = None,
    net_name: str = "Dense-7IN-32H1-32H2-1OUT-0",
) -> dict[str, Path]:
    if model_dir is None:
        model_dir = (
            repo
            / "Driver"
            / "CartPoleSimulation"
            / "SI_Toolkit_ASF"
            / "Experiments"
            / "Experiment-1"
            / "Models"
            / str(net_name)
        )

    neural_c = _first_existing(
        [
            repo / "Firmware" / "Src" / "Zynq" / "neural_imitator.c",
            repo / "Firmware" / "Src" / "Zynq" / "neural-imitator.c",
        ]
    )
    neural_h = _first_existing(
        [
            repo / "Firmware" / "Src" / "Zynq" / "neural_imitator.h",
            repo / "Firmware" / "Src" / "Zynq" / "neural-imitator.h",
        ]
    )
    if neural_c is None or neural_h is None:
        raise FileNotFoundError("Could not find neural_imitator.c/.h under Firmware/Src/Zynq")

    files = {
        "hls_normalize_a": model_dir / "normalization_vec_a.csv",
        "hls_normalize_b": model_dir / "normalization_vec_b.csv",
        "hls_denormalize_A": model_dir / "denormalization_vec_A.csv",
        "hls_denormalize_B": model_dir / "denormalization_vec_B.csv",
    }

    print("MODEL_DIR:", model_dir)
    print("NEURAL_C:", neural_c)
    print("NEURAL_H:", neural_h)
    for key, fp in files.items():
        print(key, fp.exists(), fp)

    if apply_normalization_patch:
        c_text = neural_c.read_text()
        for key, fp in files.items():
            vals = _load_csv_vector(fp)
            body = ", ".join(f"{v:.9g}f" for v in vals)
            pattern = rf"(?ms)^\s*(?:static\s+)?(?:const\s+)?float\s+{re.escape(key)}\s*\[[^\]]*\]\s*=\s*\{{.*?\}}\s*;"
            repl = f"float {key}[] = {{{body}}};"
            c_text, n = re.subn(pattern, repl, c_text, count=1)
            if n != 1:
                raise RuntimeError(f"Could not patch {key} in {neural_c}")
        neural_c.write_text(c_text)
        print("Updated", neural_c)

    if update_network_header:
        h_text = neural_h.read_text()
        in_n = len(_load_csv_vector(files["hls_normalize_a"]))
        out_n = len(_load_csv_vector(files["hls_denormalize_A"]))

        h_text, n1 = re.subn(
            r"(?m)^\s*#define\s+MLP_ACTIVATION_NEURONS\s+\d+",
            f"#define MLP_ACTIVATION_NEURONS\t\t{in_n}",
            h_text,
            count=1,
        )
        h_text, n2 = re.subn(
            r"(?m)^\s*#define\s+MLP_PREDICTION_NEURONS\s+\d+",
            f"#define MLP_PREDICTION_NEURONS\t\t{out_n}",
            h_text,
            count=1,
        )
        if n1 != 1 or n2 != 1:
            raise RuntimeError(f"Could not patch neuron count defines in {neural_h}")

        neural_h.write_text(h_text)
        print("Updated", neural_h)

    if not apply_normalization_patch and not update_network_header:
        print("Dry run only. Set APPLY_NORMALIZATION_PATCH and/or UPDATE_NETWORK_HEADER to True.")

    return {"neural_c": neural_c, "neural_h": neural_h}


def resolve_tcl_for_current_repo(
    repo: Path,
    src_tcl: Path,
    impl_tmp: Path,
    hls_output_abs: Path | None = None,
) -> Path:
    """Use repo script as-is when path matches ~/physical-cartpole, otherwise make a patched copy."""
    expected_repo = (Path.home() / "physical-cartpole").resolve()
    if repo.resolve() == expected_repo:
        print("Using original TCL:", src_tcl)
        return src_tcl

    text = src_tcl.read_text()
    repo_str = str(repo)
    text = text.replace("$::env(HOME)/physical-cartpole", repo_str)
    text = text.replace("~/physical-cartpole", repo_str)

    if src_tcl.name == "generate_vitis_project.tcl":
        xsa_candidates = [
            repo / "FPGA" / "VivadoProjects" / "CartpoleDriverZynq" / "cartpole_driver_design_wrapper.xsa",
            repo / "Firmware" / "VitisProjects" / "cartpole_hw" / "hw" / "cartpole_driver_design_wrapper.xsa",
            repo
            / "Firmware"
            / "VitisProjects"
            / "cartpole_hw"
            / "export"
            / "cartpole_hw"
            / "hw"
            / "cartpole_driver_design_wrapper.xsa",
        ]
        xsa_candidates.extend(
            sorted(
                (repo / "Firmware" / "VitisProjects").glob("**/cartpole_driver_design_wrapper.xsa"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
        )
        selected_xsa = next((p for p in xsa_candidates if p.exists()), xsa_candidates[0])

        bit_candidates = [
            repo
            / "FPGA"
            / "VivadoProjects"
            / "CartpoleDriverZynq"
            / "CartpoleDriverZynq.runs"
            / "impl_1"
            / "cartpole_driver_design_wrapper.bit",
            repo / "Firmware" / "VitisProjects" / "cartpole_hw" / "hw" / "cartpole_driver_design_wrapper.bit",
            repo
            / "Firmware"
            / "VitisProjects"
            / "cartpole_fsbl"
            / "_ide"
            / "bitstream"
            / "cartpole_driver_design_wrapper.bit",
            repo
            / "Firmware"
            / "VitisProjects"
            / "CartPoleFirmware"
            / "_ide"
            / "bitstream"
            / "cartpole_driver_design_wrapper.bit",
        ]
        bit_candidates.extend(
            sorted(
                (repo / "Firmware" / "VitisProjects").glob("**/cartpole_driver_design_wrapper.bit"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
        )
        selected_bit = next((p for p in bit_candidates if p.exists()), bit_candidates[0])

        workspace_root = repo / "Firmware" / "VitisProjects"
        stable_inputs = impl_tmp / "inputs"
        stable_inputs.mkdir(parents=True, exist_ok=True)

        if selected_xsa.exists() and workspace_root in selected_xsa.parents:
            copied_xsa = stable_inputs / "cartpole_driver_design_wrapper.xsa"
            shutil.copy2(selected_xsa, copied_xsa)
            selected_xsa = copied_xsa

        if selected_bit.exists() and workspace_root in selected_bit.parents:
            copied_bit = stable_inputs / "cartpole_driver_design_wrapper.bit"
            shutil.copy2(selected_bit, copied_bit)
            selected_bit = copied_bit

        text, n_hw = re.subn(r'set hw_xsa\s+"[^"]+"', f'set hw_xsa  "{selected_xsa}"', text, count=1)
        if n_hw != 1:
            raise RuntimeError("Could not patch 'set hw_xsa' in generate_vitis_project.tcl")

        text, n_bit = re.subn(
            r'set raw_bit_path\s+\[file join[\s\S]*?cartpole_driver_design_wrapper\.bit\]|set raw_bit_path\s+"[^"]+"',
            f'set raw_bit_path "{selected_bit}"',
            text,
            count=1,
        )
        if n_bit != 1:
            raise RuntimeError("Could not patch 'set raw_bit_path' in generate_vitis_project.tcl")

        print("Resolved Step 6.5 hw_xsa path:", selected_xsa, "exists=", selected_xsa.exists())
        print("Resolved Step 6.5 raw_bit_path:", selected_bit, "exists=", selected_bit.exists())

    if src_tcl.name == "generate_bitstream.tcl":
        project_tcl_src = repo / "FPGA" / "VivadoProjects" / "CartpoleDriverZynq_new.tcl"
        hls_output_dir = _resolve_hls4ml_output_dir(repo, hls_output_abs=hls_output_abs)
        if project_tcl_src.exists() and hls_output_dir is not None:
            hls_rel = f"HLS4ML/{hls_output_dir.name}"
            project_text = project_tcl_src.read_text()
            project_text, n_sub = re.subn(r"HLS4ML/[^/]+(?=/myproject_prj)", hls_rel, project_text)
            if n_sub > 0:
                project_tcl_out = impl_tmp / "CartpoleDriverZynq_new.notebook.tcl"
                project_tcl_out.write_text(project_text)
                text = text.replace(str(project_tcl_src), str(project_tcl_out))
                text = text.replace(
                    "$::env(HOME)/physical-cartpole/FPGA/VivadoProjects/CartpoleDriverZynq_new.tcl",
                    str(project_tcl_out),
                )
                text = text.replace(
                    "~/physical-cartpole/FPGA/VivadoProjects/CartpoleDriverZynq_new.tcl",
                    str(project_tcl_out),
                )
                print("Patched HLS4ML paths in:", project_tcl_out)
            else:
                print("No HLS4ML path substitutions were needed in:", project_tcl_src)
        else:
            print("Warning: Could not resolve HLS4ML output directory for TCL patching.")

    out_tcl = impl_tmp / f"{src_tcl.stem}.notebook.tcl"
    out_tcl.write_text(text)
    print("Using notebook-local TCL copy:", out_tcl)
    return out_tcl


def run_step64_bitstream(
    repo: Path,
    impl_vivado_exe: Path,
    hls_output_abs: Path | None = None,
) -> dict[str, Any]:
    impl_tmp = repo / ".notebook_impl"
    impl_tmp.mkdir(exist_ok=True)

    set_automation_scripts_executable(repo)

    bitstream_tcl = resolve_tcl_for_current_repo(
        repo=repo,
        src_tcl=repo / "generate_bitstream.tcl",
        impl_tmp=impl_tmp,
        hls_output_abs=hls_output_abs,
    )
    vivado_projects_dir = repo / "FPGA" / "VivadoProjects"

    project_dir = vivado_projects_dir / "CartpoleDriverZynq"
    if project_dir.exists():
        shutil.rmtree(project_dir)
        print("Removed stale Vivado project directory:", project_dir)

    _run_cmd_live(["bash", repo / "install_zybo_board.sh"], cwd=repo)

    vivado_cmd = [str(impl_vivado_exe), "-mode", "batch", "-source", bitstream_tcl]
    try:
        _run_cmd_live(vivado_cmd, cwd=vivado_projects_dir)
    except subprocess.CalledProcessError:
        env = os.environ.copy()
        env["MALLOC_CHECK_"] = "0"
        env["MALLOC_ARENA_MAX"] = "2"
        jemalloc = Path("/usr/lib/x86_64-linux-gnu/libjemalloc.so.2")
        if jemalloc.exists():
            env["LD_PRELOAD"] = str(jemalloc)
        print("First Vivado run failed. Retrying with MALLOC/LD_PRELOAD settings...")
        if project_dir.exists():
            shutil.rmtree(project_dir)
            print("Removed partially created Vivado project directory before retry:", project_dir)
        _run_cmd_live(vivado_cmd, cwd=vivado_projects_dir, env=env)

    xsa = repo / "FPGA" / "VivadoProjects" / "CartpoleDriverZynq" / "cartpole_driver_design_wrapper.xsa"
    print("XSA exists:", xsa.exists(), xsa)
    return {
        "xsa": xsa,
        "bitstream_tcl": bitstream_tcl,
        "impl_tmp": impl_tmp,
        "vivado_exe": Path(impl_vivado_exe),
    }


def _extract_tcl_path(tcl_text: str, var_name: str) -> Path | None:
    m = re.search(rf'(?m)^\s*set\s+{re.escape(var_name)}\s+"([^"]+)"', tcl_text)
    return Path(m.group(1)) if m else None


def _tail_file(path: Path, n_lines: int = 80) -> list[str]:
    if not path.exists():
        return [f"<missing: {path}>"]
    try:
        lines = path.read_text(errors="ignore").splitlines()
    except Exception as exc:
        return [f"<could not read {path}: {exc}>"]
    if not lines:
        return [f"<empty: {path}>"]
    return lines[-n_lines:]


def _log_contains(path: Path, markers: list[str]) -> bool:
    if not path.exists():
        return False
    text = path.read_text(errors="ignore")
    return any(marker in text for marker in markers)


def _find_existing_step65_xsct_pids(vitis_tcl: Path) -> list[str]:
    try:
        ps = subprocess.run(
            ["ps", "-eo", "pid=,args="],
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return []

    matches: list[str] = []
    target = str(vitis_tcl)
    for row in ps.stdout.splitlines():
        row = row.strip()
        if not row:
            continue
        parts = row.split(None, 1)
        if len(parts) != 2:
            continue
        pid, args = parts
        if "xsct" in args and target in args:
            matches.append(pid)
    return matches


def _terminate_proc(proc: subprocess.Popen[Any]) -> None:
    if proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=15)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=15)


def _run_xsct(
    cmd: list[str],
    repo: Path,
    vitis_log: Path,
    idle_timeout_sec: int,
    hard_timeout_sec: int,
    display_crash_markers: list[str],
    meta_log: Path,
    ide_log: Path,
    mode: str = "w",
    env: dict[str, str] | None = None,
) -> None:
    with vitis_log.open(mode) as logf:
        if mode == "a":
            logf.write("\n\n=== Retrying Step 6.5 with xvfb-run fallback ===\n")
        proc = subprocess.Popen(
            cmd,
            cwd=str(repo),
            env=env,
            stdout=logf,
            stderr=subprocess.STDOUT,
        )

        start_ts = time.time()
        last_progress_ts = start_ts
        last_size = vitis_log.stat().st_size if vitis_log.exists() else 0

        while True:
            rc = proc.poll()
            cur_size = vitis_log.stat().st_size if vitis_log.exists() else 0
            if cur_size != last_size:
                last_size = cur_size
                last_progress_ts = time.time()

            if rc is not None:
                if rc != 0:
                    raise subprocess.CalledProcessError(rc, cmd)
                return

            now = time.time()
            if now - start_ts > hard_timeout_sec:
                _terminate_proc(proc)
                raise TimeoutError(f"Step 6.5 xsct exceeded hard timeout ({hard_timeout_sec}s).")

            if now - last_progress_ts > idle_timeout_sec:
                marker_hit = (
                    _log_contains(vitis_log, display_crash_markers)
                    or _log_contains(meta_log, display_crash_markers)
                    or _log_contains(ide_log, display_crash_markers)
                )
                if marker_hit:
                    _terminate_proc(proc)
                    raise RuntimeError(
                        "Step 6.5 appears stuck after display/channel crash markers "
                        f"with no new log output for {idle_timeout_sec}s."
                    )

            time.sleep(2)


def run_step65_bootbin(
    repo: Path,
    vitis_tcl_src: Path,
    hls_output_abs: Path | None = None,
) -> dict[str, Any]:
    impl_tmp = repo / ".notebook_impl"
    impl_tmp.mkdir(exist_ok=True)

    vitis_tcl = resolve_tcl_for_current_repo(
        repo=repo,
        src_tcl=vitis_tcl_src,
        impl_tmp=impl_tmp,
        hls_output_abs=hls_output_abs,
    )
    if vitis_tcl is None:
        raise RuntimeError("_resolve_tcl_for_current_repo returned None for generate_vitis_project.tcl")
    vitis_tcl = Path(vitis_tcl)
    if not vitis_tcl.exists():
        raise FileNotFoundError(f"Resolved vitis_tcl does not exist: {vitis_tcl}")

    tcl_text = vitis_tcl.read_text(errors="ignore")
    hw_xsa_path = _extract_tcl_path(tcl_text, "hw_xsa")
    bit_path = _extract_tcl_path(tcl_text, "raw_bit_path")
    print("Step 6.5 hw_xsa path:", hw_xsa_path)
    print("Step 6.5 bitstream path:", bit_path)

    if hw_xsa_path is None:
        raise RuntimeError(f"Could not parse 'set hw_xsa' from {vitis_tcl}")
    if not hw_xsa_path.exists():
        raise FileNotFoundError(
            f"Step 6.5 cannot start: missing XSA file: {hw_xsa_path}. "
            "Run Step 6.4 or provide a valid fallback path in the TCL patching helper."
        )

    if bit_path is None:
        raise RuntimeError(f"Could not parse 'set raw_bit_path' from {vitis_tcl}")
    if not bit_path.exists():
        raise FileNotFoundError(
            f"Step 6.5 cannot finish BOOT.bin packaging: missing bitstream file: {bit_path}. "
            "Run Step 6.4 or provide a valid fallback path in the TCL patching helper."
        )

    preferred_xsct = "/tools/Xilinx/Vitis/2020.1/bin/xsct"
    xsct_exe = preferred_xsct if os.path.exists(preferred_xsct) else shutil.which("xsct")
    if not xsct_exe:
        raise RuntimeError("xsct not found in PATH (and /tools/Xilinx/Vitis/2020.1/bin/xsct is missing).")

    xvfb_run = shutil.which("xvfb-run")
    if not xvfb_run:
        print("Warning: xvfb-run not found. If headless GTK errors occur, install xvfb/xvfb-run.")

    step65_env = os.environ.copy()
    step65_env.setdefault("SWT_GTK3", "0")
    step65_env.setdefault("GDK_BACKEND", "x11")
    step65_env.setdefault("LIBGL_ALWAYS_INDIRECT", "1")

    idle_timeout_sec = int(os.environ.get("STEP65_IDLE_TIMEOUT_SEC", "600"))
    hard_timeout_sec = int(os.environ.get("STEP65_HARD_TIMEOUT_SEC", "2700"))

    vitis_log = repo / "vitis_output.log"
    workspace_dir = repo / "Firmware" / "VitisProjects"
    meta_log = workspace_dir / ".metadata" / ".log"
    ide_log = workspace_dir / "IDE.log"

    display_crash_markers = [
        "gtk_init_check() failed",
        "No more handles",
        "Channel closed",
        "tcfchan#0",
        "xsct server communication channel has closed unexpectedly",
    ]

    existing_pids = _find_existing_step65_xsct_pids(vitis_tcl)
    if existing_pids:
        pids = " ".join(existing_pids)
        raise RuntimeError(
            "Step 6.5 cannot start because an existing xsct process is still using this TCL "
            f"(pid(s): {', '.join(existing_pids)}). Stop those processes first, for example: kill {pids}"
        )

    run_error: Exception | None = None

    prefer_xvfb = (not os.environ.get("DISPLAY")) and bool(xvfb_run)
    if prefer_xvfb:
        print("No DISPLAY detected; running Step 6.5 under xvfb-run.")

    primary_cmd = [str(xsct_exe), "-nodisp", str(vitis_tcl)]
    if prefer_xvfb:
        primary_cmd = [xvfb_run, "-a", *primary_cmd]

    print("$", " ".join(primary_cmd))
    try:
        _run_xsct(
            primary_cmd,
            repo=repo,
            vitis_log=vitis_log,
            idle_timeout_sec=idle_timeout_sec,
            hard_timeout_sec=hard_timeout_sec,
            display_crash_markers=display_crash_markers,
            meta_log=meta_log,
            ide_log=ide_log,
            mode="w",
            env=step65_env,
        )
    except Exception as exc:
        run_error = exc
        if not xvfb_run:
            print("Primary xsct run failed, and xvfb-run is not available for fallback.")
        elif prefer_xvfb:
            print("Primary xvfb-run xsct invocation failed.")
        else:
            retry_cmd = [xvfb_run, "-a", str(xsct_exe), "-nodisp", str(vitis_tcl)]
            print("Primary xsct run failed. Retrying once with xvfb-run...")
            print("$", " ".join(retry_cmd))
            try:
                _run_xsct(
                    retry_cmd,
                    repo=repo,
                    vitis_log=vitis_log,
                    idle_timeout_sec=idle_timeout_sec,
                    hard_timeout_sec=hard_timeout_sec,
                    display_crash_markers=display_crash_markers,
                    meta_log=meta_log,
                    ide_log=ide_log,
                    mode="a",
                    env=step65_env,
                )
                run_error = None
                print("xvfb-run fallback succeeded.")
            except Exception as retry_exc:
                run_error = retry_exc
                print("xvfb-run fallback failed.")

    if run_error is not None:
        print("\nLast 80 lines from vitis_output.log:")
        for line in _tail_file(vitis_log, 80):
            print(line)

        print("\nLast 80 lines from Firmware/VitisProjects/.metadata/.log:")
        for line in _tail_file(meta_log, 80):
            print(line)

        if ide_log.exists():
            print("\nLast 80 lines from Firmware/VitisProjects/IDE.log:")
            for line in _tail_file(ide_log, 80):
                print(line)

        raise run_error

    boot_bins = sorted((repo / "Firmware" / "VitisProjects").glob("**/BOOT.bin"))
    if not boot_bins:
        raise RuntimeError("Step 6.5 completed, but no BOOT.bin was found under Firmware/VitisProjects.")

    print("Generated BOOT.bin files:")
    for p in boot_bins:
        print(" -", p)

    return {"boot_bins": boot_bins, "vitis_tcl": vitis_tcl}
