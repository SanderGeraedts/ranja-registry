import time
import board
from digitalio import DigitalInOut, Direction, Pull
import os
import ssl
import socketpool
import wifi
import adafruit_minimqtt.adafruit_minimqtt as MQTT

# add these in settings.toml
ssid = os.getenv("CIRCUITPY_WIFI_SSID")
password = os.getenv("CIRCUITPY_WIFI_PASSWORD")

print(f"Connecting to {ssid}")
wifi.radio.connect(ssid, password)
print(f"Connected to {ssid}!")

feed = "inventory/ranja"

# Wiring is from pin to ground via NC on the switch
pos_1 = DigitalInOut(board.GP13)
pos_2 = DigitalInOut(board.GP12)
pos_3 = DigitalInOut(board.GP11)
pos_4 = DigitalInOut(board.GP10)

pos_1.direction = Direction.INPUT
pos_2.direction = Direction.INPUT
pos_3.direction = Direction.INPUT
pos_4.direction = Direction.INPUT

pos_1.pull = Pull.UP
pos_2.pull = Pull.UP
pos_3.pull = Pull.UP
pos_4.pull = Pull.UP

prev_amount = 0

# Define callback methods which are called when events occur
# pylint: disable=unused-argument, redefined-outer-name
def connected(client, userdata, flags, rc):
    # This function will be called when the client is connected
    # successfully to the broker.
    print("Connected to MQTT!")


def disconnected(client, userdata, rc):
    # This method is called when the client is disconnected
    print("Disconnected from MQTT!")


# Create a socket pool
pool = socketpool.SocketPool(wifi.radio)
ssl_context = ssl.create_default_context()

# Set up a MiniMQTT Client
mqtt_client = MQTT.MQTT(
    broker=os.getenv('BROKER'),
    port=os.getenv('PORT'),
    socket_pool=pool,
    ssl_context=ssl_context,
)

# Setup the callback methods above
mqtt_client.on_connect = connected
mqtt_client.on_disconnect = disconnected

def getAmountOfBottles():
    amount = 0
    if pos_1.value:
        amount = amount + 1
    if pos_2.value:
        amount = amount + 1
    if pos_3.value:
        amount = amount + 1
    if pos_4.value:
        amount = amount + 1
    return amount

# Connect the client to the MQTT broker.
print("Connecting to MQTT...")
mqtt_client.connect()

while True:
    # Poll the message queue
    mqtt_client.loop(timeout=1)
    
    curr_amount = getAmountOfBottles()
    
    if prev_amount != curr_amount:
        print(f"Amount of bottles: {curr_amount}")
        try:
            mqtt_client.publish(feed, curr_amount)
            prev_amount = curr_amount
        except:
            print("Oepsie poepsie, iets is stukkiewukkie...")
            wifi.reset()
            mqtt_client.reconnect()
            continue

    time.sleep(1) # sleep for debounce