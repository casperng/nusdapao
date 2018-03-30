import os
import pg8000

CONN = pg8000.connect(
	database=os.environ.get('DATABASE_NAME'),
	user=os.environ.get('DATABASE_USER'),
	password=os.environ.get('DATABASE_PASSWORD'),
	host=os.environ.get('DATABASE_HOST'),
	# port=os.environ.get('DATABASE_PORT')
)

def with_rollback(fn):
	def wrapped(*args, **kwargs):
		try:
			return fn(*args, **kwargs)
		except pg8000.Error:
			CONN.rollback()
	return wrapped

@with_rollback
def start_delivery(details):
	cursor = CONN.cursor()
	cursor.execute(
		"""
		INSERT INTO deliveries (chat, userid, location, closes, arrival, pickup)
		VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
		""",
		[details['chat'], details['user'], details['location'], details['closes'], details['arrival'], details['pickup']]
	)
	results = cursor.fetchall()
	CONN.commit()
	cursor.close()

	deliveryId = results[0][0]
	return deliveryId

@with_rollback
def is_valid_delivery_id(deliveryId):
	cursor = CONN.cursor()
	cursor.execute(
		"""
		SELECT COUNT(*) from deliveries 
		WHERE id = %s
		""",
		[deliveryId]
	)
	results = cursor.fetchall()
	cursor.close()

	count = results[0][0]
	return count > 0

@with_rollback
def is_open_delivery_id(deliveryId):
	cursor = CONN.cursor()
	cursor.execute(
		"""
		SELECT COUNT(*) from deliveries 
		WHERE id = %s AND NOW() < closes
		""",
		[deliveryId]
	)
	results = cursor.fetchall()
	cursor.close()

	count = results[0][0]
	return count > 0

@with_rollback
def add_order(details):
	cursor = CONN.cursor()
	cursor.execute(
		"""
		INSERT INTO orders (deliveryId, userid, username, qty, method, remarks)
		VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
		""",
		[details['deliveryId'], details['userid'], details['username'], details['qty'], details['method'], details['remarks']]
	)
	results = cursor.fetchall()
	CONN.commit()
	cursor.close()

	deliveryId = results[0][0]
	return deliveryId

@with_rollback
def get_orders(deliveryid):
	cursor = CONN.cursor()
	cursor.execute(
		"""
		SELECT userid, username, method, remarks, qty FROM orders
		WHERE deliveryid = %s
		""",
		[deliveryid]
	)
	results = cursor.fetchall()
	cursor.close()

	def repack(row):
		userid, username, method, remarks, qty = row
		return {
			'userid': userid,
			'username': username,
			'method': method,
			'remarks': remarks,
			'qty': qty
		}

	return list(map(repack, results))

@with_rollback
def get_user_orders(deliveryid, userid):
	cursor = CONN.cursor()
	cursor.execute(
		"""
		SELECT id, username, method, remarks, qty FROM orders
		WHERE deliveryid = %s AND userid = %s
		""",
		[deliveryid, userid]
	)
	results = cursor.fetchall()
	cursor.close()

	def repack(row):
		orderid, username, method, remarks, qty = row
		return {
			'id': orderid,
			'username': username,
			'method': method,
			'remarks': remarks,
			'qty': qty
		}

	return list(map(repack, results))

@with_rollback
def get_user_deliveries(userid):
	cursor = CONN.cursor()
	cursor.execute(
		"""
        SELECT id, location, closes, arrival, pickup FROM deliveries
        WHERE userid = %s
        """,
		[userid]
	)
	results = cursor.fetchall()
	cursor.close()

	def repack(row):
		deliveryid, location, closes, arrival, pickup = row
		return {
			'deliveryid': deliveryid,
			'location': location,
			'closes': closes,
			'arrival': arrival,
			'pickup': pickup
		}

	return list(map(repack, results))

@with_rollback
def close_order_for_delivery(userid, deliveryid):
	cursor = CONN.cursor()
	cursor.execute(
		"""
        UPDATE deliveries
        SET closes = NOW() 
        WHERE id = %s AND userid = %s
        """,
		[deliveryid, userid]
	)
	results = cursor.fetchall()
	CONN.commit()
	cursor.close()
	return True

@with_rollback
def delete_user_order(userid, orderid):
	cursor = CONN.cursor()
	cursor.execute(
		"""
		DELETE FROM orders
		WHERE id = %s AND userid = %s
		""",
		[orderid, userid]
	)
	results = cursor.fetchall()
	CONN.commit()
	cursor.close()
	return True

@with_rollback
def get_users(deliveryid):
	cursor = CONN.cursor()
	cursor.execute(
		"""
        SELECT DISTINCT userid FROM orders
        WHERE deliveryid = %s
        """,
		[deliveryid]
	)
	results = cursor.fetchall()
	cursor.close()

	return [row[0] for row in results]

@with_rollback
def is_order_open(deliveryid):
	cursor = CONN.cursor()
	cursor.execute(
		"""
        SELECT COUNT(*) FROM deliveries
        WHERE id = %s  
        """,
		[deliveryid]
	)
	results = cursor.fetchall()
	cursor.close()

	return results

@with_rollback
def has_active_deliveries():
	cursor = CONN.cursor()
	cursor.execute(
		"""
		SELECT COUNT(*) FROM deliveries 
		WHERE arrival > NOW()
		"""
	)
	results = cursor.fetchall()
	cursor.close()

	count = results[0][0]
	return count > 0