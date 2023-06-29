export namespace Server {
  export const REQUIRED_PYTHON = "3.8.0"
}

export namespace Commands {
  export const OPEN_PREVIEW = "esbonio.preview.open"
  export const OPEN_PREVIEW_TO_SIDE = "esbonio.preview.openSide"
  export const PREVIEW_FILE = "esbonio.server.previewFile"

  export const RESTART_SERVER = "esbonio.server.restart"
}

/**
 * Events that are internal to the language client.
 */
export namespace Events {
  export const SERVER_START = "server/start"
  export const SERVER_STOP = "server/stop"
}

/**
 * JSON-RPC notifications that may be sent between client and server.
 */
export namespace Notifications {
  export const SCROLL_EDITOR = "editor/scroll"
  export const VIEW_SCROLL = "view/scroll"

  export const SPHINX_APP_CREATED = "sphinx/appCreated"
}
