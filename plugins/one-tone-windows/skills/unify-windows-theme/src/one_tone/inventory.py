from __future__ import annotations

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
