import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522

reader = SimpleMFRC522()

try:
	text = "delete"
	reader.write(text)
	print("written")
finally:
	GPIO.cleanup()