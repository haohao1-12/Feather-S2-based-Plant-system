# you can get all the bundles from adafruit
import ssl
import wifi
import socketpool
import adafruit_requests as requests
import adafruit_bh1750
import analogio
import time
import adafruit_minimqtt.adafruit_minimqtt as MQTT

try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets in secrets.py, add them there!")
    raise

wifi.radio.connect(secrets["ssid"], secrets["password"])

# name of the topics
mqtt_topic1 = "sl7n21/temperature"
mqtt_topic2 = "sl7n21/moisture"
mqtt_topic3 = "sl7n21/light"

# Define callback methods which are called when events occur
def connect(mqtt_client, userdata, flags, rc):
    # This will be called when the mqtt_client is connected successfully to the broker.
    print("Connected to MQTT Broker")
    print("Flags: {0}\n RC: {1}".format(flags, rc))


def disconnect(mqtt_client, userdata, rc):
    # called when the mqtt_client disconnects
    print("Disconnected from MQTT Broker!")

def publish(mqtt_client, userdata, topic, pid):
    # This method is called when the mqtt_client publishes data to a feed.
    print("Published to {0} with PID {1}".format(topic, pid))

# Create a socket pool
pool = socketpool.SocketPool(wifi.radio)

# Set up a MiniMQTT Client
mqtt_client = MQTT.MQTT(

    broker="test.mosquitto.org",
    port=1883,
    username="none",
    password="non",
    socket_pool=pool,
    ssl_context=ssl.create_default_context(),
)

# Connect callback handlers to mqtt_client
mqtt_client.on_connect = connect
mqtt_client.on_disconnect = disconnect
mqtt_client.on_publish = publish

print("Attempting to connect to %s" % mqtt_client.broker)
mqtt_client.connect()


#get temperature data from openweathermap
def weather():
    socket = socketpool.SocketPool(wifi.radio)
    https = requests.Session(socket, ssl.create_default_context())

    jsonurl = ""
    # local cached copy (you need to use your own APPID for openweathermap)
    response = https.get(jsonurl)
    print("GET complete")
    j = response.json()
    #we want the main section
    t = j["main"]
    print(float(t["temp"]) -273.15)
    # -273.15 to convert from Kelvin

    data = float(t["temp"]) -273.15
    response.close()
    return data

import board
import displayio
import terminalio
from adafruit_display_text import label
import adafruit_displayio_ssd1306

displayio.release_displays()

oled_reset = board.D9

# Use for I2C
i2c = board.I2C()
display_bus = displayio.I2CDisplay(i2c, device_address=0x3C, reset=oled_reset)

WIDTH = 128
HEIGHT = 64  # the size of the oled screen
BORDER = 2

display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=WIDTH, height=HEIGHT)
splash = displayio.Group()
def background():
    # Make the display context
    display.show(splash)

    color_bitmap = displayio.Bitmap(WIDTH, HEIGHT, 1)
    color_palette = displayio.Palette(1)
    color_palette[0] = 0xFFFFFF  # White

    bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
    splash.append(bg_sprite)

    # Draw a smaller inner rectangle
    inner_bitmap = displayio.Bitmap(WIDTH - BORDER * 2, HEIGHT - BORDER * 2, 1)
    inner_palette = displayio.Palette(1)
    inner_palette[0] = 0x000000  # Black
    inner_sprite = displayio.TileGrid(
        inner_bitmap, pixel_shader=inner_palette, x=BORDER, y=BORDER
    )
    splash.append(inner_sprite)

#use of the light intensity sensor
sensor = adafruit_bh1750.BH1750(i2c)
pin = analogio.AnalogIn(board.IO11)

# display the data
i = 0 # i is used to control the refresh rate of temperature, moisture and light intensity
data = weather() # get temperature from openweathermap

while True:
    if i%3600 == 0:
        data = weather() # the temperature is updated every 1 hour
    else:
        data = data
    background() # refresh the screen in the begining of every circulation
    text = "temp: "+str(data)[:4]+"\n"+"moisture: "+"%.1f"%(pin.value/32)+"\n"+"light: "+"%.1f Lux" %sensor.lux
    text_area = label.Label(
        terminalio.FONT, text=text, color=0xFFFFFF, x=18, y=HEIGHT // 4 - 1
    )
    splash.append(text_area)
    # publish the data to the broker
    mqtt_client.publish(mqtt_topic1, data)
    mqtt_client.publish(mqtt_topic2, "%.1f"%(pin.value/32))
    mqtt_client.publish(mqtt_topic3, "%.1f"%sensor.lux)
    i+=5
    time.sleep(5)

while True:
    pass