import os
import pg8000


CONN = pg8000.connect(
	database=os.environ.get('DATABASE_NAME'),
	user=os.environ.get('DATABASE_USER'),
	password=os.environ.get('DATABASE_PASSWORD'),
	host=os.environ.get('DATABASE_HOST'),
	# port=os.environ.get('DATABASE_PORT')
)


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


def has_active_deliveries():
	cursor = CONN.cursor()
	cursor.execute(
		"""
		SELECT COUNT(*) FROM deliveries 
		WHERE arrival > NOW()
		"""
	)
	results = cursor.fetchall()
	CONN.commit()
	cursor.close()

	count = results[0][0]
	return count > 0