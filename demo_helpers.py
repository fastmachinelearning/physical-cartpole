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
import time
from pathlib import Path
from typing import Any


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
