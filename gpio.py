#!/usr/bin/env python3
# sudo pip install adafruit-circuitpython-ssd1306
import board, busio, adafruit_ssd1306, datetime, gpiozero

from PIL import (
    Image,
    ImageDraw,
    ImageFont
)

from time import sleep


class SSD1306():
    def __init__(self, i2cDevice, i2cAddr = 0x3c):
        self.display = adafruit_ssd1306.SSD1306_I2C(128, 64, i2cDevice, addr=i2cAddr)
        self.display.fill(0)
        self.display.show()
        self.oledWidth = self.display.width
        self.oledHeight = self.display.height
    
    def show(
        self, 
        message, 
        fontPath, 
        fontSize = 12, 
        lightMode = False, 
        dispMode = False, 
        lineMode = False
    ):
        image = Image.new("1", (self.oledWidth, self.oledHeight))
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype(fontPath, fontSize) #フォント設定
        draw.rectangle((0, 0, self.oledWidth - 1, self.oledWidth - 1), outline = lineMode, fill = int(lightMode)) # bg設定
        dispText = ""
        if dispMode:
            for c in message:
                dispText += c
                draw.text((3, 0), dispText, font = font, fill = int(1 - lightMode))
                self.display.image(image)
                self.display.show()
        else:
            draw.text((3, 0), message, font = font, fill = int(1 - lightMode))
            self.display.image(image)
            self.display.show()

class AE_RX8900():
    def __init__(self, i2cDevice, i2cAddr = 0x32):
        self.weekdayCode = [
            {
                "code" : "月",
                "rtc" : 0x02
            },
            {
                "code" : "火",
                "rtc" : 0x04
            },
            {
                "code" : "水",
                "rtc" : 0x08
            },
            {
                "code" : "木",
                "rtc" : 0x10
            },
            {
                "code" : "金",
                "rtc" : 0x20
            },
            {
                "code" : "土",
                "rtc" : 0x40
            },
            {
                "code" : "日",
                "rtc" : 0x01
            }
        ]
        self.i2c = i2cDevice
        self.i2cAddr = i2cAddr

    def temp(self):
        try:
            self.i2c.writeto(self.i2cAddr, chr(0x17))
            result = bytearray(1)
            self.i2c.readfrom_into(self.i2cAddr, result)
            tempData = result[0]
            self.temp = (tempData * 2 - 187.19)/ 3.218
            return self.temp
        except:
            return 0
    
    def time(self):
        try:
            self.decode_time()
            return self.rtctime2str()
        
        except Exception as e:
            return f"RTCモジュールエラー\n{e}"
    
    def rtctime2str(self):
        return f"{self.rtcYear}/{self.rtcMon}/{self.rtcDateData} {self.rtcHou}:{self.rtcMin}:{self.rtcSec} ({self.rtcWeekday})"
    
    def decode_time(self):
        self.i2c.writeto(self.i2cAddr, chr(0x00))
        result = bytearray(8)
        self.i2c.readfrom_into(self.i2cAddr, result)
        resultRTC = [hex(i) for i in list(result)]
        try:
            self.rtcSec         = str(resultRTC[0]).split("0x")[1]
            self.rtcMin         = str(resultRTC[1]).split("0x")[1]
            self.rtcHou         = str(resultRTC[2]).split("0x")[1]
            self.rtcWeekday     =    [
                v["code"] for v in self.weekdayCode
                    if v["rtc"] == int(resultRTC[3], 16)
            ][0]
            self.rtcDateData    = str(resultRTC[4]).split("0x")[1]
            self.rtcMon         = str(resultRTC[5]).split("0x")[1]
            self.rtcYear        = f"20{str(resultRTC[6]).split('0x')[1]}"
        except Exception as e:
            print(f"時刻取得エラー : {e}")
    
    def update(self):
        try:
            self.nowTime = datetime.datetime.now() #+ datetime.timedelta(hours = 9)
            self.nowYear = self.nowTime.year
            self.nowMonth = self.nowTime.month
            self.nowDate = self.nowTime.day
            self.weekdayIndex = self.nowTime.weekday()
            self.weekdayRTC = self.weekdayCode[self.weekdayIndex]["rtc"]
            self.nowHour = self.nowTime.hour
            self.nowMinute = self.nowTime.minute
            self.nowSecond = self.nowTime.second
            #秒修正
            d = 0b0
            secondData = self.nowSecond
            for c in str(secondData):
                d = d << 4 | int(c)
            self.i2c.writeto(self.i2cAddr, f"{chr(0x00)}{chr(d)}")
        
            #分修正
            d = 0b0
            minurteData = self.nowMinute
            for c in str(minurteData):
                d = d << 4 | int(c)
            self.i2c.writeto(self.i2cAddr, f"{chr(0x01)}{chr(d)}")
        
            #時修正
            d = 0b0
            hourData = self.nowHour
            for c in str(hourData):
                d = d << 4 | int(c)
            self.i2c.writeto(self.i2cAddr, f"{chr(0x02)}{chr(d)}")
        
            #曜日修正
            weekdayData = self.weekdayRTC
            self.i2c.writeto(self.i2cAddr, f"{chr(0x03)}{chr(weekdayData)}")
        
            #日修正
            d = 0b0
            dateData = self.nowDate
            for c in str(dateData):
                d = d << 4 | int(c)
            self.i2c.writeto(self.i2cAddr, f"{chr(0x04)}{chr(d)}")
        
            #月修正
            d = 0b0
            monthData = self.nowMonth
            for c in str(monthData):
                d = d << 4 | int(c)
            self.i2c.writeto(self.i2cAddr, f"{chr(0x05)}{chr(d)}")
        
            #年修正
            d = 0b0
            yearData = self.nowYear
            for c in str(yearData % 100):
                d = d << 4 | int(c)
            #print(hex(d))
            self.i2c.writeto(self.i2cAddr, f"{chr(0x06)}{chr(d)}")
            
            self.decode_time()
            return f"Update : {self.rtctime2str()}"
        
        except Exception as e:
            return f"時刻更新エラー : {e}"


class GPIOCtrl:
    def __init__(
        self,
        ledPin = 18
    ):
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.led = gpiozero.DigitalOutputDevice(pin=ledPin)
        self.ssd1306 = SSD1306(self.i2c)
        self.ae_rx8900 = AE_RX8900(self.i2c)
        
        
    
if __name__ == "__main__":
    pinset = GPIOCtrl()
    # pinset.ssd1306.show("Alice\nin\nCradle", "font/AiC Font.ttf", fontSize = 16)
    pinset.ssd1306.show("Hello\nWorld", "font/HGRGE.TTC", fontSize = 16)
    print(pinset.ae_rx8900.update())
    print(pinset.ae_rx8900.time())
    print(pinset.ae_rx8900.temp())
    pinset.led.value = 0
    while True:
        pinset.led.value = 1 - pinset.led.value
        sleep(1)