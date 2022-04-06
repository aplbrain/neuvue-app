from django import template

register = template.Library()

@register.inclusion_tag('reusable_components/confirm_modal.html')
def create_modal(column):
    # Update syntax when you implement for delete
    return {
        "column": column.lower(),
        "modal_id": "confirmUpdate" + column.capitalize() + "Modal",
        "confirm_text_id": "confirmUpdate" + column.capitalize() + "ModalBody",
        "button_id": "update_" + column.lower() + "_modal_button",
        "button_value": column.lower(),
    }

@register.inclusion_tag('reusable_components/trigger_modal.html')
def trigger_modal(column):
    return {
        "column": column.lower(),
        "modal_id": "confirmUpdate" + column.capitalize() + "Modal",
        "confirm_text_id": "confirmUpdate" + column.capitalize() + "ModalBody",
        "button_id": column.lower() + "_button",
    }