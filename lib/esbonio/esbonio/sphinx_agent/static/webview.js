// This file gets injected into html pages built with Sphinx
// which allows the webpage to talk with the preview server and coordinate details such as refreshes
// and page scrolling.

/**
 * Find the uri and line number the editor should scroll to
 *
 * @returns {[string, number]} - The uri and line number
 */
function findEditorScrollTarget() {
    const markers = document.querySelectorAll(".esbonio-marker")

    for (let marker of markers) {
        const bbox = marker.getBoundingClientRect()
        // TODO: This probably needs to be made smarter as it does not account
        // for elements that are technically on screen but hidden. - e.g. by furo's header bar.
        if (bbox.top < 60) {
            continue
        }

        const match = marker.className.match(/.* esbonio-marker-(\d+).*/)
        if (!match || !match[1]) {
            console.debug(`Unable to find marker id in '${marker.className}'`)
            return
        }

        const markerId = match[1]
        const location = document.querySelector(`#esbonio-marker-index span[data-id="${markerId}"]`)
        if (!location) {
            console.debug(`Unable to locate source for marker id: '${markerId}'`)
            return
        }

        const uri = location.dataset.uri
        const line = parseInt(location.dataset.line)
        return [uri, line]
    }

    return
}

/**
 * Scroll the webview to show the given location
 *
 * @param {string} uri - The uri of the document to reveal
 * @param {number} linum - The line number within that document to reveal
 */
function scrollViewTo(uri, linum) {

    // Select all the markers with the given uri.
    const markers = Array.from(
        document.querySelectorAll(`#esbonio-marker-index span[data-uri="${uri}"]`)
    )

    if (!markers) {
        return
    }

    /** @type {HTMLElement} */
    let current

    /** @type {number} */
    let currentLine = 0

    /** @type {HTMLElement} */
    let previous

    /** @type {number} */
    let previousLine

    for (let marker of markers) {
        let markerId = marker.dataset.id
        let markerLine = parseInt(marker.dataset.line)
        let element = document.querySelector(`.esbonio-marker-${markerId}`)

        // Only consider markers that correspond with an element currently in the DOM
        if (!element) {
            continue
        }

        current = element
        currentLine = markerLine

        // Have we passed the target line number?
        if (markerLine > linum) {
            break
        }

        previous = current
        previousLine = currentLine
    }

    if (!current) {
        return
    }

    if (!previous) {
        previous = current
        previousLine = currentLine
    }

    // Scroll the view to a position that is an interpolation between the previous and
    // current marker based on the requested line number.
    const previousPos = window.scrollY + previous.getBoundingClientRect().top
    const currentPos = window.scrollY + current.getBoundingClientRect().top

    const t = (linum - previousLine) / Math.max(currentLine - previousLine, 1)
    const y = (1 - t) * previousPos + t * currentPos

    console.table({line: linum, previous: previousLine, current: currentLine, t: t, y: y})

    window.scrollTo(0, y - 60)
}

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
    "view/scroll": (params) => {scrollViewTo(params.uri, params.line)}
}

function handle(message) {
    // console.debug(`${JSON.stringify(message, undefined, 2)}`)

    if (message.id) {
        if (message.error) {
            console.error(`Error: ${JSON.stringify(message.error, undefined, 2)}`)
        } else if (message.method) {
            let method = message.method
            console.debug(`Request: ${method}, ${JSON.stringify(params, undefined, 2)}`)
        } else {
            let result = message.result
            console.debug(`Response: ${JSON.stringify(result, undefined, 2)}`)
        }
    } else {
        let handler = handlers[message.method]
        if (handler) {
            // console.debug(`Notification: ${message.method}, ${JSON.stringify(message.params)} `)
            handler(message.params)
        } else {
            console.error(`Got unknown notification: '${message.method}'`)
        }
    }
}

window.addEventListener("scroll", (event) => {
    const target = findEditorScrollTarget()
    if (!target) {
        return
    }

    const uri = target[0]
    const line = target[1]

    if (!uri || !line) {
        return
    }

    // TODO: Rate limits.
    sendMessage(
        { jsonrpc: "2.0", method: "editor/scroll", params: { uri: uri, line: line } }
    )

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
