(function() {
  var state = window.__antaMermaidZoom || {}
  window.__antaMermaidZoom = state

  function getMermaidSource(sourceElement) {
    if (sourceElement instanceof HTMLTextAreaElement) {
      return sourceElement.value.trim()
    }

    if (sourceElement instanceof HTMLTemplateElement) {
      return sourceElement.content.textContent.trim()
    }

    return sourceElement.textContent.trim()
  }

  function findMermaidDiagram(sourceElement) {
    var element = sourceElement.nextElementSibling

    while (element) {
      if (element.classList.contains("mermaid")) {
        return element
      }

      element = element.nextElementSibling
    }

    return null
  }

  function initializeMermaidZoom() {
    document.querySelectorAll(".mermaid-zoom-source").forEach(function(sourceElement) {
      var diagram = findMermaidDiagram(sourceElement)

      if (!diagram || diagram.dataset.zoomReady) {
        return
      }

      var source = getMermaidSource(sourceElement)
      var title = sourceElement.dataset.title || "Mermaid diagram"

      diagram.dataset.zoomReady = "true"
      diagram.classList.add("mermaid-zoom-target")
      diagram.tabIndex = 0
      diagram.setAttribute("role", "button")
      diagram.setAttribute("aria-label", "Open " + title + " full screen")
      diagram.title = "Open full screen"

      diagram.addEventListener("click", function(event) {
        if (event.target instanceof Element && event.target.closest("a")) {
          return
        }

        openMermaidZoom(source, title)
      })

      diagram.addEventListener("keydown", function(event) {
        if (event.key !== "Enter" && event.key !== " ") {
          return
        }

        event.preventDefault()
        openMermaidZoom(source, title)
      })
    })
  }

  function scheduleMermaidZoomInit() {
    initializeMermaidZoom()
    window.requestAnimationFrame(initializeMermaidZoom)
    window.setTimeout(initializeMermaidZoom, 100)
  }

  function waitForMermaid() {
    return new Promise(function(resolve, reject) {
      var attempts = 0

      function check() {
        if (window.mermaid && typeof window.mermaid.render === "function") {
          resolve(window.mermaid)
          return
        }
        attempts += 1
        if (attempts > 100) {
          reject(new Error("Mermaid renderer is not available"))
          return
        }
        window.setTimeout(check, 100)
      }

      check()
    })
  }

  function enableDragScroll(viewport) {
    var active = false
    var startX = 0
    var startY = 0
    var scrollLeft = 0
    var scrollTop = 0

    viewport.addEventListener("pointerdown", function(event) {
      active = true
      startX = event.clientX
      startY = event.clientY
      scrollLeft = viewport.scrollLeft
      scrollTop = viewport.scrollTop
      viewport.setPointerCapture(event.pointerId)
    })

    viewport.addEventListener("pointermove", function(event) {
      if (!active) {
        return
      }
      viewport.scrollLeft = scrollLeft - event.clientX + startX
      viewport.scrollTop = scrollTop - event.clientY + startY
    })

    viewport.addEventListener("pointerup", function(event) {
      active = false
      viewport.releasePointerCapture(event.pointerId)
    })
  }

  function openMermaidZoom(source, title) {
    waitForMermaid().then(function(mermaid) {
      var overlay = document.createElement("div")
      var panel = document.createElement("div")
      var toolbar = document.createElement("div")
      var titleElement = document.createElement("div")
      var viewport = document.createElement("div")
      var content = document.createElement("div")
      var scale = 1

      function makeButton(label, action) {
        var button = document.createElement("button")
        button.className = "mermaid-zoom-control"
        button.type = "button"
        button.textContent = label
        button.addEventListener("click", action)
        return button
      }

      function applyScale() {
        content.style.transform = "scale(" + scale + ")"
        content.style.width = 100 / scale + "%"
      }

      overlay.className = "mermaid-zoom-overlay"
      panel.className = "mermaid-zoom-panel"
      toolbar.className = "mermaid-zoom-toolbar"
      titleElement.className = "mermaid-zoom-title"
      viewport.className = "mermaid-zoom-viewport"
      content.className = "mermaid-zoom-content"

      titleElement.textContent = title || "Mermaid diagram"
      toolbar.append(
        titleElement,
        makeButton("-", function() {
          scale = Math.max(.5, scale - .25)
          applyScale()
        }),
        makeButton("+", function() {
          scale = Math.min(4, scale + .25)
          applyScale()
        }),
        makeButton("100%", function() {
          scale = 1
          applyScale()
        }),
        makeButton("Close", function() {
          overlay.remove()
        }),
      )
      viewport.append(content)
      panel.append(toolbar, viewport)
      overlay.append(panel)
      document.body.append(overlay)

      overlay.addEventListener("click", function(event) {
        if (event.target === overlay) {
          overlay.remove()
        }
      })
      document.addEventListener("keydown", function closeOnEscape(event) {
        if (!overlay.isConnected) {
          document.removeEventListener("keydown", closeOnEscape)
          return
        }
        if (event.key === "Escape") {
          overlay.remove()
          document.removeEventListener("keydown", closeOnEscape)
        }
      })

      mermaid.render("__mermaid_zoom_" + Date.now(), source).then(function(result) {
        content.innerHTML = result.svg
        applyScale()
        enableDragScroll(viewport)
      })
    })
  }

  if (!state.documentSubscriptionInstalled && window.document$) {
    state.documentSubscriptionInstalled = true
    window.document$.subscribe(scheduleMermaidZoomInit)
  }

  if (!state.domReadyListenerInstalled) {
    state.domReadyListenerInstalled = true
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", scheduleMermaidZoomInit)
    } else {
      scheduleMermaidZoomInit()
    }
  } else {
    scheduleMermaidZoomInit()
  }
})()
