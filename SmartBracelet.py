import paho.mqtt.client as mqtt
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QTimer  # Import QTimer from QtCore
from PyQt5.QtGui import QIntValidator  # Correct import for QIntValidator
from mqtt_init import *  # Import configuration from mqtt_init.py
import random
import sys

# Creating unique client name and health variables
global clientname, CONNECTED, current_body_temp, current_heart_rate, current_oxygen, current_sugar
CONNECTED = False
r = random.randrange(1, 10000000)
clientname = "IOT_client-IdBracelet-" + str(r)
bracelet_id = random.randrange(1, 100)

# Define topics for each health metric
BODY_TEMP_TOPIC = f'smartbracelet/{bracelet_id}/body_temp'
HEART_RATE_TOPIC = f'smartbracelet/{bracelet_id}/heart_rate'
OXYGEN_TOPIC = f'smartbracelet/{bracelet_id}/oxygen'
SUGAR_TOPIC = f'smartbracelet/{bracelet_id}/sugar'
update_rate = 5000  # in milliseconds

class MqttClient:

    def __init__(self):
        self.broker = broker_ip
        self.port = int(broker_port)
        self.clientname = clientname
        self.username = username
        self.password = password
        self.on_connected_to_form = ''

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
        global CONNECTED
        if rc == 0:
            print("Connected successfully.")
            CONNECTED = True
            self.on_connected_to_form()
        else:
            print("Connection failed with code:", rc)

    def on_disconnect(self, client, userdata, rc=0):
        print("Disconnected result code", rc)

    def connect_to(self):
        self.client = mqtt.Client(self.clientname, clean_session=True)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_log = self.on_log
        self.client.username_pw_set(self.username, self.password)
        print("Connecting to broker", self.broker)
        self.client.connect(self.broker, self.port)

    def disconnect_from(self):
        self.client.disconnect()

    def start_listening(self):
        self.client.loop_start()

    def stop_listening(self):
        self.client.loop_stop()

    def publish_to(self, topic, message):
        if CONNECTED:
            self.client.publish(topic, message)
        else:
            print("Connection is not established, cannot publish.")

class ConnectionDock(QDockWidget):

    def __init__(self, mc):
        QDockWidget.__init__(self)
        self.mc = mc
        self.mc.set_on_connected_to_form(self.on_connected)

        # Broker connection fields
        self.eHostInput = QLineEdit()
        self.eHostInput.setInputMask('999.999.999.999')
        self.eHostInput.setText(broker_ip)

        self.ePort = QLineEdit()
        self.ePort.setValidator(QIntValidator())
        self.ePort.setMaxLength(4)
        self.ePort.setText(broker_port)

        self.eClientID = QLineEdit()
        global clientname
        self.eClientID.setText(clientname)

        self.eUserName = QLineEdit()
        self.eUserName.setText(username)

        self.ePassword = QLineEdit()
        self.ePassword.setEchoMode(QLineEdit.Password)
        self.ePassword.setText(password)

        self.eConnectbtn = QPushButton("Enable/Connect", self)
        self.eConnectbtn.setToolTip("Click to connect")
        self.eConnectbtn.clicked.connect(self.on_button_connect_click)
        self.eConnectbtn.setStyleSheet("background-color: gray")

        # Health data fields for displaying metrics
        self.BodyTemp = QLineEdit()
        self.HeartRate = QLineEdit()
        self.Oxygen = QLineEdit()
        self.Sugar = QLineEdit()

        # Set up layout with new fields for each health metric
        formLayout = QFormLayout()
        formLayout.addRow("Turn On/Off", self.eConnectbtn)
        formLayout.addRow("Body Temperature", self.BodyTemp)
        formLayout.addRow("Heart Rate", self.HeartRate)
        formLayout.addRow("Oxygen Level", self.Oxygen)
        formLayout.addRow("Blood Sugar", self.Sugar)

        # Publish Topics Display
        publishTopicsBox = QGroupBox("Publish Topics")
        publishLayout = QFormLayout()
        publishLayout.addRow("Body Temp Topic", QLabel(BODY_TEMP_TOPIC))
        publishLayout.addRow("Heart Rate Topic", QLabel(HEART_RATE_TOPIC))
        publishLayout.addRow("Oxygen Topic", QLabel(OXYGEN_TOPIC))
        publishLayout.addRow("Blood Sugar Topic", QLabel(SUGAR_TOPIC))
        publishTopicsBox.setLayout(publishLayout)

        # Main layout widget
        mainLayout = QVBoxLayout()
        mainLayout.addLayout(formLayout)
        mainLayout.addWidget(publishTopicsBox)

        widget = QWidget(self)
        widget.setLayout(mainLayout)
        self.setTitleBarWidget(widget)
        self.setWidget(widget)
        self.setWindowTitle("Smart Bracelet Connection")

    def on_connected(self):
        self.eConnectbtn.setStyleSheet("background-color: green")

    def on_button_connect_click(self):
        self.mc.set_broker(self.eHostInput.text())
        self.mc.set_port(int(self.ePort.text()))
        self.mc.set_clientName(self.eClientID.text())
        self.mc.set_username(self.eUserName.text())
        self.mc.set_password(self.ePassword.text())
        self.mc.connect_to()
        self.mc.start_listening()

class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.mc = MqttClient()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(update_rate)

        self.setGeometry(30, 600, 400, 200)
        self.setWindowTitle('Smart Bracelet Health Monitor')

        self.connectionDock = ConnectionDock(self.mc)
        self.addDockWidget(Qt.TopDockWidgetArea, self.connectionDock)

    def update_data(self):
        # Generate random health metric values to simulate real data
        global current_body_temp, current_heart_rate, current_oxygen, current_sugar
        current_body_temp = round(random.uniform(36, 42), 2)
        current_heart_rate = round(random.uniform(60, 150), 2)
        current_oxygen = round(random.uniform(85, 100), 2)
        current_sugar = round(random.uniform(80, 300), 2)

        # Update GUI with health metric values
        self.connectionDock.BodyTemp.setText(str(current_body_temp))
        self.connectionDock.HeartRate.setText(str(current_heart_rate))
        self.connectionDock.Oxygen.setText(str(current_oxygen))
        self.connectionDock.Sugar.setText(str(current_sugar))

        # Publish each health metric to its respective MQTT topic
        self.mc.publish_to(BODY_TEMP_TOPIC, f'Body Temperature: {current_body_temp}')
        self.mc.publish_to(HEART_RATE_TOPIC, f'Heart Rate: {current_heart_rate}')
        self.mc.publish_to(OXYGEN_TOPIC, f'Oxygen Level: {current_oxygen}')
        self.mc.publish_to(SUGAR_TOPIC, f'Blood Sugar: {current_sugar}')


app = QApplication(sys.argv)
mainwin = MainWindow()
mainwin.show()
app.exec_()
