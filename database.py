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
		except pg8000.Connection.Error:
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
		SELECT * FROM orders
		with deliveryid = %s
		""",
		[deliveryid]
	)
	results = cursor.fetchall()
	CONN.commit()
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