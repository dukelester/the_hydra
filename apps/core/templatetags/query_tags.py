from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def page_query(context, page):
    """Keep current filters when changing page."""
    request = context.get("request")
    if request is None:
        return f"?page={page}"
    params = request.GET.copy()
    params["page"] = page
    return "?" + params.urlencode()
