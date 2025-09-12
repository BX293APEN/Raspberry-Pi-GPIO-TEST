#!/usr/bin/env python3
# sudo pip install adafruit-blinka adafruit-circuitpython-ssd1306
import board, busio, adafruit_ssd1306, datetime, gpiozero, sys

from PIL import (
    Image,
    ImageDraw,
    ImageFont
)

from time import sleep


class SSD1306():
    def __init__(self, i2cDevice, i2cAddr = 0x3c):
        self.display    = adafruit_ssd1306.SSD1306_I2C(128, 64, i2cDevice, addr=i2cAddr)
        self.display.fill(0)
        self.display.show()
        self.oledWidth  = self.display.width
        self.oledHeight = self.display.height
    
    def show(
        self, 
        message, 
        fontPath, 
        fontSize    = 12, 
        lightMode   = False, 
        dispMode    = False, 
        lineMode    = False
    ):
        image       = Image.new("1", (self.oledWidth, self.oledHeight))
        draw        = ImageDraw.Draw(image)
        font        = ImageFont.truetype(fontPath, fontSize) #フォント設定
        draw.rectangle((0, 0, self.oledWidth - 1, self.oledHeight - 1), outline = lineMode, fill = int(lightMode)) # bg設定
        dispText    = ""
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
        self.i2c        = i2cDevice
        self.i2cAddr    = i2cAddr
    
    def bcd2int(self, bcdByte):
        return ((bcdByte >> 4) * 10) + (bcdByte & 0x0F)
    
    def int2bcd_byte(self, digit):
        return (((digit // 10) & 0x0F) << 4) | ((digit % 10) & 0x0F)
    
    def temp(self):
        try:
            self.i2c.writeto(self.i2cAddr, bytearray([0x17]))
            result      = bytearray(1)
            self.i2c.readfrom_into(self.i2cAddr, result)
            tempData    = result[0]
            self.temp   = (tempData * 2 - 187.19)/ 3.218
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
        return f"{self.rtcYear}/{self.rtcMon:02}/{self.rtcDateData:02} {self.rtcHou:02}:{self.rtcMin:02}:{self.rtcSec:02} ({self.rtcWeekday})"

    def decode_time(self):
        self.i2c.writeto(self.i2cAddr, bytearray([0x00]))
        result = bytearray(8)
        self.i2c.readfrom_into(self.i2cAddr, result)
        try:
            self.rtcSec         = self.bcd2int(result[0])
            self.rtcMin         = self.bcd2int(result[1])
            self.rtcHou         = self.bcd2int(result[2])
            self.rtcWeekday     =    [
                v["code"] for v in self.weekdayCode
                    if v["rtc"] == result[3]
            ][0]
            self.rtcDateData    = self.bcd2int(result[4])
            self.rtcMon         = self.bcd2int(result[5])
            self.rtcYear        = f"20{self.bcd2int(result[6])}"
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
            
            d = self.int2bcd_byte(self.nowSecond)                   #秒修正
            self.i2c.writeto(self.i2cAddr, bytearray([0x00, d]))

            d = self.int2bcd_byte(self.nowMinute)                   #分修正
            self.i2c.writeto(self.i2cAddr, bytearray([0x01, d]))
            
            d = self.int2bcd_byte(self.nowHour)                     #時修正
            self.i2c.writeto(self.i2cAddr, bytearray([0x02, d]))

            weekdayData = self.weekdayRTC                           #曜日修正
            self.i2c.writeto(self.i2cAddr, bytearray([0x03, weekdayData]))

            d = self.int2bcd_byte(self.nowDate)                     #日修正
            self.i2c.writeto(self.i2cAddr, bytearray([0x04, d]))

            d = self.int2bcd_byte(self.nowMonth)                    #月修正
            self.i2c.writeto(self.i2cAddr, bytearray([0x05, d]))
        
            d = self.int2bcd_byte(self.nowYear % 100)               #年修正
            self.i2c.writeto(self.i2cAddr, bytearray([0x06, d]))
            
            self.decode_time()
            return f"Update : {self.rtctime2str()}"
        
        except Exception as e:
            return f"時刻更新エラー : {e}"


class GPIOCtrl:
    def __init__(
        self,
        ledPin = 18
    ):
        self.i2c        = busio.I2C(board.SCL, board.SDA)
        self.led        = gpiozero.DigitalOutputDevice(pin=ledPin)
        self.ssd1306    = SSD1306(self.i2c)
        self.ae_rx8900  = AE_RX8900(self.i2c)

    def __enter__(self):
        return self
    def __exit__(self, *args):
        self.i2c.unlock()

        
if __name__ == "__main__":
    with GPIOCtrl() as pinset:
        if len(sys.argv) > 1:
            dispTxt = sys.argv[1].replace("\\n", "\n")
            pinset.ssd1306.show(dispTxt, "font/HGRGE.TTC", fontSize = 16)

        else:
            pinset.ssd1306.show("Alice\nin\nCradle", "font/AiC Font.ttf", fontSize = 16)
            
        print(pinset.ae_rx8900.update())
        print(pinset.ae_rx8900.time())
        print(pinset.ae_rx8900.temp())
        pinset.led.value = 0

        try:
            while True:
                pinset.led.value = 1 - pinset.led.value
                sleep(1)

        except KeyboardInterrupt:
            print("終了中...")
        
        except Exception as e:
            print(e)

        finally:
            pinset.led.value = 0
