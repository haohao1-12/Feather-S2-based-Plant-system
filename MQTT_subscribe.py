# Run this on Win10/Linux/Mac to listen for messages from the MQTT broker

import paho.mqtt.client as mqtt
import time
import win32com.client as win32
a = 1
# send an email when the soil is too dry
def sendemail():
    global a # global variable is used here to prevent email bombing
    a = 2 # once a notification emial is sent, "a" should be changed so that this email can only be sent one time
    outlook = win32.Dispatch('outlook.application')
    mail = outlook.CreateItem(0)
    mail.To = '' # your own outlook account
    mail.Subject = 'Plant Alert'
    mail.Body = 'Please water me!'

    mail.Send()
    

def on_message(client, userdata, message):
    print("received message: " , str(message.payload.decode("utf-8")))
    if float(message.payload.decode("utf-8")) > 1200 and (a == 1) :
        sendemail()

mqttBroker = "test.mosquitto.org"
client = mqtt.Client()
client.connect(mqttBroker)


client.subscribe("sl7n21/temperature") # the name of the topic should be the same as what is shown in "plant_monitoring.py"
client.subscribe("sl7n21/moisture")
client.subscribe("sl7n21/light")

client.on_message = on_message


client.loop_forever() # infinite loop
