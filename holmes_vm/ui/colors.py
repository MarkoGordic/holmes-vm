#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI Colors and theme constants - Sherlock Holmes Mystery Theme
A sophisticated dark theme inspired by Victorian London fog and gaslight,
with warm browns and cool grays reminiscent of 221B Baker Street.
"""

# === Core Background & Foreground ===
# Deep charcoal background (like London fog at night)
COLOR_BG = '#1A1A1A'            # Primary background (deep charcoal)
COLOR_BG_SECONDARY = '#242424'  # Slightly lighter for panels
COLOR_BG_TERTIARY = '#2E2E2E'   # Even lighter for inputs/boxes

# Foreground colors
COLOR_FG = '#E8E6E3'            # Primary text (warm off-white)
COLOR_FG_BRIGHT = '#F5F3F0'     # Brightest text for emphasis
COLOR_MUTED = '#9A9593'         # Secondary text (warm gray)
COLOR_MUTED_DARK = '#6B6663'    # Tertiary text (darker muted)

# === Accent Colors (Victorian Brown & Bronze) ===
COLOR_ACCENT = '#A0826D'        # Primary accent (Victorian brown)
COLOR_ACCENT_LIGHT = '#B89A7D'  # Lighter accent for hover states
COLOR_ACCENT_DARK = '#8B6F5C'   # Darker accent for pressed states

# === Status Colors ===
COLOR_INFO = '#9A9593'          # Information messages (neutral gray)
COLOR_SUCCESS = '#7A9A6F'       # Success messages (muted green)
COLOR_WARN = '#C9A56D'          # Warning messages (golden brown)
COLOR_ERROR = '#B86A60'         # Error messages (muted red)

# === Special Theme Colors ===
# Bronze/brown accents for Sherlock Holmes Victorian theme
COLOR_BRONZE = '#A0826D'        # Bronze accent (main theme)
COLOR_GOLD = '#C9A56D'          # Gold accent for special elements
COLOR_DEERSTALKER = '#8B7355'   # Deerstalker brown (decorative)

# === Border & Divider Colors ===
COLOR_BORDER = '#2E2E2E'        # Default border
COLOR_BORDER_LIGHT = '#3E3E3E'  # Lighter border for emphasis
COLOR_DIVIDER = '#2A2A2A'       # Subtle divider

# === Shadow & Overlay ===
COLOR_SHADOW = '#000000'        # Pure black for shadows (with alpha)
COLOR_OVERLAY = '#1A1A1A'       # Overlay background (with alpha)

# === Progress & Loading ===
COLOR_PROGRESS_BG = '#2E2E2E'   # Progress bar background
COLOR_PROGRESS_FG = '#A0826D'   # Progress bar fill (Victorian brown)

# === Semantic Aliases for Easy Use ===
COLOR_PRIMARY = COLOR_ACCENT
COLOR_SECONDARY = COLOR_BRONZE
COLOR_TEXT = COLOR_FG
COLOR_TEXT_DIM = COLOR_MUTED

