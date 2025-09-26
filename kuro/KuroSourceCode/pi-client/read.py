from time import sleep
import sys
from mfrc522 import SimpleMFRC522
import RPi.GPIO as GPIO

reader = SimpleMFRC522()

try:
	while True:
		print("Place your RFID tag near the reader...")

		id, text = reader.read()
		print("ID: %s\nText: %s" % (id,text))
		print(f"ID: {id}")
		print(f"Text: {text}")
		sleep(5)
except KeyboardInterrupt:
	GPIO.cleanup()
	raise
