from pathlib import Path

path = Path("frontend/index.html")

html = path.read_text(encoding="utf-8-sig")

if 'id="newConversationBtn"' in html:
    print("ICON ALREADY EXISTS - NO CHANGE MADE")
    raise SystemExit

marker = 'class="close-chat"'

position = html.find(marker)

if position == -1:
    print("TARGET NOT FOUND - NO CHANGE MADE")
    raise SystemExit

button_start = html.rfind("<button", 0, position)

if button_start == -1:
    print("BUTTON START NOT FOUND - NO CHANGE MADE")
    raise SystemExit

icon = '''<button
            class="new-conversation-btn"
            id="newConversationBtn"
            type="button"
            onclick="startNewConversation()"
            title="Start a new conversation"
            aria-label="Start a new conversation"
        >
            ↻
        </button>

        '''

html = html[:button_start] + icon + html[button_start:]

path.write_text(html, encoding="utf-8")

print("ICON ADDED SUCCESSFULLY")