# herdr-app-tab

A [Herdr](https://herdr.dev) plugin that automatically launches an application in a fresh, idle single-pane tab when the tab is created or renamed to a configured `tabname`.

## Installation

```sh
herdr plugin install hvkiefer/herdr-plugin-app-tab
```

Or link a local checkout:

```sh
herdr plugin link /path/to/herdr-plugin-app-tab --enabled
```

Requires `python3` (3.11+) on `PATH` and Herdr 0.9.0+.

## Configuration

Add tab rules to Herdr's `~/.config/herdr/config.toml`:

```toml
[[plugins.herdr-app-tab.tabs]]
tabname = "git"
cmd = "lazygit"

[[plugins.herdr-app-tab.tabs]]
tabname = "nvim"
cmd = "nvim"
```

If the `config.toml` entry is missing or empty, the plugin falls back to `config.toml` (or `config.json`) in the plugin config directory (`herdr plugin config-dir hvkiefer.herdr-app-tab`):

```toml
[[tabs]]
tabname = "git"
cmd = "lazygit"

[[tabs]]
tabname = "nvim"
cmd = "nvim"
```

```json
[
  { "tabname": "git", "cmd": "lazygit" },
  { "tabname": "nvim", "cmd": "nvim" }
]
```

Tab names are matched case-insensitively. Commands only run when the tab has a single pane at an idle shell prompt with no active foreground process or agent.

## License

MIT
