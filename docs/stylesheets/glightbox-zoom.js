(function() {
  "use strict"

  function addFallbackZoom(image) {
    if (!image.isConnected || image.classList.contains("zoomable") || image.dataset.antaZoomReady) {
      return
    }

    const slide = image.closest(".gslide")
    if (!slide) {
      return
    }

    let activePointerId = null
    let dragged = false
    let offsetX = 0
    let offsetY = 0
    let startX = 0
    let startY = 0
    let dragOriginX = 0
    let dragOriginY = 0
    let suppressClick = false

    function reset() {
      activePointerId = null
      dragged = false
      offsetX = 0
      offsetY = 0
      image.classList.remove("anta-dragging")
      image.style.transform = ""
    }

    image.dataset.antaZoomReady = "true"
    image.classList.add("anta-zoomable")
    image.draggable = false

    image.addEventListener("dragstart", function(event) {
      event.preventDefault()
    })

    image.addEventListener("click", function() {
      if (suppressClick) {
        return
      }

      if (slide.classList.contains("zoomed")) {
        slide.classList.remove("zoomed")
        reset()
      } else {
        slide.classList.add("zoomed")
      }
    })

    image.addEventListener("pointerdown", function(event) {
      if (!slide.classList.contains("zoomed") || event.button !== 0 || activePointerId !== null) {
        return
      }

      activePointerId = event.pointerId
      dragged = false
      suppressClick = false
      dragOriginX = offsetX
      dragOriginY = offsetY
      startX = event.clientX - offsetX
      startY = event.clientY - offsetY
      event.preventDefault()
      image.setPointerCapture(event.pointerId)
    })

    image.addEventListener("pointermove", function(event) {
      if (event.pointerId !== activePointerId) {
        return
      }

      const nextX = event.clientX - startX
      const nextY = event.clientY - startY
      if (Math.abs(nextX - dragOriginX) > 3 || Math.abs(nextY - dragOriginY) > 3) {
        dragged = true
        image.classList.add("anta-dragging")
      }
      if (!dragged) {
        return
      }
      event.preventDefault()
      offsetX = nextX
      offsetY = nextY
      image.style.transform = `translate3d(${offsetX}px, ${offsetY}px, 0)`
    })

    function finishPointer(event) {
      if (event.pointerId !== activePointerId) {
        return
      }

      activePointerId = null
      image.classList.remove("anta-dragging")
      if (image.hasPointerCapture(event.pointerId)) {
        image.releasePointerCapture(event.pointerId)
      }
      if (dragged) {
        suppressClick = true
      }
    }

    image.addEventListener("pointerup", finishPointer)
    image.addEventListener("pointercancel", finishPointer)
  }

  function inspect(image) {
    window.setTimeout(function() {
      addFallbackZoom(image)
    }, 0)
  }

  function watch(image) {
    if (image.complete) {
      inspect(image)
    } else {
      image.addEventListener("load", function() {
        inspect(image)
      }, { once: true })
    }
  }

  const observer = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
      mutation.addedNodes.forEach(function(node) {
        if (!(node instanceof Element)) {
          return
        }
        if (node.matches(".gslide-image img")) {
          watch(node)
        }
        node.querySelectorAll(".gslide-image img").forEach(watch)
      })
    })
  })

  observer.observe(document.body, { childList: true, subtree: true })
})()
