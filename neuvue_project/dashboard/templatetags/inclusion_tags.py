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

@register.inclusion_tag('modals/flag_modal.html')
def flag_modal(task_id):
    return {
        "task_id": task_id
    }

@register.inclusion_tag('modals/remove_task_modal.html')
def remove_task_modal():
    return {}

@register.inclusion_tag('modals/timeout_modal.html')
def timeout_modal():
    return {}

@register.inclusion_tag('modals/confirm_selected_segments_modal.html')
def confirm_selected_segments_modal(number_of_selected_segments_expected):
    return {
        "number_of_selected_segments_expected": number_of_selected_segments_expected
    }