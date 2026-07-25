from __future__ import annotations

from typing import Any

FIELD_INVENTORY: dict[str, tuple[str, ...]] = {
    "windows": (
        "wallpaper", "AccentPalette", "StartTaskbarColorPrevalence", "TitleBarColorPrevalence",
        "AccentColorMenu", "StartColorMenu", "AccentColor", "ColorizationColor", "ColorizationAfterglow",
        "AppsUseLightTheme", "SystemUsesLightTheme", "AutoColorization", "highContrast",
    ),
    "terminal": (
        "background", "foreground", "selectionBackground", "selectionForeground", "cursorColor",
        "black", "red", "green", "yellow", "blue", "purple", "cyan", "white", "brightBlack", "brightRed",
        "brightGreen", "brightYellow", "brightBlue", "brightPurple", "brightCyan", "brightWhite",
        "profile.colorScheme", "profile.tabColor", "theme.applicationTheme", "window.frame", "window.unfocusedFrame",
        "tabRow.background", "tabRow.unfocusedBackground", "tab.background", "tab.unfocusedBackground",
    ),
    "vscode": (
        "foreground", "disabledForeground", "descriptionForeground", "icon.foreground", "editor.background", "editor.foreground",
        "editor.selectionBackground", "editor.selectionForeground", "editorLineNumber.foreground", "editorLineNumber.activeForeground",
        "editorCursor.foreground", "editorMultiCursor.primary.foreground", "editorMultiCursor.secondary.foreground",
        "editor.placeholder.foreground", "editor.findMatchBackground", "editor.findMatchForeground", "editorError.foreground",
        "editorWarning.foreground", "editorInfo.foreground", "editorHint.foreground", "editorGroupHeader.tabsBackground",
        "editorGroupHeader.tabsBorder", "sideBar.background", "sideBar.foreground", "sideBar.border", "sideBarTitle.background",
        "sideBarTitle.foreground", "sideBarTitle.border", "sideBarSectionHeader.background", "sideBarSectionHeader.foreground",
        "sideBarSectionHeader.border", "activityBar.background", "activityBar.foreground", "activityBar.inactiveForeground",
        "activityBar.activeBorder", "activityBar.border", "activityBarBadge.background", "activityBarBadge.foreground",
        "activityBarTop.background", "activityBarTop.foreground", "activityBarTop.inactiveForeground", "activityBarTop.activeBorder",
        "titleBar.activeBackground", "titleBar.activeForeground", "titleBar.inactiveBackground", "titleBar.inactiveForeground",
        "titleBar.border", "tab.activeBackground", "tab.activeForeground", "tab.inactiveBackground", "tab.inactiveForeground",
        "tab.activeBorderTop", "panel.background", "panel.foreground", "panel.border", "panelTitle.activeBorder",
        "panelTitle.activeForeground", "panelTitle.inactiveForeground", "statusBar.background", "statusBar.foreground", "statusBar.border",
        "input.background", "input.foreground", "input.border", "input.placeholderForeground", "dropdown.background", "dropdown.foreground",
        "list.activeSelectionBackground", "list.activeSelectionForeground", "list.inactiveSelectionForeground", "list.focusForeground",
        "list.highlightForeground", "list.focusHighlightForeground", "list.hoverBackground", "badge.background", "badge.foreground",
        "terminal.background", "terminal.foreground", "terminalCursor.foreground", "terminal.ansiBlack", "terminal.ansiRed",
        "terminal.ansiGreen", "terminal.ansiYellow", "terminal.ansiBlue", "terminal.ansiMagenta", "terminal.ansiCyan", "terminal.ansiWhite",
        "terminal.ansiBrightBlack", "terminal.ansiBrightRed", "terminal.ansiBrightGreen", "terminal.ansiBrightYellow", "terminal.ansiBrightBlue",
        "terminal.ansiBrightMagenta", "terminal.ansiBrightCyan", "terminal.ansiBrightWhite", "textLink.foreground", "textLink.activeForeground",
        "errorForeground", "notifications.foreground", "notificationCenterHeader.foreground", "focusBorder", "button.background", "button.foreground",
        "editorWidget.background", "editorWidget.border", "settings.headerForeground", "settings.modifiedItemIndicator", "breadcrumb.background",
        "breadcrumb.foreground", "breadcrumb.focusForeground",
    ),
    "trae": (),
    "codex": (
        "appearanceLightChromeTheme.surface", "appearanceLightChromeTheme.ink", "appearanceLightChromeTheme.accent",
        "appearanceLightChromeTheme.contrast", "appearanceLightChromeTheme.semanticColors.diffAdded",
        "appearanceLightChromeTheme.semanticColors.diffRemoved", "appearanceLightChromeTheme.semanticColors.skill",
        "appearanceDarkChromeTheme.surface", "appearanceDarkChromeTheme.ink", "appearanceDarkChromeTheme.accent",
        "appearanceDarkChromeTheme.contrast", "appearanceDarkChromeTheme.semanticColors.diffAdded",
        "appearanceDarkChromeTheme.semanticColors.diffRemoved", "appearanceDarkChromeTheme.semanticColors.skill",
    ),
    "chrome": (
        "frame", "frame_inactive", "toolbar", "toolbar_text", "toolbar_button_icon", "tab_background_text",
        "tab_background_text_inactive", "tab_text", "bookmark_text", "ntp_background", "ntp_header", "ntp_link", "ntp_text",
        "omnibox_background", "omnibox_text", "omnibox_background_tint", "omnibox_background_tab_switcher", "incognito_tab",
        "incognito_background", "button_background", "button_background_hover", "separator", "tints.buttons", "tints.frame", "tints.background_tab", "display_properties.control_style",
        "display_properties.theme_supports_hidpi",
    ),
}

FIELD_INVENTORY["trae"] = FIELD_INVENTORY["vscode"]


_SOURCES = {
    "windows": "https://learn.microsoft.com/en-us/windows/apps/develop/settings/settings-common",
    "terminal": "https://learn.microsoft.com/en-us/windows/terminal/customize-settings/color-schemes",
    "vscode": "https://code.visualstudio.com/api/references/theme-color",
    "trae": "https://code.visualstudio.com/api/references/theme-color",
    "codex": "verified-v1-runtime-schema",
    "chrome": "https://developer.chrome.com/docs/extensions/develop/ui/themes",
}
_BASELINES = {
    "windows": "Windows 10 22H2 / Windows 11 22H2",
    "terminal": "Windows Terminal documented profile schema",
    "vscode": "VS Code theme color reference",
    "trae": "installed public Workbench-compatible schema",
    "codex": "verified v1 color schema",
    "chrome": "Chrome Manifest V3 theme schema",
}
_INVENTORY_VERSION = "2026-07-25.v1"


def _field_label(name: str) -> str:
    return name.rsplit(".", 1)[-1].replace("_", " ").replace("Color", " color").strip().capitalize()


def _field_region(target: str, name: str) -> str:
    lowered = name.casefold()
    if target == "windows":
        return "taskbar" if "taskbar" in lowered or "start" in lowered else "windows shell"
    if target == "terminal":
        return "terminal tabs" if "tab" in lowered else "terminal"
    if target in {"vscode", "trae"}:
        return "editor" if lowered.startswith("editor") or lowered.startswith("terminal") else "workbench"
    if target == "chrome":
        return "browser chrome"
    if target == "codex":
        return "codex"
    return target


def _field_role(name: str) -> str:
    lowered = name.casefold()
    for token, role in (
        ("background", "surface"),
        ("foreground", "foreground"),
        ("border", "border"),
        ("cursor", "accent_text"),
        ("selection", "selection"),
        ("accent", "accent"),
        ("link", "accent_text"),
        ("error", "error_text"),
        ("warning", "warning_text"),
    ):
        if token in lowered:
            return role
    return "surface"


def field_inventory_for(target: str) -> tuple[dict[str, str], ...]:
    """Return the evidence-backed, user-readable Field inventory for a Target."""
    return tuple(
        {
            "technical_field": name,
            "label": _field_label(name),
            "field_category": "display_property" if "display" in name or "Prevalence" in name else "color",
            "visual_role": _field_role(name),
            "visual_region": _field_region(target, name),
            "mode_support": "light,dark",
            "official_source": _SOURCES.get(target, "unknown"),
            "version_baseline": _BASELINES.get(target, "verified runtime schema"),
            "inventory_version": _INVENTORY_VERSION,
            "capability_status": "supported",
        }
        for name in inventory_for(target)
    )


def inventory_report(
    target: str,
    statuses: dict[str, str] | None = None,
    generated_values: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], ...]:
    statuses = statuses or {}
    generated_values = generated_values or {}
    return tuple(
        {
            **entry,
            "capability_status": statuses.get(entry["technical_field"], entry["capability_status"]),
            "generated_value": generated_values.get(entry["technical_field"]),
            "verification_evidence": entry["official_source"],
        }
        for entry in field_inventory_for(target)
    )


def inventory_groups(target: str, statuses: dict[str, str] | None = None) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for entry in inventory_report(target, statuses):
        groups.setdefault(entry["visual_region"], []).append(entry)
    return groups


def inventory_for(target: str) -> tuple[str, ...]:
    return FIELD_INVENTORY.get(target, ())


def expected_capabilities(targets: tuple[str, ...]) -> dict[str, dict[str, str]]:
    windows_read_only = {"AppsUseLightTheme", "SystemUsesLightTheme", "AutoColorization", "highContrast"}
    return {
        target: {
            field: "unsupported" if target == "windows" and field in windows_read_only else "supported"
            for field in inventory_for(target)
        }
        for target in targets
    }
