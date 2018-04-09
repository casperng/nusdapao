import pytz

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
        delivery['closes'] = build_date_string(delivery['closes'])
        delivery['arrival'] = build_date_string(delivery['arrival'])
        result +=       'Delivery {id} for {dish} from {location} by {username} {usertag}\n' \
				        'Price: ${price} (+${markup} delivery fee)\n' \
						'Closing: {closes}\n' \
						'Arriving: {arrival}\n' \
						'Pickup: {pickup}\n'.format(**delivery, id=code)
        result += build_view_orders_string(delivery['orders']) + '\n'
    return result


def build_date_string(datetime):
    return datetime.astimezone(tz=pytz.timezone('Asia/Singapore')).strftime("%H:%M (%a)")


def cents_to_dollars_string(cents):
    return '{:.2f}'.format(cents/100)


def pop_all_keys(dct):
    for key in list(dct.keys()):
        del dct[key]


def only_allow_private_message(fn):
    def wrapped(bot, update, *args, **kwargs):
        if update.message.from_user.id != update.message.chat_id:
            return
        return fn(bot, update, *args, **kwargs)
    return wrapped

