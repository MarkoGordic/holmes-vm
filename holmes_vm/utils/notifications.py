#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows toast notification support for Holmes VM Setup.
Falls back gracefully on non-Windows or when notification libraries are unavailable.
"""

import sys
import subprocess
import os


def _notify_powershell(title: str, message: str, app_id: str = 'Holmes VM Setup') -> bool:
    """Show a Windows toast notification using PowerShell and WinRT."""
    if sys.platform != 'win32':
        return False

    # Use BurntToast module if available, otherwise fall back to raw .NET
    ps_code = f"""
$ErrorActionPreference = 'SilentlyContinue'
# Try BurntToast first (richer notifications)
if (Get-Module -ListAvailable -Name BurntToast -ErrorAction SilentlyContinue) {{
    Import-Module BurntToast -ErrorAction SilentlyContinue
    New-BurntToastNotification -Text '{title}', '{message}' -AppLogo $null -ErrorAction SilentlyContinue
    exit 0
}}
# Fallback: raw Windows.UI.Notifications via .NET
try {{
    [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
    [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom, ContentType = WindowsRuntime] | Out-Null
    $template = @"
<toast>
  <visual>
    <binding template="ToastGeneric">
      <text>{title}</text>
      <text>{message}</text>
    </binding>
  </visual>
</toast>
"@
    $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
    $xml.LoadXml($template)
    $toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
    $notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('{app_id}')
    $notifier.Show($toast)
}} catch {{
    # Last resort: simple balloon notification via WPF
    try {{
        Add-Type -AssemblyName System.Windows.Forms -ErrorAction Stop
        $notify = New-Object System.Windows.Forms.NotifyIcon
        $notify.Icon = [System.Drawing.SystemIcons]::Information
        $notify.BalloonTipTitle = '{title}'
        $notify.BalloonTipText = '{message}'
        $notify.Visible = $true
        $notify.ShowBalloonTip(5000)
        Start-Sleep -Milliseconds 5500
        $notify.Dispose()
    }} catch {{ }}
}}
"""
    try:
        subprocess.Popen(
            ['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', ps_code],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0)
        )
        return True
    except Exception:
        return False


def show_notification(title: str, message: str) -> bool:
    """Show a native OS notification. Returns True if notification was dispatched."""
    if sys.platform == 'win32':
        return _notify_powershell(title, message)
    elif sys.platform == 'darwin':
        try:
            subprocess.Popen([
                'osascript', '-e',
                f'display notification "{message}" with title "{title}"'
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception:
            return False
    else:
        # Linux: try notify-send
        try:
            subprocess.Popen(
                ['notify-send', title, message],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            return True
        except Exception:
            return False
