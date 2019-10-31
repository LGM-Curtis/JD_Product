"""
Author:Curtis
Time:2019年10月31日 11:33:53
爬取京东零食商品信息（无需登录，适合新手）
爬取的结果保存在MongoDB
爬取的关键词可在config文件中进行修改
使用了selenium和Chrome爬取京东
流程框架：
1.搜索关键字
利用Selenium驱动浏览器搜索关键字，得到查询后的商品列表
2.分析页码并翻页
得到商品页码数，模拟翻页操作，得到后续的商品列表
3.分析提取商品信息
利用css选择器进行筛选
4.存储至MongoDB
将抓取的商品信息存储至MongoDB中，供后期数据分析使用
"""
from selenium.webdriver import Chrome
from config import *
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from time import sleep
from selenium.common.exceptions import NoSuchElementException
import pymongo


browser = Chrome()
url = "http://www.jd.com"
wait = WebDriverWait(browser, 10)
client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]


def next_page(browser, wait, page_num):

    # 确认完整加载网页，下拉到底部
    while len(browser.find_elements_by_class_name('gl-item')) < 60:
        browser.execute_script('window.scrollTo(0, document.body.scrollHeight)')
        sleep(1)
    print("[+] 第{}加载完成".format(page_num))

    # 解析数据
    parse_page(page_num, browser)

    # 下一页
    page_num += 1
    if page_num > END_PAGE:
        print('前{}页爬取成功'.format(END_PAGE))
        return

    # 等待下一页输入框加载完成
    wait.until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, '#J_bottomPage > span.p-skip > input')
        )
    )
    # print("[+] 下一页输入框加载完成")

    # 等待下一页输入框跳页按钮加载完成
    wait.until(
        EC.element_to_be_clickable(
            (By.CSS_SELECTOR, '#J_bottomPage > span.p-skip > a')
        )
    )
    # print("[+] 跳页按钮加载完成")

    # 输入页码
    input_ = browser.find_element_by_css_selector('#J_bottomPage > span.p-skip > input')
    input_.clear()
    input_.send_keys(page_num)
    # print("[+] 输入页码完成")

    # 点击跳页
    input_.send_keys(Keys.ENTER)
    # print("[+] 点击跳页完成")

    # 等待下一页加载完成
    wait.until(
        EC.text_to_be_present_in_element(
            (By.CSS_SELECTOR, '#J_bottomPage > span.p-num > a.curr'),
            str(page_num)
        )
    )
    # print("[+] 下一页加载完成")

    # 跳下一页
    next_page(browser, wait, page_num)


def parse_page(page_num, browser):
    print("[+] 开始解析第{}页数据".format(page_num))
    items = browser.find_elements_by_class_name('gl-item')
    for item in items:
        # 在前面的基础上继续解析, 如果那个属性没有提取到，保证其他属性可以正常提取
        try:
            title = item.find_element_by_css_selector("div.p-name > a > em").text
        except NoSuchElementException:
            title = None
        try:
            price = item.find_element_by_css_selector("div.p-price > strong > i").text
        except NoSuchElementException:
            price = None
        try:
            store = item.find_element_by_css_selector("div.p-shop > span > a").text
        except NoSuchElementException:
            store = None
        try:
            link = item.find_element_by_css_selector("div.p-img > a").get_attribute("href")
        except NoSuchElementException:
            link = None
        try:
            comment = item.find_element_by_css_selector(".p-commit a").text
        except NoSuchElementException:
            comment = None
        product_message = {
            '商品名称': title,
            '价格': price+'元',
            '店铺': store,
            '商品链接': link,
            '累计评价': comment
        }
        print(product_message)
        save_to_mongo(product_message)
    print("[+] 解析第{}页数据完成".format(page_num))


def search(browser, url, keyword, wait):
    # 打开链接
    browser.get(url)
    # 等待加载输入框完成,等待id为q的加载
    wait.until(
        EC.presence_of_element_located(
            (By.ID, 'key')
        )
    )
    # print("[+] 搜索框加载完成")

    # 等待加载搜索按钮完成,等待css选择器满足条件,
    wait.until(
        EC.element_to_be_clickable(
            (By.CSS_SELECTOR, '#search > div > div.form > button > i')
        )
    )
    # print("[+] 搜索按钮加载完成")

    # 输入关键字
    input_ = browser.find_element_by_id('key')
    input_.send_keys(keyword)
    # print("[+] 输入关键字完成")

    # 点击搜索
    botton = browser.find_element_by_css_selector('#search > div > div.form > button > i')
    botton.click()
    print("[+] 点击搜索完成")

    # 翻页
    page_num = 1
    next_page(browser, wait, page_num)


def save_to_mongo(result):
    try:
        if db[MONGO_TABLE].insert(result):
            print('成功存储至MONGODB')
    except Exception:
        print('存储失败')


def main():
    search(browser, url, KEYWORD, wait)


if __name__ == '__main__':
    main()
