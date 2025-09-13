import re, jaconv, time

class MorseCodeTranslator:
    def __init__(self, tempo = 0.03, gpio = None):
        self.hiragana = re.compile(r'[\u3041-\u3096]') #ひらがなの登録
        self.katakana = re.compile(r'[\u30A0-\u30FA]') #カタカナの登録
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
                hkataka = jaconv.hira2hkata(code)
                hkm = jaconv.h2z(hkataka[0])
                try:
                    hka = jaconv.h2z(hkataka[1])
                    val += f"{self.morseData[jaconv.kata2hira(hkm)]} "
                    if hka == '\uFF9E':
                        code = "濁点"
                    elif hka == '\uFF9F':
                        code = "半濁点"
                
                except IndexError:
                    hka = ""

            elif (self.katakana.search(code) is not None):
                hkataka = jaconv.z2h(code)
                hkm = jaconv.h2z(hkataka[0])
                try:
                    hka = jaconv.h2z(hkataka[1])
                    val += f"{self.morseData[jaconv.kata2hira(hkm)]} "
                    if hka == '\uFF9E':
                        code = "濁点"
                    elif hka == '\uFF9F':
                        code = "半濁点"
                
                except IndexError:
                    hka = ""
                    code = jaconv.kata2hira(hkm)
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
            time.sleep(self.tempo * 3)
            self.morseGPIO.value = False
            time.sleep(self.tempo)

    def to(self):
        if self.morseGPIO is not None:
            self.morseGPIO.value = True
            time.sleep(self.tempo)
            self.morseGPIO.value = False
            time.sleep(self.tempo)
        
    def sep(self):
        if self.morseGPIO is not None:
            self.morseGPIO.value = False
            time.sleep(self.tempo * 2)

if __name__ == "__main__":
    morse = MorseCodeTranslator()
    print(morse.encode("sos"))
    print(morse.decode(morse.encode("sos"), "en"))