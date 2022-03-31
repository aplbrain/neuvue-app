from django import template

register = template.Library()

@register.inclusion_tag('reusable_components/confirm_modal.html')
def show_modal(column):
    # Update syntax when you implement for delete
    return {
        "column": column.lower(),
        "modal_id": "confirmUpdate" + column.capitalize() + "Modal",
        "confirm_text_id": "confirmUpdate" + column.capitalize() + "ModalBody",
        "text": column.lower(),
        "button_id": "update_" + column.lower() + "_modal_button",
        "button_value": column.lower()
    }
