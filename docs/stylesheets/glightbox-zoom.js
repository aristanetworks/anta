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

    let active = false
    let dragged = false
    let offsetX = 0
    let offsetY = 0
    let startX = 0
    let startY = 0
    let suppressClick = false

    function reset() {
      active = false
      dragged = false
      offsetX = 0
      offsetY = 0
      image.classList.remove("anta-dragging")
      image.style.transform = ""
    }

    image.dataset.antaZoomReady = "true"
    image.classList.add("anta-zoomable")

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
      if (!slide.classList.contains("zoomed") || event.button !== 0) {
        return
      }

      active = true
      dragged = false
      startX = event.clientX - offsetX
      startY = event.clientY - offsetY
      image.setPointerCapture(event.pointerId)
    })

    image.addEventListener("pointermove", function(event) {
      if (!active) {
        return
      }

      const nextX = event.clientX - startX
      const nextY = event.clientY - startY
      if (Math.abs(nextX - offsetX) > 3 || Math.abs(nextY - offsetY) > 3) {
        dragged = true
        image.classList.add("anta-dragging")
      }
      offsetX = nextX
      offsetY = nextY
      image.style.transform = `translate3d(${offsetX}px, ${offsetY}px, 0)`
    })

    image.addEventListener("pointerup", function(event) {
      if (!active) {
        return
      }

      active = false
      image.classList.remove("anta-dragging")
      image.releasePointerCapture(event.pointerId)
      if (dragged) {
        suppressClick = true
        window.setTimeout(function() {
          suppressClick = false
        }, 0)
      }
    })
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
