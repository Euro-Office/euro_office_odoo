#
# (c) Copyright Ascensio System SIA 2024
#

import json


def dump_for_inline_script(obj):
    """Serialize ``obj`` to JSON that is safe to embed inside a single-quoted
    JavaScript string in an inline <script> element.

    ``json.dumps`` escapes double quotes but does NOT escape single quotes or
    ``<``/``>``, so any user-controlled value (document title, user name,
    tokens, URLs) could terminate the JS string literal — or close the script
    element itself with ``</script>`` — and inject arbitrary JavaScript into
    the page. The template renders the result raw inside
    ``var config = JSON.parse('<t t-out="editorConfig" />');``.

    The escapes below are valid JavaScript/JSON string escapes, so the
    resulting string still parses to the same object after
    ``JSON.parse``.
    """
    return (
        json.dumps(obj, ensure_ascii=True)
        .replace("&", "\\u0026")
        .replace("'", "\\u0027")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
    )
