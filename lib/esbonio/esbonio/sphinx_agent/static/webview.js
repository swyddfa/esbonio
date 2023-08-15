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

// Return the line number we should ask the editor to scroll to.
function findScrollTarget() {

    // Are we at the top of the page?
    if (window.scrollY <= 100) {
        return -1
    }

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

let scrollTargets = new Map()

const host = window.location.hostname;
const queryString = window.location.search;
const queryParams = new URLSearchParams(queryString);
const ws = parseInt(queryParams.get("ws"));
const showMarkers = queryParams.has("show-markers")

const wsServer = `ws://${host}:${ws}`
console.debug(`Connecting to '${wsServer}'...`)

const socket = new WebSocket(wsServer);
let connected = false

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
        if (params.line <= 1) {
            window.scrollTo(0, 0)
            return
        }

        // TODO: Look for targets within X of target line instead?
        let target = scrollTargets.get(params.line)
        if (!target) {
            return
        }

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

function main() {
    scrollTargets = indexScrollTargets()
    console.debug(scrollTargets)

    if (showMarkers) {
        let markerStyle = document.createElement('style')
        let lines = [".linemarker { background: rgb(255, 0, 0, 0.25); position: relative; }"]
        for (let line of scrollTargets.keys()) {
            lines.push(`.linemarker-${line}::before {
                          content: 'line ${line}'; position: absolute; right: 0; top: -1.2em;
                       }`)
        }

        markerStyle.innerText = lines.join('\n')
        document.body.append(markerStyle)
    }

    // Are we in an <iframe>?
    if (window.parent !== window.top) {
        window.parent.postMessage({ 'ready': true }, "*")
    }
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", main);
} else {
    main();
}
