from django import template

register = template.Library()

@register.inclusion_tag('reusable_components/confirm_modal.html')
def confirm_modal(column):
    return {
        "column": column.lower(),
        "capitalized_column": column.capitalize(),
        "modal_id": "confirmUpdate" + column.capitalize() + "Modal",
        "confirm_text_id": "confirmUpdate" + column.capitalize() + "ModalBody",
        "button_id": column.lower() + "-button",
    }

@register.inclusion_tag('reusable_components/metrics_card.html')
def metrics_card(title, value, color):
    return {
        "title": title,
        "value": value,
        "color": color     # should be a bootstrap color utility, e.g. primary, secondary
    }