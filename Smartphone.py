import paho.mqtt.client as mqtt
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIntValidator
from mqtt_init import *  # Import MQTT broker configurations
import sys
import random
import datetime

# Unique client name for the smartphone
global clientname
r = random.randrange(1, 10000000)
clientname = "SmartPhoneClient-" + str(r)

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
        self.on_connected_to_form = ''
        self.emergency_status = False  # Track if there’s an emergency
        # Latest values for each health metric
        self.latest_heart_rate = "N/A"
        self.latest_body_temp = "N/A"
        self.latest_oxygen = "N/A"
        self.latest_sugar = "N/A"

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
            self.client.subscribe(self.subscribeTopic)
            if callable(self.on_connected_to_form):
                self.on_connected_to_form()
        else:
            print("Failed to connect with code:", rc)

    def on_disconnect(self, client, userdata, rc):
        print("Disconnected with code:", rc)

    def on_message(self, client, userdata, msg):
        topic = msg.topic
        message = str(msg.payload.decode("utf-8"))
        print(f"Message received from {topic}: {message}")
        self.check_critical_values(topic, message)

        # Update relevant metric based on topic
        if "heart_rate" in topic:
            self.latest_heart_rate = message.split(": ")[1]
            mainwin.update_heart_rate_display()
        elif "body_temp" in topic:
            self.latest_body_temp = message.split(": ")[1]
            mainwin.update_body_temp_display()
        elif "oxygen" in topic:
            self.latest_oxygen = message.split(": ")[1]
            mainwin.update_oxygen_display()
        elif "sugar" in topic:
            self.latest_sugar = message.split(": ")[1]
            mainwin.update_sugar_display()

    def connect_to(self):
        self.client = mqtt.Client(self.clientname, clean_session=True)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_log = self.on_log
        self.client.on_message = self.on_message
        self.client.username_pw_set(self.username, self.password)
        print(f"Connecting to broker {self.broker}:{self.port}")
        self.client.connect(self.broker, self.port)

    def disconnect_from(self):
        self.client.disconnect()

    def start_listening(self):
        self.client.loop_start()

    def stop_listening(self):
        self.client.loop_stop()

    def subscribe_to(self, topic):
        self.client.subscribe(topic)

    def check_critical_values(self, topic, message):
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

        self.emergency_status = emergency_triggered
        mainwin.update_emergency_status()

    def save_logs(self):
        """Save current health metrics to a log file."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = (
            f"{timestamp}\n"
            f"Emergency Status: {'Yes' if self.emergency_status else 'No'}\n"
            f"Heart Rate: {self.latest_heart_rate}\n"
            f"Body Temp: {self.latest_body_temp}\n"
            f"Oxygen Level: {self.latest_oxygen}\n"
            f"Blood Sugar: {self.latest_sugar}\n\n"
        )
        with open("health_metrics_log.txt", "a") as file:
            file.write(log_message)
        print("Logs saved to health_metrics_log.txt")


class SmartPhoneInterface(QDockWidget):

    def __init__(self, mc):
        super().__init__()
        self.mc = mc
        self.mc.set_on_connected_to_form(self.on_connected)

        # MQTT connection fields
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
        self.setWindowTitle("SmartPhone Connection")

    def on_connected(self):
        self.eConnectBtn.setStyleSheet("background-color: green")

    def on_button_connect_click(self):
        self.mc.set_broker(self.eHostInput.text())
        self.mc.set_port(int(self.ePort.text()))
        self.mc.set_clientName(self.eClientID.text())
        self.mc.set_username(self.eUserName.text())
        self.mc.set_password(self.ePassword.text())
        self.mc.connect_to()
        self.mc.start_listening()
        self.mc.subscribe_to(self.eSubscribeTopic.text())


class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.mc = MqttClient()
        self.setGeometry(50, 50, 400, 600)
        self.setWindowTitle('SmartPhone Health Monitor')

        # Main central widget and layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Emergency Status Label
        self.emergency_label = QLabel("Emergency: Everything is fine", self)
        self.emergency_label.setStyleSheet("font-size: 16px;")
        main_layout.addWidget(self.emergency_label)

        # Display labels for each health metric
        self.heart_rate_label = QLabel("Latest Heart Rate: N/A", self)
        self.body_temp_label = QLabel("Latest Body Temp: N/A", self)
        self.oxygen_label = QLabel("Latest Oxygen Level: N/A", self)
        self.sugar_label = QLabel("Latest Blood Sugar: N/A", self)
        
        # Add health metric labels to layout
        main_layout.addWidget(self.heart_rate_label)
        main_layout.addWidget(self.body_temp_label)
        main_layout.addWidget(self.oxygen_label)
        main_layout.addWidget(self.sugar_label)

        # Save Log Button
        self.save_log_button = QPushButton("Save Log", self)
        self.save_log_button.setEnabled(True)  # Ensure the button is enabled
        self.save_log_button.clicked.connect(self.save_logs)  # Connect the button to save_logs method
        main_layout.addWidget(self.save_log_button)

        # Smartphone interface dock widget
        self.smartphoneInterface = SmartPhoneInterface(self.mc)
        self.addDockWidget(Qt.TopDockWidgetArea, self.smartphoneInterface)

    def update_emergency_status(self):
        """Update the emergency label based on the client's health status and save logs if emergency occurs."""
        if self.mc.emergency_status:
            self.emergency_label.setText("Emergency: Yes")
            self.emergency_label.setStyleSheet("color: red; font-weight: bold; font-size: 16px;")
            print("Emergency detected, saving logs...")
            self.save_logs()  # Automatically save logs when an emergency is detected
        else:
            self.emergency_label.setText("Emergency: Everything is fine")
            self.emergency_label.setStyleSheet("color: green; font-weight: bold; font-size: 16px;")

    # Methods to update display labels with the latest metric values
    def update_heart_rate_display(self):
        self.heart_rate_label.setText(f"Latest Heart Rate: {self.mc.latest_heart_rate}")

    def update_body_temp_display(self):
        self.body_temp_label.setText(f"Latest Body Temp: {self.mc.latest_body_temp}")

    def update_oxygen_display(self):
        self.oxygen_label.setText(f"Latest Oxygen Level: {self.mc.latest_oxygen}")

    def update_sugar_display(self):
        self.sugar_label.setText(f"Latest Blood Sugar: {self.mc.latest_sugar}")

    def save_logs(self):
        print("Saving logs...")  # Print to confirm button is working
        self.mc.save_logs()

    def connect_to_broker(self):
        """Connect to the MQTT broker and start listening for messages."""
        self.mc.connect_to()
        self.mc.start_listening()



app = QApplication(sys.argv)
mainwin = MainWindow()
mainwin.show()
app.exec_()
