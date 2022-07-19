
# import required modules
from selenium import webdriver
import requests
from datetime import datetime


def open_chrome():
    drive = webdriver.Chrome("/home/amogha/Downloads/chromedriver")
    drive.get("https://www.cactus2000.de/uk/unit/masshum.shtml")
    return drive

def convert2h(temperature,percentage,pressure,drive):

    temp = drive.find_element_by_name("temp")
    temp.clear()
    temp.send_keys(temperature)

    pres = drive.find_element_by_name("pres")
    pres.clear()
    pres.send_keys(pressure)

    prec = drive.find_element_by_name("rh_H2O")
    # prec.clear()
    prec.send_keys(percentage)
    # print(percentage)
    # time.sleep(8)
    but = drive.find_element_by_xpath("//input[@type='button']")
    but.click()
    # import time
    # time.sleep(1)
    hum = drive.find_element_by_name("spc_H2O")
    # print()
    ans = hum.get_attribute("value")
    reset = drive.find_element_by_xpath("//input[@type='reset']")
    reset.click()
    return ans


def call_an_api():
    api_key = "443a0e042702dbb50ca2e32194e1b326"

    base_url = "http://api.openweathermap.org/data/2.5/onecall?lat=13.5&lon=76&units=metric&"

    complete_url = base_url + "appid=" + api_key


    response = requests.get(complete_url)
    x = response.json()

    return x

def calculate_dict(x):

    arr=x
    a=[]
    for i in arr:
        if i=="daily":
            a = arr[i]
            # print(arr[i])

    d = {}

    drive = open_chrome()

    for i in a:
        date = datetime.utcfromtimestamp(i["dt"]).strftime('%Y-%m-%d')
        print(date)

        pr = float(format(i["pressure"]*0.1,".2f"))
        print("Surface Pressure",pr)
        print("Temperature",i["temp"]["day"])
        print("humi %", i["humidity"])
        hum = convert2h(i["temp"]["day"],i["humidity"],i["pressure"],drive)
        hum = float(format(float(hum),".2f"))
        print("humidity",hum)
        print(i["pop"])
        d[date] = [pr,i["temp"]["day"],hum,i["pop"]]

    drive.quit()

    return d

def main():
    x = call_an_api()
    print("weather api called !!")
    

    di = calculate_dict(x)
    print(di)
    
    fil = open("data_wth.txt", "wt")
    fil.write(str(di))
    fil.close()
    #except:
     #   print("unable to write !!")


if __name__ == '__main__':
    main()
