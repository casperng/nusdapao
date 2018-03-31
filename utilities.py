
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


def build_view_all_orders_string(deliveries):
    if not deliveries:
        return "There are no active deliveries now"
    result = ""
    for code, delivery in deliveries.items():
        delivery['price'] = cents_to_dollars_string(delivery['price'])
        delivery['markup'] = cents_to_dollars_string(delivery['markup'])
        result +=       'Delivery {id} for {dish} from {location} by {username}\n' \
				        'Price: {price}\n' \
						'Markup: {markup}\n' \
						'Closing: {closes}\n' \
						'Arriving: {arrival}\n' \
						'Pickup: {pickup}\n'.format(**delivery, id=code)
        result += build_view_orders_string(delivery['orders']) + '\n'
    return result


def build_date_string(datetime):
    return datetime.strftime("%H:%M %d/%m/%y")


def cents_to_dollars_string(cents):
    return '{:.2f}'.format(cents/100)

def pop_all_keys(dct):
    for key in list(dct.keys()):
        del dct[key]
