// This file gets injected into html pages built with Sphinx (assuming it's enabled of course!)
// which allows the webpage to talk with the preview server and coordinate details such as refreshes
// and page scrolling.

const queryString = window.location.search;
const queryParams = new URLSearchParams(queryString);
const ws = parseInt(queryParams.get("ws")); // is the number 123
console.debug(`Connecting to websocket server on port: ${ws}...`)

const socket = new WebSocket(`ws://localhost:${ws}`);
const handlers = {
    "view/reload": function(params) {
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

// Connection opened
socket.addEventListener("open", (event) => {
    console.debug("Connected.")
    // let data = { jsonrpc: "2.0", id: 2,  method: "hello/world", params: { x: 1 }}
    // socket.send(JSON.stringify(data));
});

// Listen for messages
socket.addEventListener("message", (event) => {
  handle(JSON.parse(event.data))
});
