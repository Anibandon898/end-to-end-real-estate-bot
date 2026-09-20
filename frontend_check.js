

/* ============================================================
   PROPERTY PILOT AI
   FRONTEND ENGINE
============================================================ */


/*
    ==========================================================
    API
    ==========================================================

    Production Render backend.
*/

const API_URL = "http://127.0.0.1:8000/api/v1/chat";
const UPLOAD_API_URL = "http://127.0.0.1:8000/api/v1/upload-image";
const SESSION_KEY =
    "propertypilot_session";


const TOTAL_FIELDS = 8;


/*
    Maximum images selected at once.
*/

const MAX_IMAGES = 8;


/*
    Maximum image size.

    8 MB.
*/

const MAX_IMAGE_SIZE = 20 * 1024 * 1024;



/* ============================================================
   SESSION
============================================================ */

function createSessionId(){

    if(
        window.crypto &&
        typeof window.crypto.randomUUID === "function"
    ){

        return window.crypto.randomUUID();

    }

    return (
        "propertypilot-" +
        Date.now() +
        "-" +
        Math.random()
            .toString(36)
            .substring(2,10)
    );

}


function getSessionId(){

    let session =
        localStorage.getItem(
            SESSION_KEY
        );


    if(!session){

        session =
            createSessionId();

        localStorage.setItem(
            SESSION_KEY,
            session
        );

    }


    return session;

}


let sessionId =
    getSessionId();



/* ============================================================
   ELEMENTS
============================================================ */

const chatBox =
    document.getElementById(
        "chatBox"
    );


const messageInput =
    document.getElementById(
        "messageInput"
    );


const sendButton =
    document.getElementById(
        "sendButton"
    );


const newChatButton =
    document.getElementById(
        "newChatButton"
    );


const progressBar =
    document.getElementById(
        "progressBar"
    );


const progressText =
    document.getElementById(
        "progressText"
    );


let typingRow =
    document.getElementById(
        "typingRow"
    );


let typingIndicator =
    document.getElementById(
        "typingIndicator"
    );


const uploadButton =
    document.getElementById(
        "uploadButton"
    );


const imageInput =
    document.getElementById(
        "imageInput"
    );


const attachmentArea =
    document.getElementById(
        "attachmentArea"
    );


const attachmentList =
    document.getElementById(
        "attachmentList"
    );


const attachmentTitle =
    document.getElementById(
        "attachmentTitle"
    );


const clearAttachments =
    document.getElementById(
        "clearAttachments"
    );


const uploadStatus =
    document.getElementById(
        "uploadStatus"
    );


const connectionBanner =
    document.getElementById(
        "connectionBanner"
    );



/* ============================================================
   STATE
============================================================ */

let busy = false;

let selectedImages = [];

let uploadedImages = [];



/* ============================================================
   TIME
============================================================ */

function currentTime(){

    return new Date().toLocaleTimeString(
        [],
        {
            hour:"2-digit",
            minute:"2-digit"
        }
    );

}



/* ============================================================
   ADD MESSAGE
============================================================ */

function addMessage(
    text,
    type
){

    const row =
        document.createElement(
            "div"
        );


    row.className =
        "message-row" +
        (
            type === "user"
                ? " user"
                : ""
        );


    const message =
        document.createElement(
            "div"
        );


    message.className =
        "message " +
        type;


    const content =
        document.createElement(
            "div"
        );


    content.className =
        "message-content";


    content.textContent =
        text;


    const time =
        document.createElement(
            "span"
        );


    time.className =
        "message-time";


    time.textContent =
        currentTime();


    message.appendChild(
        content
    );


    message.appendChild(
        time
    );


    row.appendChild(
        message
    );


    chatBox.insertBefore(
        row,
        typingRow
    );


    scrollToBottom();

}



/* ============================================================
   IMAGE MESSAGE
============================================================ */

function addImageMessage(){

    if(
        selectedImages.length === 0
    ){

        return;

    }


    const row =
        document.createElement(
            "div"
        );


    row.className =
        "message-row user";


    const message =
        document.createElement(
            "div"
        );


    message.className =
        "message user";


    const content =
        document.createElement(
            "div"
        );


    content.className =
        "message-content";


    content.textContent =
        selectedImages.length === 1
            ? "📷 Property image attached"
            : `📷 ${selectedImages.length} property images attached`;


    message.appendChild(
        content
    );


    const time =
        document.createElement(
            "span"
        );


    time.className =
        "message-time";


    time.textContent =
        currentTime();


    message.appendChild(
        time
    );


    row.appendChild(
        message
    );


    chatBox.insertBefore(
        row,
        typingRow
    );


    scrollToBottom();

}



/* ============================================================
   SCROLL
============================================================ */

function scrollToBottom(){

    requestAnimationFrame(
        () => {

            chatBox.scrollTop =
                chatBox.scrollHeight;

        }
    );

}



/* ============================================================
   TYPING
============================================================ */

function showTyping(){

    if(!typingRow){
        return;
    }


    typingRow.style.display =
        "flex";


    if(typingIndicator){

        typingIndicator.style.display =
            "flex";

    }


    scrollToBottom();

}


function hideTyping(){

    if(!typingRow){
        return;
    }


    typingRow.style.display =
        "none";


    if(typingIndicator){

        typingIndicator.style.display =
            "none";

    }

}



/* ============================================================
   PROGRESS
============================================================ */

function updateProgress(data){

    if(
        !data ||
        !data.collected_data
    ){

        return;

    }


    const collected =
        data.collected_data;


    const fields = [

        "name",
        "email",
        "phone",
        "purpose",
        "location",
        "property_type",
        "budget",
        "timeline"

    ];


    let completed =
        0;


    fields.forEach(
        field => {

            const value =
                collected[field];


            if(
                value !== null &&
                value !== undefined &&
                String(value).trim() !== ""
            ){

                completed++;

            }

        }
    );


    const percent =
        Math.round(
            (
                completed /
                TOTAL_FIELDS
            ) * 100
        );


    progressBar.style.width =
        percent + "%";


    progressText.textContent =
        percent + "%";

}



/* ============================================================
   SUCCESS CARD
============================================================ */

function addSuccessCard(data){

    const quality =
        data.lead_quality ||
        (
            data.collected_data &&
            data.collected_data.lead_quality
        ) ||
        "COLD";


    const n8n =
        data.integrations &&
        data.integrations.n8n &&
        data.integrations.n8n.sent;


    const supabase =
        data.integrations &&
        data.integrations.supabase &&
        data.integrations.supabase.saved;


    const row =
        document.createElement(
            "div"
        );


    row.className =
        "message-row";


    const card =
        document.createElement(
            "div"
        );


    card.className =
        "success-card";


    card.innerHTML = `

        <div class="success-header">

            <div class="success-title">

                ✓ Property request received

            </div>

            <div class="quality">

                ${escapeHtml(quality)} LEAD

            </div>

        </div>


        <div class="success-text">

            Your requirements have been captured
            successfully. Our real estate team can
            now follow up with your request.

        </div>


        <div class="integrations">

            <div class="integration">

                n8n:
                ${n8n ? "Connected" : "Pending"}

            </div>


            <div class="integration">

                Database:
                ${supabase ? "Saved" : "Pending"}

            </div>

        </div>

    `;


    row.appendChild(
        card
    );


    chatBox.insertBefore(
        row,
        typingRow
    );


    scrollToBottom();

}



/* ============================================================
   ESCAPE HTML
============================================================ */

function escapeHtml(value){

    return String(value)
        .replace(
            /[&<>"']/g,
            function(character){

                const map = {

                    "&":"&amp;",
                    "<":"&lt;",
                    ">":"&gt;",
                    '"':"&quot;",
                    "'":"&#039;"

                };

                return map[character];

            }
        );

}



/* ============================================================
   UPLOAD STATUS
============================================================ */

function setUploadStatus(
    text,
    type = ""
){

    uploadStatus.textContent =
        text;


    uploadStatus.className =
        "upload-status";


    if(text){

        uploadStatus.classList.add(
            "visible"
        );

    }


    if(type){

        uploadStatus.classList.add(
            type
        );

    }

}



/* ============================================================
   RENDER IMAGE PREVIEWS
============================================================ */

function renderImagePreviews(){

    attachmentList.innerHTML =
        "";


    if(
        selectedImages.length === 0
    ){

        attachmentArea.classList.remove(
            "visible"
        );

        attachmentTitle.textContent =
            "Property images";

        return;

    }


    attachmentArea.classList.add(
        "visible"
    );


    attachmentTitle.textContent =
        selectedImages.length === 1
            ? "1 property image"
            : `${selectedImages.length} property images`;


    selectedImages.forEach(
        (item,index) => {

            const wrapper =
                document.createElement(
                    "div"
                );


            wrapper.className =
                "attachment-item";


            const image =
                document.createElement(
                    "img"
                );


            image.src =
                item.preview;


            image.alt =
                "Property image";


            const remove =
                document.createElement(
                    "button"
                );


            remove.type =
                "button";


            remove.className =
                "remove-attachment";


            remove.textContent =
                "Ã—";


            remove.title =
                "Remove image";


            remove.addEventListener(
                "click",
                () => {

                    removeImage(index);

                }
            );


            wrapper.appendChild(
                image
            );


            wrapper.appendChild(
                remove
            );


            attachmentList.appendChild(
                wrapper
            );

        }
    );


    scrollToBottom();

}



/* ============================================================
   REMOVE IMAGE
============================================================ */

function removeImage(index){

    if(
        selectedImages[index] &&
        selectedImages[index].preview
    ){

        URL.revokeObjectURL(
            selectedImages[index].preview
        );

    }


    selectedImages.splice(
        index,
        1
    );


    renderImagePreviews();


    if(
        selectedImages.length === 0
    ){

        setUploadStatus(
            ""
        );

    }

}



/* ============================================================
   CLEAR IMAGES
============================================================ */

function clearAllImages(){

    selectedImages.forEach(
        item => {

            if(item.preview){

                URL.revokeObjectURL(
                    item.preview
                );

            }

        }
    );


    selectedImages = [];


    uploadedImages = [];


    imageInput.value =
        "";


    renderImagePreviews();


    setUploadStatus(
        ""
    );

}



/* ============================================================
   HANDLE FILES
============================================================ */

function handleSelectedFiles(
    files
){

    if(!files || !files.length){

        return;

    }


    const incoming =
        Array.from(files);


    if(
        selectedImages.length +
        incoming.length >
        MAX_IMAGES
    ){

        setUploadStatus(
            `You can attach a maximum of ${MAX_IMAGES} images.`,
            "error"
        );

        return;

    }


    let accepted =
        0;


    incoming.forEach(
        file => {

            if(
                !file.type.startsWith(
                    "image/"
                )
            ){

                return;

            }


            if(
                file.size >
                MAX_IMAGE_SIZE
            ){

                setUploadStatus(
                    `${file.name} is larger than 20MB.`,
                    "error"
                );

                return;

            }


            const preview =
                URL.createObjectURL(
                    file
                );


            selectedImages.push({

                file:
                    file,

                preview:
                    preview,

                name:
                    file.name,

                size:
                    file.size,

                type:
                    file.type

            });


            accepted++;

        }
    );


    if(accepted > 0){

        setUploadStatus(
            `${accepted} image${accepted > 1 ? "s" : ""} ready to attach.`,
            "success"
        );

    }


    renderImagePreviews();

}



/* ============================================================
   UPLOAD IMAGES
============================================================ */

/*
    This function is ready for the backend endpoint:

    POST /api/v1/upload

    The backend can later upload the images to
    Supabase Storage and return their public URLs.

    Until that endpoint is available, the frontend still
    allows the user to select and preview images without
    breaking the chatbot.
*/

async function uploadImages(){

    if(
        selectedImages.length === 0
    ){

        return [];

    }


    const uploaded = [];


    for(
        const item of selectedImages
    ){

        try{

            const formData =
                new FormData();


            formData.append(
                "file",
                item.file
            );


            formData.append(
                "session_id",
                sessionId
            );


            const response =
                await fetch(
                    UPLOAD_API_URL,
                    {
                        method:"POST",
                        body:formData
                    }
                );


            if(
                !response.ok
            ){

                /*
                    If the upload endpoint does not
                    exist yet, don't break the chat.
                */

                if(
                    response.status === 404
                ){

                    console.warn(
                        "Image upload endpoint is not active yet."
                    );

                    return [];

                }


                throw new Error(
                    "Image upload failed."
                );

            }


            const data =
                await response.json();


            if(
                data.url
            ){

                uploaded.push(
                    data.url
                );

            }
            else if(
                data.image_url
            ){

                uploaded.push(
                    data.image_url
                );

            }

        }
        catch(error){

            console.warn(
                "Image upload:",
                error
            );

            /*
                Do not stop normal chat because
                image storage is unavailable.
            */

            return [];

        }

    }


    return uploaded;

}



/* ============================================================
   SEND MESSAGE
============================================================ */

async function sendMessage(){

    if(busy){

        return;

    }


    const message =
        messageInput.value.trim();


    /*
        Allow image-only messages.
    */

    if(
        !message &&
        selectedImages.length === 0
    ){

        messageInput.focus();

        return;

    }


    busy = true;


    sendButton.disabled =
        true;


    uploadButton.disabled =
        true;


    connectionBanner.classList.remove(
        "visible"
    );


    /*
        Show user's text.
    */

    if(message){

        addMessage(
            message,
            "user"
        );

    }


    /*
        Show attached image message.
    */

    if(
        selectedImages.length > 0
    ){

        addImageMessage();

    }


    messageInput.value =
        "";


    showTyping();


    try{

        /*
            Try uploading images.

            If the backend upload endpoint is not
            available, normal chat continues.
        */

        uploadedImages =
            await uploadImages();


        let finalMessage = message;

        if(
            !finalMessage
        ){

            finalMessage =
                "I have attached property image(s). Please help me with this property.";

        }


        const response =
            await fetch(
                API_URL,
                {
                    method:"POST",

                    headers:{
                        "Content-Type":
                            "application/json"
                    },

                    body:JSON.stringify({

                        session_id:
                            sessionId,

                        message:
                            finalMessage

                    })

                }
            );


        let data;


        try{

            data =
                await response.json();

        }
        catch(jsonError){

            throw new Error(
                "The server returned an invalid response."
            );

        }


        hideTyping();


        if(
            !response.ok ||
            data.success === false
        ){

            throw new Error(
                data.error ||
                data.detail ||
                "Unable to process message."
            );

        }


        connectionBanner.classList.remove(
            "visible"
        );


        addMessage(
            data.reply ||
            "I received your message.",
            "bot"
        );


        updateProgress(
            data
        );


        if(data.lead_complete){

            addSuccessCard(
                data
            );

        }


        /*
            Clear images only after successful
            chat processing.
        */

        clearAllImages();


    }
    catch(error){

        hideTyping();


        console.error(
            "PropertyPilot AI Error:",
            error
        );


        connectionBanner.classList.add(
            "visible"
        );


        addMessage(
            "I'm having trouble connecting to PropertyPilot AI right now. Please try again in a moment.",
            "bot"
        );

    }
    finally{

        busy = false;


        sendButton.disabled =
            false;


        uploadButton.disabled =
            false;


        messageInput.focus();

    }

}



/* ============================================================
   QUICK ACTIONS
============================================================ */

function setupQuickActions(){

    document
        .querySelectorAll(
            ".quick-button"
        )
        .forEach(
            button => {

                button.addEventListener(
                    "click",
                    function(){

                        /*
                            Put the suggestion in the
                            input so the user can edit it.
                        */

                        messageInput.value =
                            this.dataset.message;


                        messageInput.focus();

                    }
                );

            }
        );

}



/* ============================================================
   NEW CHAT
============================================================ */

function resetChat(){

    clearAllImages();


    localStorage.removeItem(
        SESSION_KEY
    );


    sessionId =
        createSessionId();


    localStorage.setItem(
        SESSION_KEY,
        sessionId
    );


    chatBox.innerHTML = `

        <div class="date-label">
            Today
        </div>


        <div class="message-row">

            <div class="message bot">

                <div class="message-content">

Welcome! 👋 I'm your PropertyPilot AI real estate assistant.

Let's start a fresh conversation.

You can speak naturally. For example:

"David"
"David Okoro"
"I'm David"
"I'm David Okoro"
"My name is David"

May I have your name?

                </div>

                <span class="message-time">
                    Just now
                </span>

            </div>

        </div>


        <div
            class="quick-actions"
            id="quickActions">


            <button
                type="button"
                class="quick-button"
                data-message="I am looking for a house">

                🏢  Find a house

            </button>


            <button
                type="button"
                class="quick-button"
                data-message="I am looking for an apartment">

                🏢 Find an apartment

            </button>


            <button
                type="button"
                class="quick-button"
                data-message="I am looking for land">

                🌳 Find land

            </button>


            <button
                type="button"
                class="quick-button"
                data-message="I want to invest in property">

                💼 Property investment

            </button>


            <button
                type="button"
                class="quick-button"
                data-message="I want to rent a property">

                🔑 Rent a property

            </button>


        </div>


        <div
            class="connection-banner"
            id="connectionBanner">

            PropertyPilot AI is temporarily unable to connect
            to the assistant server.

        </div>


        <div
            class="message-row typing-row"
            id="typingRow">

            <div
                class="typing"
                id="typingIndicator">

                <span></span>
                <span></span>
                <span></span>

            </div>

        </div>

    `;


    /*
        Reconnect dynamic elements.
    */

    typingRow =
        document.getElementById(
            "typingRow"
        );


    typingIndicator =
        document.getElementById(
            "typingIndicator"
        );


    progressBar.style.width =
        "0%";


    progressText.textContent =
        "0%";


    busy =
        false;


    sendButton.disabled =
        false;


    uploadButton.disabled =
        false;


    messageInput.value =
        "";


    setupQuickActions();


    messageInput.focus();


    scrollToBottom();

}



/* ============================================================
   FILE INPUT
============================================================ */

uploadButton.addEventListener(
    "click",
    function(){

        if(busy){

            return;

        }

        imageInput.click();

    }
);


imageInput.addEventListener(
    "change",
    function(){

        handleSelectedFiles(
            this.files
        );

    }
);



/* ============================================================
   CLEAR ATTACHMENTS
============================================================ */

clearAttachments.addEventListener(
    "click",
    clearAllImages
);



/* ============================================================
   DRAG AND DROP
============================================================ */

const inputBox =
    document.querySelector(
        ".input-box"
    );


inputBox.addEventListener(
    "dragover",
    function(event){

        event.preventDefault();

        inputBox.style.borderColor =
            "var(--gold)";

    }
);


inputBox.addEventListener(
    "dragleave",
    function(){

        inputBox.style.borderColor =
            "";

    }
);


inputBox.addEventListener(
    "drop",
    function(event){

        event.preventDefault();

        inputBox.style.borderColor =
            "";

        handleSelectedFiles(
            event.dataTransfer.files
        );

    }
);



/* ============================================================
   SEND BUTTON
============================================================ */

sendButton.addEventListener(
    "click",
    sendMessage
);



/* ============================================================
   NEW CHAT
============================================================ */

newChatButton.addEventListener(
    "click",
    resetChat
);



/* ============================================================
   ENTER KEY
============================================================ */

messageInput.addEventListener(
    "keydown",
    function(event){

        if(
            event.key === "Enter" &&
            !event.shiftKey
        ){

            event.preventDefault();

            sendMessage();

        }

    }
);



/* ============================================================
   START
============================================================ */

setupQuickActions();

messageInput.focus();


/*
    Initial status.
*/

setUploadStatus("");

