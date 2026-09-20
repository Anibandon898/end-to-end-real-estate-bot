(function () {
    "use strict";

    // =========================================================
    // PROPERTY PILOT AI — EMBEDDABLE CHATBOT WIDGET
    // =========================================================

    const API_URL =
        "https://propertypilot-ai-5yai.onrender.com/api/v1/chat";

    const SESSION_KEY = "propertypilot_widget_session";

    // ---------------------------------------------------------
    // Session
    // ---------------------------------------------------------

    function getSessionId() {
        let sessionId = localStorage.getItem(SESSION_KEY);

        if (!sessionId) {
            sessionId =
                "widget-" +
                Date.now() +
                "-" +
                Math.random().toString(36).substring(2, 10);

            localStorage.setItem(SESSION_KEY, sessionId);
        }

        return sessionId;
    }

    function resetSession() {
        const sessionId =
            "widget-" +
            Date.now() +
            "-" +
            Math.random().toString(36).substring(2, 10);

        localStorage.setItem(SESSION_KEY, sessionId);

        return sessionId;
    }

    // ---------------------------------------------------------
    // Styles
    // ---------------------------------------------------------

    const style = document.createElement("style");

    style.textContent = `
        #propertypilot-widget-button {
            position: fixed;
            right: 22px;
            bottom: 22px;
            width: 62px;
            height: 62px;
            border-radius: 50%;
            border: none;
            background: #111111;
            color: #d4af37;
            font-size: 28px;
            cursor: pointer;
            z-index: 999999;
            box-shadow: 0 8px 30px rgba(0,0,0,0.25);
            transition: transform 0.2s ease;
        }

        #propertypilot-widget-button:hover {
            transform: scale(1.08);
        }

        #propertypilot-widget {
            position: fixed;
            right: 22px;
            bottom: 96px;
            width: 370px;
            height: 560px;
            background: #ffffff;
            border-radius: 18px;
            overflow: hidden;
            box-shadow: 0 15px 50px rgba(0,0,0,0.25);
            z-index: 999998;
            display: none;
            font-family:
                Arial,
                Helvetica,
                sans-serif;
        }

        #propertypilot-header {
            height: 70px;
            background: #111111;
            color: #ffffff;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 18px;
            box-sizing: border-box;
        }

        .propertypilot-brand {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .propertypilot-logo {
            width: 38px;
            height: 38px;
            border-radius: 50%;
            background: #d4af37;
            color: #111111;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 18px;
        }

        .propertypilot-title {
            font-size: 16px;
            font-weight: bold;
        }

        .propertypilot-subtitle {
            font-size: 11px;
            opacity: 0.7;
            margin-top: 3px;
        }

        #propertypilot-close {
            background: transparent;
            border: none;
            color: white;
            font-size: 25px;
            cursor: pointer;
        }

        #propertypilot-messages {
            height: 420px;
            overflow-y: auto;
            padding: 18px;
            background: #f7f5ef;
            box-sizing: border-box;
        }

        .propertypilot-message {
            max-width: 82%;
            padding: 11px 14px;
            border-radius: 14px;
            margin-bottom: 12px;
            font-size: 14px;
            line-height: 1.45;
            word-wrap: break-word;
        }

        .propertypilot-bot {
            background: #ffffff;
            color: #222222;
            border-bottom-left-radius: 4px;
            margin-right: auto;
        }

        .propertypilot-user {
            background: #111111;
            color: #ffffff;
            border-bottom-right-radius: 4px;
            margin-left: auto;
        }

        #propertypilot-input-area {
            height: 70px;
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 10px;
            box-sizing: border-box;
            background: #ffffff;
            border-top: 1px solid #eeeeee;
        }

        #propertypilot-input {
            flex: 1;
            height: 46px;
            border: 1px solid #dddddd;
            border-radius: 24px;
            padding: 0 15px;
            outline: none;
            font-size: 14px;
            box-sizing: border-box;
        }

        #propertypilot-input:focus {
            border-color: #d4af37;
        }

        #propertypilot-send {
            width: 46px;
            height: 46px;
            border: none;
            border-radius: 50%;
            background: #d4af37;
            color: #111111;
            cursor: pointer;
            font-size: 18px;
            font-weight: bold;
        }

        #propertypilot-new-chat {
            position: absolute;
            right: 52px;
            top: 24px;
            background: transparent;
            border: none;
            color: #d4af37;
            font-size: 11px;
            cursor: pointer;
        }

        .propertypilot-typing {
            display: inline-flex;
            gap: 4px;
            align-items: center;
        }

        .propertypilot-dot {
            width: 6px;
            height: 6px;
            background: #888888;
            border-radius: 50%;
            animation: propertypilot-bounce 1.2s infinite;
        }

        .propertypilot-dot:nth-child(2) {
            animation-delay: 0.15s;
        }

        .propertypilot-dot:nth-child(3) {
            animation-delay: 0.3s;
        }

        @keyframes propertypilot-bounce {
            0%, 60%, 100% {
                transform: translateY(0);
            }

            30% {
                transform: translateY(-4px);
            }
        }

        @media (max-width: 600px) {

            #propertypilot-widget {
                right: 10px;
                left: 10px;
                bottom: 82px;
                width: auto;
                height: 70vh;
                max-height: 600px;
            }

            #propertypilot-messages {
                height: calc(70vh - 140px);
                max-height: 460px;
            }

            #propertypilot-widget-button {
                right: 16px;
                bottom: 16px;
            }
        }
    `;

    document.head.appendChild(style);

    // ---------------------------------------------------------
    // Widget HTML
    // ---------------------------------------------------------

    const button = document.createElement("button");

    button.id = "propertypilot-widget-button";
    button.innerHTML = "💬";
    button.setAttribute("aria-label", "Open PropertyPilot AI");

    const widget = document.createElement("div");

    widget.id = "propertypilot-widget";

    widget.innerHTML = `
        <div id="propertypilot-header">

            <div class="propertypilot-brand">

                <div class="propertypilot-logo">
                    P
                </div>

                <div>
                    <div class="propertypilot-title">
                        PropertyPilot AI
                    </div>

                    <div class="propertypilot-subtitle">
                        Smart Real Estate Assistant
                    </div>
                </div>

            </div>

            <button id="propertypilot-new-chat">
                New Chat
            </button>

            <button id="propertypilot-close">
                ×
            </button>

        </div>

        <div id="propertypilot-messages"></div>

        <div id="propertypilot-input-area">

            <input
                id="propertypilot-input"
                type="text"
                placeholder="Type your message..."
                autocomplete="off"
            />

            <button id="propertypilot-send">
                ➤
            </button>

        </div>
    `;

    document.body.appendChild(widget);
    document.body.appendChild(button);

    // ---------------------------------------------------------
    // Elements
    // ---------------------------------------------------------

    const messages = document.getElementById(
        "propertypilot-messages"
    );

    const input = document.getElementById(
        "propertypilot-input"
    );

    const sendButton = document.getElementById(
        "propertypilot-send"
    );

    const closeButton = document.getElementById(
        "propertypilot-close"
    );

    const newChatButton = document.getElementById(
        "propertypilot-new-chat"
    );

    // ---------------------------------------------------------
    // Add message
    // ---------------------------------------------------------

    function addMessage(text, type) {

        const message = document.createElement("div");

        message.className =
            "propertypilot-message " +
            (type === "user"
                ? "propertypilot-user"
                : "propertypilot-bot");

        message.textContent = text;

        messages.appendChild(message);

        messages.scrollTop = messages.scrollHeight;
    }

    // ---------------------------------------------------------
    // Typing indicator
    // ---------------------------------------------------------

    function showTyping() {

        const typing = document.createElement("div");

        typing.className =
            "propertypilot-message propertypilot-bot";

        typing.id = "propertypilot-typing";

        typing.innerHTML = `
            <span class="propertypilot-typing">
                <span class="propertypilot-dot"></span>
                <span class="propertypilot-dot"></span>
                <span class="propertypilot-dot"></span>
            </span>
        `;

        messages.appendChild(typing);

        messages.scrollTop = messages.scrollHeight;
    }

    function hideTyping() {

        const typing =
            document.getElementById(
                "propertypilot-typing"
            );

        if (typing) {
            typing.remove();
        }
    }

    // ---------------------------------------------------------
    // Send message
    // ---------------------------------------------------------

    async function sendMessage() {

        const message = input.value.trim();

        if (!message) {
            return;
        }

        addMessage(message, "user");

        input.value = "";

        input.disabled = true;
        sendButton.disabled = true;

        showTyping();

        try {

            const response = await fetch(API_URL, {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({

                    session_id: getSessionId(),

                    message: message

                })

            });

            if (!response.ok) {
                throw new Error(
                    "Server returned " +
                    response.status
                );
            }

            const data = await response.json();

            hideTyping();

            addMessage(
                data.reply ||
                "Sorry, I could not process that message.",
                "bot"
            );

        } catch (error) {

            hideTyping();

            addMessage(
                "I'm having trouble connecting right now. Please try again.",
                "bot"
            );

            console.error(
                "PropertyPilot Widget Error:",
                error
            );

        } finally {

            input.disabled = false;
            sendButton.disabled = false;

            input.focus();
        }
    }

    // ---------------------------------------------------------
    // Open / close
    // ---------------------------------------------------------

    button.addEventListener("click", function () {

        const isOpen =
            widget.style.display === "block";

        widget.style.display =
            isOpen ? "none" : "block";

        if (!isOpen) {

            if (messages.children.length === 0) {

                addMessage(
                    "Welcome! 👋 I'm your PropertyPilot AI real estate assistant. How can I help you today?",
                    "bot"
                );

            }

            input.focus();
        }

    });

    closeButton.addEventListener(
        "click",
        function () {
            widget.style.display = "none";
        }
    );

    // ---------------------------------------------------------
    // New conversation
    // ---------------------------------------------------------

    newChatButton.addEventListener(
        "click",
        function () {

            resetSession();

            messages.innerHTML = "";

            addMessage(
                "Welcome! 👋 Let's start a new conversation. May I have your name?",
                "bot"
            );

            input.focus();
        }
    );

    // ---------------------------------------------------------
    // Send events
    // ---------------------------------------------------------

    sendButton.addEventListener(
        "click",
        sendMessage
    );

    input.addEventListener(
        "keydown",
        function (event) {

            if (event.key === "Enter") {
                event.preventDefault();
                sendMessage();
            }

        }
    );

})();