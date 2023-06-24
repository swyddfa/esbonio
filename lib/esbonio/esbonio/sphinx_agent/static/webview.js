// This file gets injected into html pages built with Sphinx (assuming it's enabled of course!)
// which allows the webpage to talk with the preview server and coordinate details such as refreshes
// and page scrolling.
const scrollTargets = Array.from(document.querySelectorAll(".linemarker"))

// Return the line number we should ask the editor to scroll to.
function findScrollTarget() {
    let scrollTarget

    for (let target of scrollTargets) {
        const bbox = target.getBoundingClientRect()
        // TODO: This mechanism, probably needs to be made smarter as it does not account
        // for elements that are technically on screen but hidden. - e.g. by furo's header bar.
        if (bbox.top > 0) {
            scrollTarget = target
            break
        }
    }

    if (!scrollTarget) {
        return
    }

    let linum
    for (let cls of scrollTarget.classList) {
        let result = cls.match(/linemarker-(\d+)/)
        if (result) {
            linum = parseInt(result[1])
            break
        }
    }
    return linum
}


const queryString = window.location.search;
const queryParams = new URLSearchParams(queryString);
const ws = parseInt(queryParams.get("ws")); // is the number 123
console.debug(`Connecting to websocket server on port: ${ws}...`)

const socket = new WebSocket(`ws://localhost:${ws}`);
let connected = false

function sendMessage(data) {
    if (!connected) {
        return
    }
    let msg = JSON.stringify(data)
    console.debug(msg)
    socket.send(msg);
}

const handlers = {
    "view/reload": function (params) {
        console.debug("Reloading page...")
        window.location.reload()
    }
}

function handle(message) {
    console.debug(`${JSON.stringify(message, undefined, 2)}`)

    if (message.id) {
        if (message.error) {
            console.error(`Error: ${JSON.stringify(message.error, undefined, 2)}`)
        } else if (message.method) {
            let method = message.method
            console.debug(`Got request: ${method}, ${JSON.stringify(params, undefined, 2)}`)
        } else {
            let result = message.result
            console.debug(`Got response: ${JSON.stringify(result, undefined, 2)}`)
        }
    } else {
        let handler = handlers[message.method]
        if (handler) {
            handler(message.params)
        } else {
            console.error(`Got unknown notification: '${method}'`)
        }
    }
}

window.addEventListener("scroll", (event) => {
    let linum = findScrollTarget()
    if (linum) {
        sendMessage(
            { jsonrpc: "2.0", method: "editor/scroll", params: { line: linum } }
        )
    }
})

// Connection opened
socket.addEventListener("open", (event) => {
    console.debug("Connected.")
    connected = true
});

// Listen for messages
socket.addEventListener("message", (event) => {
    handle(JSON.parse(event.data))
});
