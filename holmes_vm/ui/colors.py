#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI Colors and theme constants - Deep London Night (Teal-Blue)
A refined dark theme inspired by the provided image: deep blue backgrounds,
blue-gray text, and teal accents.
"""

# === Core Background & Foreground ===
# Deep blue backgrounds
COLOR_BG = '#0F1F2A'            # Primary background (deep blue)
COLOR_BG_SECONDARY = '#142736'  # Panels
COLOR_BG_TERTIARY = '#183447'   # Inputs/boxes

# Foreground colors (cool neutrals)
COLOR_FG = '#E6EEF3'            # Primary text (cool off-white)
COLOR_FG_BRIGHT = '#F7FAFC'     # Bright text
COLOR_MUTED = '#9BB3C5'         # Secondary text (blue-gray)
COLOR_MUTED_DARK = '#6D8797'    # Tertiary text (darker blue-gray)

# === Accent Colors (Teal/Cyan) ===
COLOR_ACCENT = '#2F9BC1'        # Primary accent (teal)
COLOR_ACCENT_LIGHT = '#5AC2E0'  # Hover state
COLOR_ACCENT_DARK = '#1F6F8F'   # Pressed state

# === Status Colors ===
COLOR_INFO = '#9BB3C5'          # Information messages (blue-gray)
COLOR_SUCCESS = '#66C2A3'       # Success (teal-green)
COLOR_WARN = '#E0B860'          # Warning (muted amber)
COLOR_ERROR = '#E27A7A'         # Error (soft red)

# === Special Theme Colors ===
COLOR_BRONZE = '#2F9BC1'        # Alias to accent in this palette
COLOR_GOLD = '#E0B860'          # Warm highlight contrasting the blues
COLOR_DEERSTALKER = '#1F6F8F'   # Deep teal accent

# === Border & Divider Colors ===
COLOR_BORDER = '#1C3040'        # Default border
COLOR_BORDER_LIGHT = '#274658'  # Lighter border for emphasis
COLOR_DIVIDER = '#1A2E3D'       # Subtle divider

# === Shadow & Overlay ===
COLOR_SHADOW = '#000000'        # Black for shadows
COLOR_OVERLAY = '#0F1F2A'       # Overlay background

# === Progress & Loading ===
COLOR_PROGRESS_BG = '#183447'   # Progress bar background
COLOR_PROGRESS_FG = '#2F9BC1'   # Progress bar fill (teal)

# === Semantic Aliases for Easy Use ===
COLOR_PRIMARY = COLOR_ACCENT
COLOR_SECONDARY = COLOR_BRONZE
COLOR_TEXT = COLOR_FG
COLOR_TEXT_DIM = COLOR_MUTED

