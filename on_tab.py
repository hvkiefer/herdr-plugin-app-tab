"""Launch configured apps when a tab is created or renamed with a matching name."""
import json
import os
from pathlib import Path
import subprocess
import tomllib


def find(obj, key):
    """Return the first value for key anywhere in nested dicts/lists."""
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for v in obj.values():
            r = find(v, key)
            if r is not None:
                return r
    elif isinstance(obj, list):
        for v in obj:
            r = find(v, key)
            if r is not None:
                return r
    return None


def parse_entries(data):
    if isinstance(data, dict):
        entries = data.get("tabs")
        if entries is None:
            entries = data.get("apps")
    elif isinstance(data, list):
        entries = data
    else:
        return None

    if not isinstance(entries, list):
        return None

    rules = {}
    for item in entries:
        if not isinstance(item, dict):
            continue
        tabname = item.get("tabname")
        cmd = item.get("cmd")
        if isinstance(tabname, str) and tabname.strip() and isinstance(cmd, str) and cmd.strip():
            rules[tabname.strip().lower()] = cmd.strip()
    return rules


def extract_herdr_config_entry(data):
    """Extract herdr-app-tab config from main Herdr config.toml."""
    if not isinstance(data, dict):
        return None
    plugins = data.get("plugins")
    if isinstance(plugins, dict):
        for key in (
            "herdr-app-tab",
            "hvkiefer.herdr-app-tab",
            "local.herdr-app-tab",
            "herdr_app_tab",
        ):
            if key in plugins:
                return plugins[key]
    for key in ("herdr-app-tab", "herdr_app_tab"):
        if key in data:
            return data[key]
    return None


def main_config_path():
    env_path = os.environ.get("HERDR_CONFIG_PATH")
    if env_path:
        return Path(env_path)
    config_dir = os.environ.get("HERDR_PLUGIN_CONFIG_DIR")
    if config_dir:
        # .../herdr/plugins/config/<plugin_id> -> .../herdr/config.toml
        candidate = Path(config_dir).resolve().parents[2] / "config.toml"
        if candidate.is_file():
            return candidate
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else (Path.home() / ".config")
    return base / "herdr" / "config.toml"


def load_rules():
    cfg_path = main_config_path()
    if cfg_path.is_file():
        with cfg_path.open("rb") as f:
            main_data = tomllib.load(f)
        entry = extract_herdr_config_entry(main_data)
        rules = parse_entries(entry)
        # Only fall back to plugin config if the config.toml entry is missing or empty.
        if rules:
            return rules

    candidates = []
    config_dir = os.environ.get("HERDR_PLUGIN_CONFIG_DIR")
    if config_dir:
        cdir = Path(config_dir)
        candidates.extend([cdir / "config.toml", cdir / "config.json"])

    plugin_root = Path(os.environ.get("HERDR_PLUGIN_ROOT") or Path(__file__).resolve().parent)
    candidates.extend([plugin_root / "config.toml", plugin_root / "config.json"])

    for path in candidates:
        if not path.is_file():
            continue
        if path.suffix == ".json":
            data = json.loads(path.read_text(encoding="utf-8"))
        else:
            with path.open("rb") as f:
                data = tomllib.load(f)
        rules = parse_entries(data)
        if rules is not None:
            return rules

    return {}


def pane_is_idle_shell(herdr, pane_id):
    proc = subprocess.run(
        [herdr, "pane", "process-info", "--pane", pane_id],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return True
    info = json.loads(proc.stdout).get("result", {}).get("process_info", {})
    shell_pid = info.get("shell_pid")
    fg_pgid = info.get("foreground_process_group_id")
    if shell_pid is not None and fg_pgid is not None:
        return shell_pid == fg_pgid
    return True


def main():
    herdr = os.environ.get("HERDR_BIN_PATH", "herdr")
    event = json.loads(os.environ.get("HERDR_PLUGIN_EVENT_JSON") or "{}")
    label = find(event, "label")
    tab_id = find(event, "tab_id")
    if not isinstance(label, str) or not label.strip() or not tab_id:
        return

    rules = load_rules()
    cmd = rules.get(label.strip().lower())
    if not cmd:
        return

    out = subprocess.run([herdr, "pane", "list"], capture_output=True, text=True, check=True).stdout
    panes = [p for p in json.loads(out)["result"]["panes"] if p.get("tab_id") == tab_id]

    # Only act on a fresh single-pane tab at its idle shell prompt, so we never type into a busy pane.
    if len(panes) != 1 or panes[0].get("agent"):
        return

    pane_id = panes[0]["pane_id"]
    if not pane_is_idle_shell(herdr, pane_id):
        return

    subprocess.run([herdr, "pane", "run", pane_id, cmd], check=True)


if __name__ == "__main__":
    main()
