from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Callable, Mapping

from ..palette import contrast_ratio, parse_hex_color
from ..plan import Plan
from ..storage import atomic_write_text
from .base import AdapterResult, field_capabilities

_SCHEME_NAME = "One Tone"
_THEME_NAME = "One Tone"
_SCHEME_MAPPING = {"light": f"{_SCHEME_NAME} Light", "dark": f"{_SCHEME_NAME} Dark"}
_PSREADLINE_FIELDS = ("InlinePrediction", "ListPrediction", "ListPredictionSelected")
_PROFILE_START = "# >>> one-tone windows-terminal prediction colors >>>"
_PROFILE_END = "# <<< one-tone windows-terminal prediction colors <<<"


def _powershell_probe() -> str:
    return """
$ErrorActionPreference = 'Stop'
Import-Module PSReadLine -ErrorAction SilentlyContinue
$module = Get-Module PSReadLine
$fields = @()
$options = Get-PSReadLineOption -ErrorAction SilentlyContinue
if ($null -ne $options) {
  $fields = @($options | Get-Member -MemberType Property | Select-Object -ExpandProperty Name | Where-Object { $_ -in @('InlinePredictionColor','ListPredictionColor','ListPredictionSelectedColor') } | ForEach-Object { $_ -replace 'Color$','' })
}
[ordered]@{
  profile = [string]$PROFILE.CurrentUserAllHosts
  version = if ($null -ne $module) { [string]$module.Version } else { '' }
  fields = $fields
} | ConvertTo-Json -Compress
"""


def _powershell_candidates() -> list[Path]:
    configured = os.environ.get("ONE_TONE_POWERSHELL_EXECUTABLE")
    if configured:
        return [Path(configured)]
    candidates: list[Path] = []
    for command in ("pwsh", "powershell"):
        resolved = shutil.which(command)
        if resolved and Path(resolved) not in candidates:
            candidates.append(Path(resolved))
    return candidates


def _ansi_expression(color: str, background: bool = False) -> str:
    red, green, blue = parse_hex_color(color)
    channel = 48 if background else 38
    return f"[char]27 + '[{channel};2;{red};{green};{blue}m'"


def _checked_text_color(palette: Mapping[str, str], role: str, background: str) -> str:
    try:
        color = palette[role]
    except KeyError as error:
        raise ValueError(f"{role} is unavailable in the Plan Palette") from error
    if contrast_ratio(color, background) < 4.5:
        raise ValueError(f"{role} does not meet the required contrast against the Terminal surface")
    return color


def _prediction_profile_block(plan: Plan) -> str:
    light = plan.palette_for("light")
    dark = plan.palette_for("dark")
    light_prediction = _checked_text_color(light, "prediction_foreground", light["surface"])
    dark_prediction = _checked_text_color(dark, "prediction_foreground", dark["surface"])
    lines = [
        _PROFILE_START,
        "if ($env:WT_SESSION) {",
        "  $oneToneLightMode = $false",
        "  try {",
        "    $oneToneLightMode = ((Get-ItemProperty -Path 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize' -Name AppsUseLightTheme -ErrorAction Stop).AppsUseLightTheme -eq 1)",
        "  } catch { }",
        f"  $oneToneInlinePrediction = if ($oneToneLightMode) {{ {_ansi_expression(light_prediction)} }} else {{ {_ansi_expression(dark_prediction)} }}",
        f"  $oneToneListPrediction = if ($oneToneLightMode) {{ {_ansi_expression(light_prediction)} }} else {{ {_ansi_expression(dark_prediction)} }}",
        f"  $oneToneListPredictionSelected = if ($oneToneLightMode) {{ {_ansi_expression(light['selection_foreground'])} + {_ansi_expression(light['selection_background'], True)} }} else {{ {_ansi_expression(dark['selection_foreground'])} + {_ansi_expression(dark['selection_background'], True)} }}",
        "  Set-PSReadLineOption -Colors @{",
        "    InlinePrediction = $oneToneInlinePrediction",
        "    ListPrediction = $oneToneListPrediction",
        "    ListPredictionSelected = $oneToneListPredictionSelected",
        "  }",
        "}",
        _PROFILE_END,
    ]
    return "\n".join(lines)


def _replace_profile_block(content: str, block: str) -> str:
    start = content.find(_PROFILE_START)
    end = content.find(_PROFILE_END)
    if (start < 0) != (end < 0) or end >= 0 and end < start:
        raise ValueError("PowerShell Profile contains an incomplete One Tone block")
    if start >= 0:
        end += len(_PROFILE_END)
        return content[:start] + block + content[end:]
    separator = "" if not content or content.endswith(("\n", "\r")) else "\n"
    return content + separator + block + "\n"


def _remove_profile_block(content: str) -> str:
    start = content.find(_PROFILE_START)
    end = content.find(_PROFILE_END)
    if start < 0 or end < start:
        raise ValueError("PowerShell Profile does not contain a complete One Tone block")
    return content[:start] + content[end + len(_PROFILE_END):]


def _restore_managed_profile_block(current: str, original: str) -> str:
    original_start = original.find(_PROFILE_START)
    original_end = original.find(_PROFILE_END)
    if original_start >= 0 and original_end >= original_start:
        original_block = original[original_start:original_end + len(_PROFILE_END)]
        return _replace_profile_block(current, original_block)
    if _PROFILE_START not in current and _PROFILE_END not in current:
        return current
    return _remove_profile_block(current)


def _managed_profile_matches(content: str, original: str) -> bool:
    original_start = original.find(_PROFILE_START)
    original_end = original.find(_PROFILE_END)
    if original_start >= 0 and original_end >= original_start:
        expected = original[original_start:original_end + len(_PROFILE_END)]
        return expected in content
    return _PROFILE_START not in content and _PROFILE_END not in content


def resolve_default_profile(settings: dict[str, Any]) -> tuple[int, str] | None:
    profiles = settings.get("profiles", {})
    profile_list = profiles.get("list", [])
    if not isinstance(profile_list, list):
        return None
    default = profiles.get("default")
    if default is not None:
        for index, profile in enumerate(profile_list):
            if str(profile.get("guid")) == str(default) or profile.get("name") == default:
                return index, "profiles.default resolved by GUID/name"
        return None
    default = settings.get("defaultProfile")
    if default is not None:
        for index, profile in enumerate(profile_list):
            if str(profile.get("guid")) == str(default) or profile.get("name") == default:
                return index, "defaultProfile resolved by GUID/name"
    for index, profile in enumerate(profile_list):
        if not profile.get("source"):
            return index, "profiles.default is null; first local profile selected"
    return None


def _palette_colors(plan: Plan, mode: str | None = None) -> dict[str, str]:
    palette = plan.palette_for(mode or plan.mode)
    return {
        "background": palette["surface"],
        "foreground": palette["foreground"],
        "selectionBackground": palette["selection_background"],
        "selectionForeground": palette["selection_foreground"],
        "black": palette["foreground"],
        "red": palette["error_text"],
        "green": palette["success_text"],
        "yellow": palette["warning_text"],
        "blue": palette["accent_text"],
        "purple": palette["accent_text"],
        "cyan": palette["accent_text"],
        "white": palette["foreground"],
        "brightBlack": palette["foreground"],
        "brightRed": palette["error_text"],
        "brightGreen": palette["success_text"],
        "brightYellow": palette["warning_text"],
        "brightBlue": palette["accent_text"],
        "brightPurple": palette["accent_text"],
        "brightCyan": palette["accent_text"],
        "brightWhite": palette["foreground"],
    }


def _scheme_colors(plan: Plan, mode: str | None = None) -> dict[str, str]:
    colors = _palette_colors(plan, mode)
    palette = plan.palette_for(mode or plan.mode)
    name = _SCHEME_NAME if mode is None else f"{_SCHEME_NAME} {mode.title()}"
    return {"name": name, "cursorColor": palette["accent_text"], **colors}


def _theme_colors(plan: Plan, mode: str | None = None) -> dict[str, Any]:
    palette = plan.palette_for(mode or plan.mode)
    name = _THEME_NAME if mode is None else f"{_THEME_NAME} {mode.title()}"
    return {
        "name": name,
        "window": {
            "applicationTheme": "system",
            "frame": palette["accent"],
            "unfocusedFrame": palette["muted_foreground"],
        },
        "tabRow": {
            "background": palette["surface_subtle"],
            "unfocusedBackground": palette["background"],
        },
        "tab": {
            "background": palette["accent"],
            "unfocusedBackground": palette["surface"],
        },
    }


class TerminalAdapter:
    target = "terminal"

    def __init__(
        self,
        settings_path: Path,
        target_instance: Mapping[str, Any] | None = None,
        powershell_executable: Path | None = None,
        command_runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
        discover_shell: bool = False,
    ) -> None:
        self.settings_path = settings_path
        self._profile_index: int | None = None
        self._resolution_message = ""
        self._target_instance = dict(target_instance or {})
        self._powershell_executable = powershell_executable
        self._command_runner = command_runner or subprocess.run
        self._discover_shell_enabled = discover_shell or command_runner is not None or bool(target_instance)
        self._profile_path: Path | None = None
        self._shell_info: dict[str, Any] = {}
        self._shell_discovered = bool(self._target_instance)
        self._load_shell_instance()

    def _load_shell_instance(self) -> None:
        instance = self._target_instance
        if instance.get("powershell_executable"):
            self._powershell_executable = Path(str(instance["powershell_executable"]))
        if instance.get("profile_path"):
            self._profile_path = Path(str(instance["profile_path"]))
        info = instance.get("psreadline")
        if isinstance(info, dict):
            self._shell_info = dict(info)

    def _discover_shell(self) -> None:
        if self._target_instance or self._shell_discovered:
            return
        self._shell_discovered = True
        if not self._discover_shell_enabled:
            self._shell_info = {"status": "not-applicable", "reason": "PSReadLine discovery disabled for this adapter"}
            return
        candidates = [self._powershell_executable] if self._powershell_executable is not None else _powershell_candidates()
        if not candidates:
            self._shell_info = {"status": "not-applicable", "reason": "PowerShell host not found"}
            return
        fallback: dict[str, Any] = {"status": "unsupported", "reason": "PowerShell hosts do not expose PSReadLine prediction fields"}
        supported_candidates: list[tuple[Path, Path, dict[str, Any]]] = []
        for executable in candidates:
            self._powershell_executable = executable
            try:
                completed = self._command_runner(
                    [str(executable), "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", _powershell_probe()],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                payload = json.loads((completed.stdout or "").strip().splitlines()[-1])
                fields = payload.get("fields", [])
                if isinstance(fields, str):
                    fields = [fields]
                fields = sorted({str(field) for field in fields})
                profile_path = Path(str(payload.get("profile", ""))) if payload.get("profile") else None
                fallback = {
                    "status": "supported" if profile_path is not None and set(_PSREADLINE_FIELDS) <= set(fields) else "unsupported",
                    "version": str(payload.get("version", "")),
                    "fields": fields,
                    "reason": "required PSReadLine prediction fields are unavailable" if set(_PSREADLINE_FIELDS) - set(fields) else "",
                }
                if fallback["status"] == "supported":
                    supported_candidates.append((executable, profile_path, fallback))
            except (OSError, ValueError, IndexError, json.JSONDecodeError) as error:
                fallback = {"status": "unsupported", "reason": f"PowerShell capability discovery failed: {error}"}
        profile_paths = {profile for _, profile, _ in supported_candidates}
        if len(profile_paths) > 1:
            self._powershell_executable = None
            self._profile_path = None
            self._shell_info = {
                "status": "unsupported",
                "reason": "PowerShell Profile candidates are ambiguous",
                "candidates": [
                    {"executable": str(executable), "profile_path": str(profile)}
                    for executable, profile, _ in supported_candidates
                ],
            }
            return
        if supported_candidates:
            executable, profile_path, info = supported_candidates[0]
            self._powershell_executable = executable
            self._profile_path = profile_path
            self._shell_info = info
            return
        self._shell_info = fallback

    def target_instance(self) -> dict[str, Any]:
        self._discover_shell()
        instance: dict[str, Any] = {"status": "ok", "settings_path": str(self.settings_path)}
        if self._powershell_executable is not None:
            instance["powershell_executable"] = str(self._powershell_executable)
        if self._profile_path is not None:
            instance["profile_path"] = str(self._profile_path)
        if self._shell_info:
            instance["psreadline"] = dict(self._shell_info)
        return instance

    def _shell_capabilities(self, status: str) -> dict[str, str]:
        return {field: status for field in _PSREADLINE_FIELDS}

    def _metadata(self, status: str = "supported") -> dict[str, Any]:
        capabilities = field_capabilities(self.target, statuses=self._shell_capabilities(status))
        return {
            "field_capabilities": capabilities,
            "target_instance": self.target_instance(),
            "psreadline": dict(self._shell_info),
        }

    def _apply_profile(self, plan: Plan) -> tuple[str, str]:
        status = self._shell_info.get("status", "not-applicable")
        if status != "supported":
            return status, str(self._shell_info.get("reason") or "PSReadLine prediction colors are not supported")
        if self._profile_path is None:
            return "unsupported", "PSReadLine Profile path was not discovered"
        try:
            content = self._read_profile() if self._profile_path.is_file() else ""
            atomic_write_text(
                self._profile_path,
                _replace_profile_block(content, _prediction_profile_block(plan)),
                newline="",
            )
            return "applied", "PSReadLine prediction colors updated for Windows Terminal sessions"
        except ValueError as error:
            self._shell_info.update({"status": "unsupported", "reason": f"PSReadLine Profile update skipped: {error}"})
            return "unsupported", f"PSReadLine prediction colors unavailable: {error}"
        except OSError as error:
            self._shell_info.update({"status": "unsupported", "reason": f"PSReadLine Profile update failed: {error}"})
            return "failed", f"PSReadLine Profile update failed: {error}"

    def _verify_profile(self, plan: Plan) -> tuple[str, bool, str]:
        status = self._shell_info.get("status", "not-applicable")
        if status != "supported":
            return status, True, str(self._shell_info.get("reason") or "PSReadLine prediction colors are not supported")
        if self._profile_path is None:
            return "unsupported", True, "PSReadLine Profile path was not discovered"
        try:
            content = self._read_profile() if self._profile_path.is_file() else ""
            expected = _prediction_profile_block(plan)
            return "verified", content.find(expected) >= 0, "PSReadLine prediction colors verified"
        except ValueError as error:
            self._shell_info.update({"status": "unsupported", "reason": f"PSReadLine Profile verify skipped: {error}"})
            return "unsupported", True, f"PSReadLine prediction colors unavailable: {error}"
        except OSError as error:
            return "failed", False, f"PSReadLine Profile verify failed: {error}"

    def _read_profile(self) -> str:
        with self._profile_path.open("r", encoding="utf-8", newline="") as handle:  # type: ignore[union-attr]
            return handle.read()

    def _read(self) -> dict[str, Any]:
        payload = json.loads(self.settings_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Terminal settings must be a JSON object")
        return payload

    def detect(self) -> AdapterResult:
        if not self.settings_path.is_file():
            return AdapterResult(self.target, "skipped", False, False, f"Terminal settings not found: {self.settings_path}")
        try:
            self._discover_shell()
            settings = self._read()
            resolved = resolve_default_profile(settings)
            if resolved is None:
                return AdapterResult(self.target, "skipped", False, False, "Terminal default Profile could not be resolved")
            self._profile_index, self._resolution_message = resolved
            shell_status = self._shell_info.get("status", "not-applicable")
            status = "partial" if shell_status == "unsupported" else "ok"
            shell_message = self._shell_info.get("reason") or "PSReadLine prediction capability discovered"
            return AdapterResult(
                self.target, status, False, True,
                f"Terminal Profile detected; {self._resolution_message}; {shell_message}",
                status == "partial", metadata=self._metadata(shell_status),
            )
        except (OSError, ValueError, json.JSONDecodeError) as error:
            return AdapterResult(self.target, "failed", False, False, f"Terminal detect failed: {error}")

    def snapshot(self, backup_dir: Path) -> AdapterResult:
        if not self.settings_path.is_file():
            return AdapterResult(self.target, "failed", False, False, "Terminal settings not found")
        try:
            backup_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(self.settings_path, backup_dir / "terminal-settings.json")
            self._discover_shell()
            if self._profile_path is not None:
                profile_state = {"exists": self._profile_path.is_file()}
                atomic_write_text(backup_dir / "powershell-profile-state.json", json.dumps(profile_state))
                if self._profile_path.is_file():
                    shutil.copy2(self._profile_path, backup_dir / "powershell-profile.ps1")
            return AdapterResult(
                self.target, "ok", False, True, "Terminal settings snapshot saved",
                metadata={"target_instance": self.target_instance()},
            )
        except OSError as error:
            return AdapterResult(self.target, "failed", False, False, f"Terminal snapshot failed: {error}")

    def apply(self, plan: Plan) -> AdapterResult:
        try:
            settings = self._read()
            resolved = resolve_default_profile(settings)
            if resolved is None:
                return AdapterResult(self.target, "failed", False, False, "Terminal default Profile could not be resolved")
            self._profile_index, self._resolution_message = resolved
            profile_list = settings["profiles"]["list"]
            profile_color_keys = (*_palette_colors(plan), "cursorColor")
            for profile in profile_list:
                if not isinstance(profile, dict):
                    continue
                for key in profile_color_keys:
                    profile.pop(key, None)
                profile["colorScheme"] = dict(_SCHEME_MAPPING)
                profile["tabColor"] = plan.palette_for(plan.mode)["accent"]
            settings["profiles"].setdefault("defaults", {})["colorScheme"] = dict(_SCHEME_MAPPING)
            schemes = [item for item in settings.get("schemes", []) if item.get("name") != _SCHEME_NAME]
            schemes = [item for item in schemes if not str(item.get("name", "")).startswith(f"{_SCHEME_NAME} ")]
            schemes.extend(_scheme_colors(plan, mode) for mode in ("light", "dark"))
            schemes.append(_scheme_colors(plan))
            settings["schemes"] = schemes
            themes = [item for item in settings.get("themes", []) if isinstance(item, dict) and item.get("name") != _THEME_NAME]
            themes = [item for item in themes if not str(item.get("name", "")).startswith(f"{_THEME_NAME} ")]
            themes.extend(_theme_colors(plan, mode) for mode in ("light", "dark"))
            themes.append(_theme_colors(plan))
            settings["themes"] = themes
            settings["theme"] = _THEME_NAME
            atomic_write_text(
                self.settings_path,
                json.dumps(settings, ensure_ascii=False, indent=2) + "\n",
            )
            self._discover_shell()
            shell_status, shell_message = self._apply_profile(plan)
            overall_status = "partial" if shell_status in {"unsupported", "failed"} else "ok"
            shell_capability = "applied" if shell_status == "applied" else shell_status
            return AdapterResult(
                self.target, overall_status, True, False,
                f"Terminal Profile updated; {self._resolution_message}; {shell_message}",
                overall_status == "partial", metadata=self._metadata(shell_capability),
            )
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
            return AdapterResult(self.target, "failed", False, False, f"Terminal apply failed: {error}")

    def verify(self, plan: Plan) -> AdapterResult:
        try:
            settings = self._read()
            resolved = resolve_default_profile(settings)
            if resolved is None:
                return AdapterResult(self.target, "failed", False, False, "Terminal default Profile could not be resolved")
            index, message = resolved
            expected = _palette_colors(plan)
            profile_list = settings["profiles"]["list"]
            scheme = next((item for item in settings.get("schemes", []) if item.get("name") == _SCHEME_NAME), None)
            scheme_expected = _scheme_colors(plan)
            theme = next((item for item in settings.get("themes", []) if item.get("name") == _THEME_NAME), None)
            paired_schemes = {
                item.get("name"): item
                for item in settings.get("schemes", [])
                if isinstance(item, dict) and item.get("name") in {"One Tone Light", "One Tone Dark"}
            }
            paired_themes = {
                item.get("name"): item
                for item in settings.get("themes", [])
                if isinstance(item, dict) and item.get("name") in {"One Tone Light", "One Tone Dark"}
            }
            verified = (
                all(
                    isinstance(profile, dict)
                    and profile.get("colorScheme") == _SCHEME_MAPPING
                    and not any(key in profile for key in (*expected, "cursorColor"))
                    and profile.get("tabColor") == plan.palette_for(plan.mode)["accent"]
                    for profile in profile_list
                )
                and settings.get("profiles", {}).get("defaults", {}).get("colorScheme") == _SCHEME_MAPPING
                and isinstance(scheme, dict)
                and all(scheme.get(key) == value for key, value in scheme_expected.items())
                and settings.get("theme") == _THEME_NAME
                and theme == _theme_colors(plan)
                and all(paired_schemes.get(f"One Tone {mode.title()}") == _scheme_colors(plan, mode) for mode in ("light", "dark"))
                and all(paired_themes.get(f"One Tone {mode.title()}") == _theme_colors(plan, mode) for mode in ("light", "dark"))
            )
            shell_status, shell_verified, shell_message = self._verify_profile(plan)
            shell_capability = "verified" if shell_status == "verified" and shell_verified else shell_status
            overall_verified = verified and (shell_status in {"not-applicable", "unsupported", "failed"} or shell_verified)
            overall_status = "partial" if shell_status in {"unsupported", "failed"} else "ok"
            if not overall_verified and shell_status not in {"unsupported", "failed"}:
                overall_status = "failed"
            return AdapterResult(
                self.target, overall_status, False, overall_verified,
                f"Terminal Profile verified; {message}; {shell_message}" if overall_verified else "Terminal Profile colors do not match Plan",
                overall_status == "partial", metadata=self._metadata(shell_capability),
            )
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
            return AdapterResult(self.target, "failed", False, False, f"Terminal verify failed: {error}")

    def rollback(self, backup_dir: Path, metadata: Mapping[str, Any] | None = None) -> AdapterResult:
        backup = backup_dir / "terminal-settings.json"
        if not backup.is_file():
            return AdapterResult(self.target, "failed", False, False, "Terminal backup not found")
        try:
            shutil.copy2(backup, self.settings_path)
            profile_state_path = backup_dir / "powershell-profile-state.json"
            if profile_state_path.is_file() and self._profile_path is not None:
                profile_state = json.loads(profile_state_path.read_text(encoding="utf-8"))
                profile_backup = backup_dir / "powershell-profile.ps1"
                if profile_state.get("exists") and profile_backup.is_file():
                    original_profile = profile_backup.read_text(encoding="utf-8", newline="")
                    current_profile = self._read_profile() if self._profile_path.is_file() else ""
                    atomic_write_text(
                        self._profile_path,
                        _restore_managed_profile_block(current_profile, original_profile),
                        newline="",
                    )
                elif not profile_state.get("exists") and self._profile_path.exists():
                    restored_profile = _restore_managed_profile_block(self._read_profile(), "")
                    if restored_profile.strip():
                        atomic_write_text(self._profile_path, restored_profile, newline="")
                    else:
                        self._profile_path.unlink()
            restored = self.settings_path.read_bytes() == backup.read_bytes()
            if profile_state_path.is_file() and self._profile_path is not None:
                profile_state = json.loads(profile_state_path.read_text(encoding="utf-8"))
                if profile_state.get("exists"):
                    original_profile = profile_backup.read_text(encoding="utf-8", newline="") if profile_backup.is_file() else ""
                    restored = restored and self._profile_path.is_file() and _managed_profile_matches(self._read_profile(), original_profile)
                elif self._profile_path.is_file():
                    restored = restored and _PROFILE_START not in self._read_profile() and _PROFILE_END not in self._read_profile()
                else:
                    restored = restored and not self._profile_path.exists()
            return AdapterResult(self.target, "ok" if restored else "failed", True, restored, "Terminal settings restored")
        except (OSError, ValueError, json.JSONDecodeError) as error:
            return AdapterResult(self.target, "failed", False, False, f"Terminal rollback failed: {error}")
