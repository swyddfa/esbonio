document.body.addEventListener("htmx:configRequest", function (event) {
  let updatedPath = event.detail.path.replace(/:([A-Za-z0-9_]+)/g, function (_match, name) {
    let value = event.detail.parameters[name]
    delete event.detail.parameters[name]

    if (!value) {
      return "not-found"
    }

    return value
  })

  event.detail.path = updatedPath
  console.debug(event)
})

function syncDropdowns(source, others) {
  let category = source.dataset.category
  let id = source.options[source.selectedIndex].dataset.id
  console.debug('Syncing dropdowns')

  others.forEach(dropdown => {
    dropdown.selectedIndex = source.selectedIndex
    dropdown.dispatchEvent(new Event('change'))
  })

  return [category, id]
}

function syncURL(key, value) {
  let params = new URLSearchParams(window.location.search)
  params.set(key, value)

  let newURL = window.location.origin + window.location.pathname + '?' + params.toString()
  window.history.pushState({ path: newURL }, '', newURL)
}

let dropdowns = document.querySelectorAll('select[data-kind="relevant-to"]')
let currentlySyncing = false

// Maps categories to the corresponding dropdowns
let dropdownMap = new Map()
dropdowns.forEach(dropdown => {
  let category = dropdown.dataset.category
  if (dropdownMap.has(category)) {
    dropdownMap.get(category).push(dropdown)
  } else {
    dropdownMap.set(category, [dropdown])
  }
})
console.debug(dropdownMap)

let urlParams = new URLSearchParams(window.location.search)
for (const [_, dropdowns] of dropdownMap.entries()) {

  // Ensure user's selection is propagated to all dropdowns within a category.
  dropdowns.forEach(d => {
    d.addEventListener('change', (evt) => {
      if (currentlySyncing) {
        return
      }

      currentlySyncing = true
      scrollTarget = evt.target

      const [key, value] = syncDropdowns(evt.target, dropdowns)
      syncURL(key, value)
      // evt.target.scrollIntoView() - needs more thought.

      currentlySyncing = false
    })
  })
}

// Set dropdowns based on URL parameters.
document.addEventListener('DOMContentLoaded', () => {
  for (const [category, dropdowns] of dropdownMap.entries()) {
    let defaultIndex = 0

    if (urlParams.has(category)) {
      let options = Array.from(dropdowns[0].options)
      let ids = options.map(o => o.dataset.id)
      let id = urlParams.get(category)

      let idx = ids.indexOf(id)
      if (idx >= 0) {
        defaultIndex = idx
      }
    }

    dropdowns[0].selectedIndex = defaultIndex
    currentlySyncing = true
    syncDropdowns(dropdowns[0], dropdowns)
    currentlySyncing = false
  }
})
