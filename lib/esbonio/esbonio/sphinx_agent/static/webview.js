// This file gets injected into html pages built with Sphinx (assuming it's enabled of course!)
// which allows the webpage to talk with the preview server and coordinate details such as refreshes
// and page scrolling.
function indexScrollTargets() {
    let targets = new Map()
    for (let target of Array.from(document.querySelectorAll(".linemarker"))) {

        let linum
        for (let cls of target.classList) {
            let result = cls.match(/linemarker-(\d+)/)
            if (result) {
                linum = parseInt(result[1])
                targets.set(linum, target)
                break
            }
        }
    }

    return targets
}

const scrollTargets = indexScrollTargets()
console.debug(scrollTargets)

// Return the line number we should ask the editor to scroll to.
function findScrollTarget() {

    for (let [linum, target] of scrollTargets.entries()) {
        const bbox = target.getBoundingClientRect()
        // TODO: This probably needs to be made smarter as it does not account
        // for elements that are technically on screen but hidden. - e.g. by furo's header bar.
        if (bbox.top > 0) {
            return linum
        }
    }

    return
}


const queryString = window.location.search;
const queryParams = new URLSearchParams(queryString);
const ws = parseInt(queryParams.get("ws"));
console.debug(`Connecting to websocket server on port: ${ws}...`)

const socket = new WebSocket(`ws://localhost:${ws}`);
let connected = false

const COOLDOWN = 1000 // ms
let editorInControl = undefined

function sendMessage(data) {
    if (!connected) {
        return
    }
    let msg = JSON.stringify(data)
    // console.debug(msg)
    socket.send(msg);
}

const handlers = {
    "view/reload": function (params) {
        console.debug("Reloading page...")
        window.location.reload()
    },
    "view/scroll": function (params) {
        // TODO: Look for targets within X of target line instead?
        let target = scrollTargets.get(params.line)
        if (!target) {
            return
        }

        // Don't send `editor/scroll` messages for a while to prevent the view and
        // editor from fighting each other for control.
        if (editorInControl) {
            clearTimeout(editorInControl)
        }
        editorInControl = setTimeout(() => {
            editorInControl = undefined
            console.debug("editorInControl cooldown ended.")
        }, COOLDOWN)

        target.scrollIntoView(true)
    }
}

function handle(message) {
    // console.debug(`${JSON.stringify(message, undefined, 2)}`)

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
            console.error(`Got unknown notification: '${message.method}'`)
        }
    }
}

window.addEventListener("scroll", (event) => {
    if (editorInControl) {
        return
    }

    let linum = findScrollTarget()
    if (linum) {
        // TODO: Rate limits.
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
