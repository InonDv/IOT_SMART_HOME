import paho.mqtt.client as mqtt
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIntValidator
from mqtt_init import *  # Import broker configurations from mqtt_init.py
import sys
import random

# Unique client name for the hospital
global clientname
r = random.randrange(1, 10000000)
clientname = "HospitalClient-" + str(r)

# Subscription topic for all smart bracelet data
BRACELET_TOPIC = 'smartbracelet/#'

# Thresholds for critical health metrics
CRITICAL_BODY_TEMP = 39.0
CRITICAL_HEART_RATE = 120
CRITICAL_OXYGEN_LEVEL = 90
CRITICAL_SUGAR_LEVEL = 200

class MqttClient:

    def __init__(self):
        self.broker = broker_ip
        self.port = int(broker_port)
        self.clientname = clientname
        self.username = username
        self.password = password
        self.subscribeTopic = BRACELET_TOPIC
        self.on_connected_to_form = None
        self.emergency_status = False  # Track if there’s an emergency

    # Setter methods for each attribute
    def set_broker(self, value):
        self.broker = value

    def set_port(self, value):
        self.port = value

    def set_clientName(self, value):
        self.clientname = value

    def set_username(self, value):
        self.username = value

    def set_password(self, value):
        self.password = value

    def set_on_connected_to_form(self, on_connected_to_form):
        self.on_connected_to_form = on_connected_to_form

    def on_log(self, client, userdata, level, buf):
        print("log:", buf)

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected successfully to broker.")
            self.client.subscribe(self.subscribeTopic)  # Subscribe to all bracelet data
            if callable(self.on_connected_to_form):
                self.on_connected_to_form()  # Trigger the function when connected
        else:
            print("Failed to connect with code:", rc)

    def on_disconnect(self, client, userdata, rc):
        print("Disconnected with code:", rc)

    def on_message(self, client, userdata, msg):
        topic = msg.topic
        message = str(msg.payload.decode("utf-8"))
        print(f"Message received from {topic}: {message}")
        self.check_emergency_status(topic, message)

    def connect_to(self):
        self.client = mqtt.Client(self.clientname, clean_session=True)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_log = self.on_log
        self.client.on_message = self.on_message
        self.client.username_pw_set(self.username, self.password)
        print(f"Connecting to broker {self.broker}:{self.port}")
        self.client.connect(self.broker, self.port)
        self.client.loop_start()  # Start the loop to maintain the connection

    def disconnect_from(self):
        self.client.disconnect()

    def subscribe_to(self, topic):
        self.client.subscribe(topic)

    def check_emergency_status(self, topic, message):
        """Check received health metrics and update emergency status."""
        emergency_triggered = False

        if "body_temp" in topic:
            body_temp = float(message.split(": ")[1])
            if body_temp > CRITICAL_BODY_TEMP:
                print("ALERT: Critical body temperature detected!")
                emergency_triggered = True
        elif "heart_rate" in topic:
            heart_rate = float(message.split(": ")[1])
            if heart_rate > CRITICAL_HEART_RATE:
                print("ALERT: Critical heart rate detected!")
                emergency_triggered = True
        elif "oxygen" in topic:
            oxygen_level = float(message.split(": ")[1])
            if oxygen_level < CRITICAL_OXYGEN_LEVEL:
                print("ALERT: Low oxygen level detected!")
                emergency_triggered = True
        elif "sugar" in topic:
            sugar_level = float(message.split(": ")[1])
            if sugar_level > CRITICAL_SUGAR_LEVEL:
                print("ALERT: High blood sugar level detected!")
                emergency_triggered = True

        # Update emergency status
        self.emergency_status = emergency_triggered
        mainwin.update_emergency_status()


class HospitalInterface(QDockWidget):

    def __init__(self, mc):
        super().__init__()

        self.mc = mc
        self.mc.set_on_connected_to_form(self.on_connected)

        # Interface elements for MQTT connection
        self.eHostInput = QLineEdit()
        self.eHostInput.setInputMask('999.999.999.999')
        self.eHostInput.setText(broker_ip)

        self.ePort = QLineEdit()
        self.ePort.setValidator(QIntValidator())
        self.ePort.setText(broker_port)

        self.eClientID = QLineEdit()
        self.eClientID.setText(clientname)

        self.eUserName = QLineEdit()
        self.eUserName.setText(username)

        self.ePassword = QLineEdit()
        self.ePassword.setEchoMode(QLineEdit.Password)
        self.ePassword.setText(password)

        self.eConnectBtn = QPushButton("Connect", self)
        self.eConnectBtn.clicked.connect(self.on_button_connect_click)
        self.eConnectBtn.setStyleSheet("background-color: gray")

        self.eSubscribeTopic = QLineEdit()
        self.eSubscribeTopic.setText(BRACELET_TOPIC)

        layout = QFormLayout()
        layout.addRow("Connect", self.eConnectBtn)
        layout.addRow("Subscription Topic", self.eSubscribeTopic)

        widget = QWidget(self)
        widget.setLayout(layout)
        self.setTitleBarWidget(widget)
        self.setWidget(widget)
        self.setWindowTitle("Hospital Connection")

    def on_connected(self):
        self.eConnectBtn.setStyleSheet("background-color: green")

    def on_button_connect_click(self):
        self.mc.set_broker(self.eHostInput.text())
        self.mc.set_port(int(self.ePort.text()))
        self.mc.set_clientName(self.eClientID.text())
        self.mc.set_username(self.eUserName.text())
        self.mc.set_password(self.ePassword.text())
        self.mc.connect_to()
        self.mc.subscribe_to(self.eSubscribeTopic.text())


class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.mc = MqttClient()
        self.setGeometry(50, 50, 400, 250)
        self.setWindowTitle('Hospital Emergency Monitor')

        # Emergency Status Label
        self.emergency_label = QLabel("Emergency: Everything is fine", self)
        self.emergency_label.setGeometry(50, 100, 300, 30)

        # Hospital interface dock widget
        self.hospitalInterface = HospitalInterface(self.mc)
        self.addDockWidget(Qt.TopDockWidgetArea, self.hospitalInterface)

    def update_emergency_status(self):
        """Update the emergency label based on the client's health status."""
        if self.mc.emergency_status:
            self.emergency_label.setText("Emergency: Yes")
            self.emergency_label.setStyleSheet("color: red; font-weight: bold;")
        else:
            self.emergency_label.setText("Emergency: Everything is fine")
            self.emergency_label.setStyleSheet("color: green; font-weight: bold;")


app = QApplication(sys.argv)
mainwin = MainWindow()
mainwin.show()
app.exec_()
