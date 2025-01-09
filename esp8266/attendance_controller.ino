#include <ESP8266WiFi.h>
#include <WebSocketsClient.h>
#include <ArduinoJson.h>
#include <Adafruit_Fingerprint.h>
#include <SPI.h>
#include <MFRC522.h>

// WiFi credentials
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// WebSocket server settings
const char* websocket_server = "YOUR_SERVER_IP";
const int websocket_port = 8765;

// Hardware pins
#define FINGERPRINT_RX 14  // D5
#define FINGERPRINT_TX 12  // D6
#define RST_PIN 5         // D1
#define SS_PIN 4          // D2

// Global objects
WebSocketsClient webSocket;
SoftwareSerial fingerprintSerial(FINGERPRINT_RX, FINGERPRINT_TX);
Adafruit_Fingerprint fingerprint = Adafruit_Fingerprint(&fingerprintSerial);
MFRC522 rfid(SS_PIN, RST_PIN);

// Status variables
bool fingerprintReady = false;
bool rfidReady = false;
int fingerprintCount = 0;
int rfidCount = 0;

void setup() {
    Serial.begin(115200);
    
    // Initialize fingerprint sensor
    fingerprintSerial.begin(57600);
    if (fingerprint.verifyPassword()) {
        Serial.println("Fingerprint sensor connected!");
        fingerprintReady = true;
        fingerprintCount = fingerprint.templateCount;
    }
    
    // Initialize RFID reader
    SPI.begin();
    rfid.PCD_Init();
    if (rfid.PCD_PerformSelfTest()) {
        Serial.println("RFID reader connected!");
        rfidReady = true;
    }
    
    // Connect to WiFi
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("WiFi connected");
    
    // Configure WebSocket client
    webSocket.begin(websocket_server, websocket_port, "/");
    webSocket.onEvent(webSocketEvent);
    webSocket.setReconnectInterval(5000);
}

void loop() {
    webSocket.loop();
    
    // Check RFID
    if (rfidReady && rfid.PICC_IsNewCardPresent() && rfid.PICC_ReadCardSerial()) {
        String cardId = "";
        for (byte i = 0; i < rfid.uid.size; i++) {
            cardId += String(rfid.uid.uidByte[i], HEX);
        }
        
        // Send RFID event
        DynamicJsonDocument doc(200);
        doc["device"] = "esp8266";
        doc["event"]["type"] = "rfid";
        doc["event"]["status"] = "card_detected";
        doc["event"]["card_id"] = cardId;
        
        String jsonString;
        serializeJson(doc, jsonString);
        webSocket.sendTXT(jsonString);
        
        rfid.PICC_HaltA();
        rfid.PCD_StopCrypto1();
    }
    
    // Send status update every 5 seconds
    static unsigned long lastStatus = 0;
    if (millis() - lastStatus > 5000) {
        sendStatus();
        lastStatus = millis();
    }
}

void webSocketEvent(WStype_t type, uint8_t * payload, size_t length) {
    switch(type) {
        case WStype_DISCONNECTED:
            Serial.println("WebSocket disconnected");
            break;
            
        case WStype_CONNECTED:
            Serial.println("WebSocket connected");
            sendStatus();
            break;
            
        case WStype_TEXT:
            handleCommand((char*)payload);
            break;
    }
}

void sendStatus() {
    DynamicJsonDocument doc(200);
    doc["device"] = "esp8266";
    doc["status"]["fingerprint"] = fingerprintReady ? "Ready" : "Not Ready";
    doc["status"]["rfid"] = rfidReady ? "Ready" : "Not Ready";
    doc["status"]["fingerprint_count"] = fingerprintCount;
    doc["status"]["rfid_count"] = rfidCount;
    doc["status"]["ip"] = WiFi.localIP().toString();
    doc["status"]["rssi"] = WiFi.RSSI();
    
    String jsonString;
    serializeJson(doc, jsonString);
    webSocket.sendTXT(jsonString);
}

void handleCommand(char* payload) {
    DynamicJsonDocument doc(200);
    DeserializationError error = deserializeJson(doc, payload);
    
    if (error) {
        Serial.println("JSON parsing failed");
        return;
    }
    
    const char* command = doc["command"];
    
    if (strcmp(command, "test_fingerprint") == 0) {
        testFingerprint();
    }
    else if (strcmp(command, "enroll_fingerprint") == 0) {
        enrollFingerprint();
    }
    else if (strcmp(command, "test_rfid") == 0) {
        testRFID();
    }
    else if (strcmp(command, "register_card") == 0) {
        registerCard();
    }
}

void testFingerprint() {
    if (!fingerprintReady) {
        sendFingerprintEvent("error", "Sensor not ready");
        return;
    }
    
    sendFingerprintEvent("testing", "Place finger on sensor");
    
    while (!fingerprint.getImage()) {
        delay(100);
    }
    
    int p = fingerprint.image2Tz();
    if (p != FINGERPRINT_OK) {
        sendFingerprintEvent("error", "Image conversion failed");
        return;
    }
    
    sendFingerprintEvent("success", "Test successful");
}

void enrollFingerprint() {
    if (!fingerprintReady) {
        sendFingerprintEvent("error", "Sensor not ready");
        return;
    }
    
    int id = fingerprint.templateCount + 1;
    
    sendFingerprintEvent("enrolling", "Place finger on sensor");
    
    while (!fingerprint.getImage()) {
        delay(100);
    }
    
    int p = fingerprint.image2Tz(1);
    if (p != FINGERPRINT_OK) {
        sendFingerprintEvent("error", "Image conversion failed");
        return;
    }
    
    sendFingerprintEvent("enrolling", "Remove finger");
    delay(2000);
    
    sendFingerprintEvent("enrolling", "Place same finger again");
    while (!fingerprint.getImage()) {
        delay(100);
    }
    
    p = fingerprint.image2Tz(2);
    if (p != FINGERPRINT_OK) {
        sendFingerprintEvent("error", "Image conversion failed");
        return;
    }
    
    p = fingerprint.createModel();
    if (p != FINGERPRINT_OK) {
        sendFingerprintEvent("error", "Failed to create model");
        return;
    }
    
    p = fingerprint.storeModel(id);
    if (p != FINGERPRINT_OK) {
        sendFingerprintEvent("error", "Failed to store model");
        return;
    }
    
    fingerprintCount++;
    sendFingerprintEvent("success", "Enrollment successful");
    sendStatus();
}

void testRFID() {
    if (!rfidReady) {
        sendRFIDEvent("error", "Reader not ready", "");
        return;
    }
    
    sendRFIDEvent("testing", "Waiting for card", "");
}

void registerCard() {
    if (!rfidReady) {
        sendRFIDEvent("error", "Reader not ready", "");
        return;
    }
    
    sendRFIDEvent("registering", "Place card on reader", "");
}

void sendFingerprintEvent(const char* status, const char* message) {
    DynamicJsonDocument doc(200);
    doc["device"] = "esp8266";
    doc["event"]["type"] = "fingerprint";
    doc["event"]["status"] = status;
    doc["event"]["message"] = message;
    
    String jsonString;
    serializeJson(doc, jsonString);
    webSocket.sendTXT(jsonString);
}

void sendRFIDEvent(const char* status, const char* message, const char* cardId) {
    DynamicJsonDocument doc(200);
    doc["device"] = "esp8266";
    doc["event"]["type"] = "rfid";
    doc["event"]["status"] = status;
    doc["event"]["message"] = message;
    if (strlen(cardId) > 0) {
        doc["event"]["card_id"] = cardId;
    }
    
    String jsonString;
    serializeJson(doc, jsonString);
    webSocket.sendTXT(jsonString);
}
