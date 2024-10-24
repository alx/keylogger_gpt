# keylogger_gpt

Send screenshot to openai gpt-4o to get informations visible on screen 

## Usage

``` sh
# Take a fullscreen screenshot
flameshot full -p /home/alx/org/inbox/screenshots/$(date +"%Y-%m-%d_%H-%M-%S").png

# Process screenshot
#   - url in clipboard
#   - org-mode item in /home/alx/org/inbox_screenshot.org
python3 /home/alx/code/keylogger_gpt/main.py
```
