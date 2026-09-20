from pathlib import Path

path = Path("frontend/index.html")

html = path.read_text(encoding="utf-8-sig")

if "async function startNewConversation()" in html:
    print("FUNCTION ALREADY EXISTS - NO CHANGE MADE")
    raise SystemExit

function = r'''
<script>
async function startNewConversation() {
    try {
        const response = await fetch(
            "http://127.0.0.1:8000/api/v1/new-session",
            {
                method: "POST"
            }
        );

        const data = await response.json();

        if (data.success) {
            localStorage.setItem(
                "propertypilot_session",
                data.session_id
            );

            window.location.reload();
        }
    } catch (error) {
        console.error(
            "New conversation error:",
            error
        );
    }
}
</script>
'''

marker = "</body>"

if marker not in html:
    print("BODY MARKER NOT FOUND - NO CHANGE MADE")
    raise SystemExit

html = html.replace(marker, function + "\n" + marker, 1)

path.write_text(html, encoding="utf-8")

print("NEW CONVERSATION FUNCTION ADDED SUCCESSFULLY")