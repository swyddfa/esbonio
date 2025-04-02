// This file gets injected into html pages built with Sphinx
// which allows the webpage to talk with the preview server and coordinate details such as refreshes
// and page scrolling.

/** @type {WebSocket} */
let socket

/** @type {string} */
let targetUri

/** @type {number} */
let targetLine

/**
 * Rewrite internal links so that the link between the webview and
 * language server is maintained across pages.
 */
function rewriteInternalLinks(wsPort) {
    if (!wsPort) {
        return
    }

    const links = Array.from(document.querySelectorAll("a.internal"))

    for (let link of links) {
        let uri
        try {
            uri = new URL(link.href)
        } catch (err) {
            console.debug(`Skipping link ${link.href}, ${err}`)
            continue
        }

        if (!uri.search) {
            uri.search = `?ws=${wsPort}`
        } else if (!uri.searchParams.get('ws')) {
            uri.search += `&ws=${wsPort}`
        }

        link.href = uri.toString()
    }
}

/**
 * Sync the webview's scroll position with the editor
 */
function syncScrollPosition() {
    const target = findEditorScrollTarget()
    if (!target) {
        console.debug('No target found')
        return
    }

    const uri = target[0]
    const line = target[1]

    if (!uri || !line) {
        console.debug('Missing uri or line')
        return
    }

    if (uri === targetUri && line === targetLine) {
        return
    }

    sendMessage(
        { jsonrpc: "2.0", method: "editor/scroll", params: { uri: uri, line: line } }
    )

    targetUri = uri
    targetLine = line
}

/**
 * Get the uri and line number of the given marker
 *
 * @param {HTMLElement} marker
 * @returns {[string, number]} - The uri and line number
 */
function getMarkerLocation(marker) {
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

        return getMarkerLocation(marker)
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

    // console.table({line: linum, previous: previousLine, current: currentLine, t: t, y: y})

    window.scrollTo(0, y - 60)
    targetUri = uri
    targetLine = linum
}

/**
 * Render the markers used to synchronise scroll state
 */
function renderLineMarkers() {

    const markers = Array.from(document.querySelectorAll(`.esbonio-marker`))
    let lines = [".esbonio-marker { position: relative; }"]

    for (let marker of markers) {
        let location = getMarkerLocation(marker)
        if (!location) {
            continue
        }

        let uri = location[0]
        let line = location[1]

        const match = marker.className.match(/.* esbonio-marker-(\d+).*/)
        let markerId = match[1]

        lines.push(`
.esbonio-marker-${markerId}::before {
  display: none;
  content: '${uri}:${line}';
  font-family: monospace;
  position: absolute;
  top: -1.2em;
}

.esbonio-marker-${markerId}:hover::before {
  display: block;
}
`)
    }

    let markerStyle = document.createElement('style')
    markerStyle.innerText = lines.join('\n')
    document.body.append(markerStyle)
}

const queryParams = new URLSearchParams(window.location.search);
const showMarkers = queryParams.has("show-markers")
const wsUrl = queryParams.get("ws");

const textDecoder = new TextDecoder()


function sendMessage(data) {
    if (!socket || socket.readyState !== WebSocket.OPEN) {
        return
    }
    let msg = JSON.stringify(data)
    // console.debug(msg)
    socket.send(msg);
}

const handlers = {
    "view/reload": function (params) {
        console.debug("Reloading page...")

        if (window.location.hash) {
            // Clear the url hash before reloading, this will prevent us from losing our scroll state on reload.
            // see https://github.com/swyddfa/esbonio/issues/788
            //
            // Can't be the empty string though, as that will cause the browser to jump to the top of the page!
            window.location.hash = '_'
        }
        window.location.reload()
    },
    "view/scroll": (params) => { scrollViewTo(params.uri, params.line) }
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
    syncScrollPosition()
})

let attempt = 0

function connect() {
    attempt += 1
    console.debug(`Connecting to '${wsUrl}' (attempt: ${attempt})...`)

    let newSocket = new WebSocket(wsUrl);
    newSocket.binaryType = 'arraybuffer'

    // Connection opened
    newSocket.addEventListener("open", (event) => {
        console.log("Connected.")
        socket = newSocket

        const entries = performance.getEntriesByType("navigation")
        if (entries.length === 0) {
        console.log('Unable to determine navigation type')
            setTimeout(syncScrollPosition, 50)
            return
        }

        if (entries.length > 1) {
        console.log("More than one navigation event to choose from!")
        }

        // Only sync the scroll position if the page was not reloaded
        // https://github.com/swyddfa/esbonio/issues/933
        if (entries[0].type !== 'reload') {
            setTimeout(syncScrollPosition, 50)
        }
    });

    // Listen for messages
    newSocket.addEventListener("message", (event) => {
        let message

        if (event.data instanceof ArrayBuffer) {
            let buf = new Uint8Array(event.data)
            message = JSON.parse(textDecoder.decode(buf))
        } else {
            message = JSON.parse(event.data)
        }
        handle(message)
    });

    // Connection closed
    newSocket.addEventListener("close", (event) => {
        console.log("Disconnected.")
        setTimeout(connect, 1000)
    })
}

function main() {
    connect()

    if (showMarkers) {
        renderLineMarkers()
    }

    rewriteInternalLinks(wsUrl)

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
