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

      var nestedDiagram = element.querySelector(".mermaid")
      if (nestedDiagram) {
        return nestedDiagram
      }

      element = element.nextElementSibling
    }

    return null
  }

  function getMermaidClickTargets(source) {
    var clickTargets = []
    var clickPattern = /^\s*click\s+([A-Za-z0-9_-]+)/gm
    var match

    while ((match = clickPattern.exec(source)) !== null) {
      clickTargets.push(match[1])
    }

    return clickTargets
  }

  function isLinkClick(event) {
    var path = typeof event.composedPath === "function" ? event.composedPath() : []

    if (!path.length && event.target) {
      path = [event.target]
    }

    return path.some(function(target) {
      if (!(target instanceof Element)) {
        return false
      }

      return Boolean(target.closest("a"))
    })
  }

  function createZoomButton(source, title, sourceElement, diagram) {
    var button = document.createElement("button")
    button.className = "mermaid-zoom-open"
    button.type = "button"
    button.textContent = "Zoom"
    button.setAttribute("aria-label", "Open " + title + " full screen")
    button.title = "Open full screen"
    button.addEventListener("click", function() {
      openMermaidZoom(source, title, button)
    })
    diagram.insertAdjacentElement("beforebegin", button)
    sourceElement.zoomButton = button
  }

  function initializeMermaidZoom() {
    document.querySelectorAll(".mermaid-zoom-source").forEach(function(sourceElement) {
      var diagram = findMermaidDiagram(sourceElement)

      if (!diagram) {
        return
      }

      if (sourceElement.dataset.zoomReady && sourceElement.zoomDiagram === diagram) {
        return
      }

      var source = getMermaidSource(sourceElement)
      var title = sourceElement.dataset.title || "Mermaid diagram"
      var clickTargets = getMermaidClickTargets(source)
      var hasNavigationTargets = clickTargets.length > 0

      if (sourceElement.zoomButton) {
        sourceElement.zoomButton.remove()
      }

      sourceElement.dataset.zoomReady = "true"
      sourceElement.zoomDiagram = diagram
      diagram.dataset.zoomReady = "true"
      diagram.classList.add("mermaid-zoom-target")
      createZoomButton(source, title, sourceElement, diagram)

      if (!hasNavigationTargets) {
        diagram.classList.add("mermaid-zoom-target--clickable")
        diagram.tabIndex = 0
        diagram.setAttribute("role", "button")
        diagram.setAttribute("aria-label", "Open " + title + " full screen")
        diagram.title = "Open full screen"

        diagram.addEventListener("click", function(event) {
          if (isLinkClick(event)) {
            return
          }

          openMermaidZoom(source, title, diagram)
        })

        diagram.addEventListener("keydown", function(event) {
          if (isLinkClick(event)) {
            return
          }

          if (event.key !== "Enter" && event.key !== " ") {
            return
          }

          event.preventDefault()
          openMermaidZoom(source, title, diagram)
        })
      }
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
    var activePointerId = null
    var startX = 0
    var startY = 0
    var scrollLeft = 0
    var scrollTop = 0

    function isInteractiveTarget(event) {
      return event.target instanceof Element && Boolean(event.target.closest("a, button, input, select, textarea, [role='button']"))
    }

    viewport.addEventListener("pointerdown", function(event) {
      if (event.button !== 0 || isInteractiveTarget(event)) {
        return
      }

      active = true
      activePointerId = event.pointerId
      startX = event.clientX
      startY = event.clientY
      scrollLeft = viewport.scrollLeft
      scrollTop = viewport.scrollTop
      viewport.setPointerCapture(event.pointerId)
    })

    viewport.addEventListener("pointermove", function(event) {
      if (!active || event.pointerId !== activePointerId) {
        return
      }
      viewport.scrollLeft = scrollLeft - event.clientX + startX
      viewport.scrollTop = scrollTop - event.clientY + startY
    })

    viewport.addEventListener("pointerup", function(event) {
      if (!active || event.pointerId !== activePointerId) {
        return
      }

      active = false
      activePointerId = null
      viewport.releasePointerCapture(event.pointerId)
    })

    viewport.addEventListener("pointercancel", function(event) {
      if (!active || event.pointerId !== activePointerId) {
        return
      }

      active = false
      activePointerId = null
    })
  }

  function openMermaidZoom(source, title, invokingElement) {
    if (state.pageLeaving) {
      return
    }

    if (typeof state.closeActiveMermaidZoom === "function") {
      state.closeActiveMermaidZoom(false)
    }

    waitForMermaid().then(function(mermaid) {
      if (state.pageLeaving) {
        return
      }

      var overlay = document.createElement("div")
      var panel = document.createElement("div")
      var toolbar = document.createElement("div")
      var titleElement = document.createElement("div")
      var viewport = document.createElement("div")
      var content = document.createElement("div")
      var scale = 1
      var closed = false
      var titleId = "__mermaid_zoom_title_" + Date.now()

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

      function getToolbarControls() {
        return Array.prototype.slice.call(panel.querySelectorAll(
          "a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex='-1'])"
        )).filter(function(element) {
          return element.offsetParent !== null
        })
      }

      function closeZoom(restoreFocus) {
        if (closed) {
          return
        }

        if (restoreFocus !== false) {
          restoreFocus = true
        }

        closed = true
        state.closeActiveMermaidZoom = null
        overlay.removeEventListener("click", closeOnBackdrop)
        document.removeEventListener("keydown", handleOverlayKeydown)
        overlay.remove()

        if (restoreFocus && invokingElement && invokingElement.isConnected && typeof invokingElement.focus === "function") {
          invokingElement.focus()
        }
      }

      function closeOnBackdrop(event) {
        if (event.target === overlay) {
          closeZoom()
        }
      }

      function handleOverlayKeydown(event) {
        if (event.key === "Escape") {
          event.preventDefault()
          closeZoom()
          return
        }

        if (event.key !== "Tab") {
          return
        }

        var toolbarControls = getToolbarControls()

        if (!toolbarControls.length) {
          event.preventDefault()
          panel.focus()
          return
        }

        var firstElement = toolbarControls[0]
        var lastElement = toolbarControls[toolbarControls.length - 1]

        if (!panel.contains(document.activeElement)) {
          event.preventDefault()
          if (event.shiftKey) {
            lastElement.focus()
          } else {
            firstElement.focus()
          }
        } else if (event.shiftKey && document.activeElement === firstElement) {
          event.preventDefault()
          lastElement.focus()
        } else if (!event.shiftKey && document.activeElement === lastElement) {
          event.preventDefault()
          firstElement.focus()
        }
      }

      overlay.className = "mermaid-zoom-overlay"
      panel.className = "mermaid-zoom-panel"
      toolbar.className = "mermaid-zoom-toolbar"
      titleElement.className = "mermaid-zoom-title"
      viewport.className = "mermaid-zoom-viewport"
      content.className = "mermaid-zoom-content"

      panel.tabIndex = -1
      panel.setAttribute("role", "dialog")
      panel.setAttribute("aria-modal", "true")
      panel.setAttribute("aria-labelledby", titleId)
      titleElement.id = titleId
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
          closeZoom()
        }),
      )
      viewport.append(content)
      panel.append(toolbar, viewport)
      overlay.append(panel)
      document.body.append(overlay)
      state.closeActiveMermaidZoom = closeZoom

      overlay.addEventListener("click", closeOnBackdrop)
      document.addEventListener("keydown", handleOverlayKeydown)

      var initialFocusElement = toolbar.querySelector("button:not([disabled])")
      if (initialFocusElement) {
        initialFocusElement.focus()
      } else {
        panel.focus()
      }

      mermaid.render("__mermaid_zoom_" + Date.now(), source).then(function(result) {
        content.innerHTML = result.svg
        if (typeof result.bindFunctions === "function") {
          result.bindFunctions(content)
        } else if (typeof result.fn === "function") {
          result.fn(content)
        }
        applyScale()
        enableDragScroll(viewport)
      }).catch(function(error) {
        content.textContent = "Unable to render diagram."
        console.error("Mermaid zoom render failed:", error)
      })
    }).catch(function(error) {
      console.error("Mermaid zoom failed to initialize:", error)
    })
  }

  if (!state.documentSubscriptionInstalled && window.document$) {
    state.documentSubscriptionInstalled = true
    window.document$.subscribe(function() {
      if (typeof state.closeActiveMermaidZoom === "function") {
        state.closeActiveMermaidZoom(false)
      }
      scheduleMermaidZoomInit()
    })
  }

  if (!state.pageHideListenerInstalled) {
    state.pageHideListenerInstalled = true
    window.addEventListener("pageshow", function() {
      state.pageLeaving = false
    })
    window.addEventListener("pagehide", function() {
      state.pageLeaving = true
      if (typeof state.closeActiveMermaidZoom === "function") {
        state.closeActiveMermaidZoom(false)
      }
    })
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
