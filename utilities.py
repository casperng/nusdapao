
def build_view_orders_string(orders):
    ORDER_MESSAGE_TEMPLATE = "The orders are:\n"
    ORDER_ITEM_MESSAGE_TEMPLATE = "{qty} ({remarks}) - {username} [{method}]\n"
    ORDER_ITEM_MESSAGE_NO_REMARKS_TEMPLATE = "{qty} - {username} [{method}]\n"

    reply = ORDER_MESSAGE_TEMPLATE
    for order in orders:
        if order['remarks']:
            reply += ORDER_ITEM_MESSAGE_TEMPLATE.format(**order)
        else:
            reply += ORDER_ITEM_MESSAGE_NO_REMARKS_TEMPLATE.format(**order)

    return reply


def build_date_string(datetime):
    return datetime.strftime("%H:%M %d/%m/%y")


def pop_all_keys(dct):
    for key in list(dct.keys()):
        del dct[key]
