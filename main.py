from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from time import sleep
import configparser
import base64
import requests

def main():
    url = 'https://cart.books.com.tw/member/login'

    conf = configparser.ConfigParser()
    conf.read('config.ini', encoding='utf-8') # 这里要加utf-8, 否则会报错, 默认gbk
    config_section  = 'config'
    username = conf.get(config_section, 'username') # 帐号
    password = conf.get(config_section, 'password') # 密码
    api_key = conf.get(config_section, 'api_key') 

    options = webdriver.ChromeOptions()
    options.add_experimental_option('detach', True)  # 不自动关闭浏览器
    options.add_experimental_option('prefs', { 
        "profile.default_content_setting_values.notifications": 2 # 防止跳出通知
    })
    browser = webdriver.Chrome(service = Service(ChromeDriverManager().install()), options = options)
    browser.maximize_window() # 窗口最大化
    browser.get(url)

    # toDataURL将内容转成图片, canvas是h5标签的容器, 可在里面绘图
    img_base64 = browser.execute_script('''
        var el = arguments[0];
        var canvas = document.createElement('canvas');
        canvas.width = el.width;
        canvas.height = el.height;
        canvas.getContext('2d').drawImage(el, 0, 0);
        return canvas.toDataURL('image/jpeg').substring(22);
    ''', browser.find_element(By.XPATH, "//*[@id='captcha_img']/img"))
    with open('captcha_login.png', 'wb') as image:
        image.write(base64.b64decode(img_base64))

    # 下载该验证码图片
    file = {'file': open('captcha_login.png', 'rb')} 

    data = {
        'key': api_key,
        'method': 'post'
    }
    # 验证码提交地址
    res = requests.post('http://2captcha.com/in.php', files = file, data = data)
    print(f'response:{res.text}')
    if res.ok and res.text.find('OK') > -1:
        captcha_id = res.text.split('|')[1]
        for i in range(10):
            # 获取辨识结果
            resp = requests.get(f'http://2captcha.com/res.php?key={api_key}&action=get&id={captcha_id}')
            print(f'response:{resp.text}')

            if resp.text.find('OK') > -1:
                captcha_text = resp.text.split('|')[1] # 获取辨识结果
                el_username = browser.find_element(By.ID, 'login_id')
                el_password = browser.find_element(By.ID, 'login_pswd')
                el_captcha = browser.find_element(By.ID, 'captcha')
                btn_login = browser.find_element(By.ID, 'books_login')
                el_username.send_keys(username)  
                el_password.send_keys(password) 
                el_captcha.send_keys(captcha_text)
                btn_login.click()  # 点击登入
                break
            elif resp.text.find('CAPCHA_NOT_READY') > -1: # 未辨识完成
                sleep(3)
        else:
            print('获取验证码错误')
    else:
        print('提交验证码错误')
    browser.close() # 关闭当前tab选项卡, quit关闭整个浏览器

if __name__ == '__main__':
    main()