#!/bin/bash
# Install (or remove with --uninstall) a macOS LaunchAgent that runs scripts/run_rebalance.sh at 08:00 local
# time on weekdays, before the 9:30am ET open. Orders are Alpaca paper only.
set -e
LABEL="com.ai-stock-trading.rebalance"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [ "$1" = "--uninstall" ]; then
  launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
  rm -f "$PLIST"
  echo "Removed $LABEL"
  exit 0
fi

chmod +x "$ROOT/scripts/run_rebalance.sh"
mkdir -p "$HOME/Library/LaunchAgents"
{
  echo '<?xml version="1.0" encoding="UTF-8"?>'
  echo '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">'
  echo '<plist version="1.0"><dict>'
  echo "  <key>Label</key><string>$LABEL</string>"
  echo "  <key>ProgramArguments</key><array><string>/bin/bash</string><string>$ROOT/scripts/run_rebalance.sh</string></array>"
  echo '  <key>StartCalendarInterval</key><array>'
  for day in 1 2 3 4 5; do
    echo "    <dict><key>Weekday</key><integer>$day</integer><key>Hour</key><integer>8</integer><key>Minute</key><integer>0</integer></dict>"
  done
  echo '  </array>'
  echo "  <key>StandardErrorPath</key><string>$ROOT/data/live/launchd.err</string>"
  echo '</dict></plist>'
} > "$PLIST"

mkdir -p "$ROOT/data/live"
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
echo "Installed $LABEL: weekdays 08:00 local time. Log: $ROOT/data/live/rebalance.log"
echo "Remove with: scripts/install_schedule.sh --uninstall"
