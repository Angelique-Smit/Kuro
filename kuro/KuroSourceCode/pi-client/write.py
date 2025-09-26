import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522

reader = SimpleMFRC522()

try:
	text = input('new data')
	print("now place your tag to write")
	reader.write(text)
	print("written")
finally:
	GPIO.cleanup()


