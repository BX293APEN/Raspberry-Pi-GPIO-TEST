#!/usr/bin/env python3
# sudo pip install adafruit-blinka adafruit-circuitpython-ssd1306

from board import (
    SCL,
    SDA
)

from PIL import (
    Image,
    ImageDraw,
    ImageFont
)

from jaconv import (
    hira2hkata,
    h2z,
    z2h,
    kata2hira
)

from sys import argv
from os import path
from re import compile
from time import sleep
from datetime import datetime

from busio import I2C
from gpiozero import DigitalOutputDevice
from adafruit_ssd1306 import SSD1306_I2C

class SSD1306():
    def __init__(self, i2cDevice, i2cAddr = 0x3c):
        self.display    = SSD1306_I2C(128, 64, i2cDevice, addr=i2cAddr)
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
            self.nowTime = datetime.now() #+ datetime.timedelta(hours = 9)
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

class MorseCodeTranslator:
    def __init__(self, gpio = None, tempo = 0.03):
        self.hiragana = compile(r'[\u3041-\u3096]') #ひらがなの登録
        self.katakana = compile(r'[\u30A0-\u30FA]') #カタカナの登録
        self.tempo =  tempo
        self.morseGPIO = gpio
        self.morseDataDict = {
            "ja" : {
                "あ" : "--.--",
                "い" : ".-",
                "う" : "..-",
                "え" : "-.---",
                "お" : ".-...",
                "か" : ".-..",
                "き" : "-.-..",
                "く" : "...-",
                "け" : "-.--",
                "こ" : "----",
                "さ" : "-.-.-",
                "し" : "--.-.",
                "す" : "---.-",
                "せ" : ".---.",
                "そ" : "---.",
                "た" : "-.",
                "ち" : "..-.",
                "つ" : ".--.",
                "て" : ".-.--",
                "と" : "..-..",
                "な" : ".-.",
                "に" : "-.-.",
                "ぬ" : "....",
                "ね" : "--.-",
                "の" : "..--",
                "は" : "-...",
                "ひ" : "--..-",
                "ふ" : "--..",
                "へ" : ".",
                "ほ" : "-..",
                "ま" : "-..-",
                "み" : "..-.-",
                "む" : "-",
                "め" : "-...-",
                "も" : "-..-.",
                "や" : ".--",
                "ゆ" : "-..--",
                "よ" : "--",
                "ら" : "...",
                "り" : "--.",
                "る" : "-.--.",
                "れ" : "---",
                "ろ" : ".-.-",
                "わ" : "-.-",
                "を" : ".---",
                "ん" : ".-.-.",
                "、" : ".-.-.-",
                "濁点" : "..",
                "半濁点" : "..--.",
                "ー" : ".--.-",
                "？" : "..--.."
            },
            "en" : {
                "a" : ".-",
                "b" : "-...",
                "c" : "-.-.",
                "d" : "-..",
                "e" : ".",
                "f" : "..-.",
                "g" : "--.",
                "h" : "....",
                "i" : "..",
                "j" : ".---",
                "k" : "-.-",
                "l" : ".-..",
                "m" : "--",
                "n" : "-.",
                "o" : "---",
                "p" : ".--.",
                "q" : "--.-",
                "r" : ".-.",
                "s" : "...",
                "t" : "-",
                "u" : "..-",
                "v" : "...-",
                "w" : ".--",
                "x" : "-..-",
                "y" : "-.--",
                "z" : "--..",
                "." : ".-.-.",
                "'" : ".----.",
                "," : "--..--",
                "?" : "..--.."
            },
            "base" : {
                "1" : ".----",
                "2" : "..---",
                "3" : "...--",
                "4" : "....-",
                "5" : ".....",
                "6" : "-....",
                "7" : "--...",
                "8" : "---..",
                "9" : "----.",
                "0" : "-----",
                "space" : " "
            }
        }

        self.morseData = dict(**self.morseDataDict["base"], **self.morseDataDict["ja"], **self.morseDataDict["en"])
    
    def decode(self, morseCode:str, encoding = "ja"):
        morseCodeData = morseCode.split(" ")
        ans = ""
        lang = encoding
        if lang != "ja":
            lang = "en"
        codeDict = dict(**self.morseDataDict["base"], **self.morseDataDict[lang])
        
        for mcode in morseCodeData:
            try:
                if mcode == "":
                    ans += " "
                    
                else:
                    code = [k for k, v in codeDict.items() if v == mcode][0]
                    if code == "濁点":
                        ans += "゛"
                    elif code == "半濁点":
                        ans += "゜"
                    else:
                        ans += code
            except:
                ans += " "
        return ans
    
    def encode(self, morsestr):
        val = ""
        for code in morsestr:
            if code == "　":
                code = "space"
            elif code == " ":
                code = "space"
            elif code == "゛":
                code = "濁点"
            elif code == "゜":
                code = "半濁点"
                
            elif (self.hiragana.search(code) is not None):
                hkataka = hira2hkata(code)
                hkm = h2z(hkataka[0])
                try:
                    hka = h2z(hkataka[1])
                    val += f"{self.morseData[kata2hira(hkm)]} "
                    if hka == '\uFF9E':
                        code = "濁点"
                    elif hka == '\uFF9F':
                        code = "半濁点"
                
                except IndexError:
                    hka = ""

            elif (self.katakana.search(code) is not None):
                hkataka = z2h(code)
                hkm = h2z(hkataka[0])
                try:
                    hka = h2z(hkataka[1])
                    val += f"{self.morseData[kata2hira(hkm)]} "
                    if hka == '\uFF9E':
                        code = "濁点"
                    elif hka == '\uFF9F':
                        code = "半濁点"
                
                except IndexError:
                    hka = ""
                    code = kata2hira(hkm)
            else:
                code = code.lower()
            val += f"{self.morseData[code]} "
        return val
    
    def gpio(self, val):
        for c in val:
            if c == "-":
                self.tu()
            elif c == ".":
                self.to()
            else:
                self.sep()
        return val
    
    def tu(self):
        if self.morseGPIO is not None:
            self.morseGPIO.value = True
            sleep(self.tempo * 3)
            self.morseGPIO.value = False
            sleep(self.tempo)

    def to(self):
        if self.morseGPIO is not None:
            self.morseGPIO.value = True
            sleep(self.tempo)
            self.morseGPIO.value = False
            sleep(self.tempo)
        
    def sep(self):
        if self.morseGPIO is not None:
            self.morseGPIO.value = False
            sleep(self.tempo * 2)

class GPIOCtrl:
    def __init__(
        self,
        ledPin = 18
    ):
        self.i2c        = I2C(SCL, SDA)
        self.led        = DigitalOutputDevice(pin=ledPin)
        self.ssd1306    = SSD1306(self.i2c)
        self.ae_rx8900  = AE_RX8900(self.i2c)
        self.morse = MorseCodeTranslator(gpio = self.led, tempo = 0.1)

    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.i2c.unlock()

if __name__ == "__main__":
    dirName = path.dirname(path.abspath(__file__))
    font = f"{dirName}/font/AiC Font.ttf"
    msg = "Alice\nin\nCradle"

    with GPIOCtrl() as pinset:
        if len(argv) > 1:
            font = f"{dirName}/font/HGRGE.TTC"
            msg = argv[1].replace("\\n", "\n")
        
        pinset.ssd1306.show(msg, font, fontSize = 16)

        print(pinset.ae_rx8900.update())
        print(pinset.ae_rx8900.time())
        print(pinset.ae_rx8900.temp())

        try:
            pinset.morse.gpio(pinset.morse.encode(msg.replace("\n", " ")))
        except:
            pass

        pinset.led.value = 0
