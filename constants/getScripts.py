SCROLL_BODY = """
    let e = arguments[0];
    while (e && e !== document.body) {
      const s = getComputedStyle(e);
      if ((s.overflowY==='auto'||s.overflowY==='scroll') && e.scrollHeight>e.clientHeight) return e;
      e = e.parentElement;
    }
    return document.scrollingElement;
    """
SCROLL_INTO_VIEW = "arguments[0].scrollIntoView({block:'center'});"
SMOOTH_SCROLL = "arguments[0].scrollTop = arguments[0].scrollTop + Math.floor(arguments[0].clientHeight*0.65);"
SCROLL_TO_BOTTOM = "const el=arguments[0]; return Math.abs(el.scrollHeight - el.scrollTop - el.clientHeight) < 4;"