# -*- coding: utf-8 -*-
import time
#等待元素控件
from selenium.webdriver.support.ui import WebDriverWait
from appium import webdriver
from handle_mysql import MySQL
import pickle
import os

desired_caps = {
  "platformName": "Android",
  "platformVersion": "7.1.2",
  "deviceName": "127.0.0.1:62028",
  "appPackage": "com.luojilab.player",
  "appActivity": "com.luojilab.business.welcome.SplashActivity",
  "noReset": True,
  # "unicodeKeyboard": True, # 需要输入时用这个
  # "resetKeyboard": True,  # 还原输入法
  "automationName": "UiAutomator2"
}

# 本地的appium服务器
server = 'http://localhost:4723/wd/hub'
driver = webdriver.Remote(server, desired_caps)
wait = WebDriverWait(driver, 10)


def get_size(driver):
    x = driver.get_window_size()['width']
    y = driver.get_window_size()['height']
    return (x, y)

def handle_dedao(driver):
    try:
        # 去除更新按钮，如果没找到更新按钮，就抛异常了，然后pass
        if wait.until(lambda x: x.find_element_by_xpath("//android.widget.Button[@resource-id='com.luojilab.player:id/button2']")):
            driver.find_element_by_xpath("//android.widget.Button[@resource-id='com.luojilab.player:id/button2']").click()
    except:
        pass
    # 点击已购买按钮
    # if wait.until(lambda x: x.find_element_by_id("//android.widget.ImageView[@resource-id='com.luojilab.player:id/threeImageView']")):
    if wait.until(lambda x: x.find_element_by_id("com.luojilab.player:id/threeImageView")):
        driver.find_element_by_id("com.luojilab.player:id/threeImageView").click()

    # 点击课程
    if wait.until(lambda x: x.find_element_by_xpath("//android.widget.TextView[@resource-id='com.luojilab.player:id/tv_course']")):
        driver.find_element_by_xpath("//android.widget.TextView[@resource-id='com.luojilab.player:id/tv_course']").click()

    # 点击课程里面的最新购买
    if wait.until(lambda x: x.find_element_by_id("com.luojilab.player:id/nearBuyBtn")):
        driver.find_element_by_id("com.luojilab.player:id/nearBuyBtn").click()

    # 得到正在更新列表，不爬取这些正在更新列表
    no_crawl_columns = []
    get_no_crawl_columns(driver, no_crawl_columns, '正在更新')
    # get_no_crawl_columns(driver, no_crawl_columns, '其他')
    print(no_crawl_columns)

    # 从数据库中取出爬取完毕的栏目，去重
    def f(x):
        return x[0]
    db_crawled_finished_columns = mysql.select('tb_column', ['column_name'], 'crawl_finished = 1')
    # print(result)
    no_crawl_columns += list(map(f, db_crawled_finished_columns))
    print('完整的no_crawl_columns：', no_crawl_columns)



    # 点击全部列表
    if wait.until(lambda x: x.find_element_by_xpath("//android.widget.TextView[@text='全部 133']")):
        driver.find_element_by_xpath("//android.widget.TextView[@text='全部 133']").click()


    while True:
        # 循环当前页面的栏目列表
        crawl_columns_list(driver, no_crawl_columns)
        # print(db_crawled_finished_columns)

        # 拖动前临时变量
        temp = driver.page_source

        # 拖动
        if wait.until(lambda x: x.find_element_by_class_name("android.support.v7.widget.RecyclerView")):
            # if wait.until(lambda x: x.find_element_by_id("com.luojilab.player:id/rv_flat_list")):
            rv_flat_list = driver.find_element_by_class_name("android.support.v7.widget.RecyclerView")
            # rv_flat_list = driver.find_element_by_id("com.luojilab.player:id/rv_flat_list")
            columns = rv_flat_list.find_elements_by_class_name("android.widget.LinearLayout")

            origin_el = columns[1]
            destination_el = columns[len(columns) - 2]
            driver.drag_and_drop(destination_el, origin_el)

        if temp == driver.page_source:
            break



def crawl_columns_list(driver, no_crawl_columns):
    '''
    循环点击当前页面的所有栏目
    :param driver:
    :param no_crawl_columns: 这是点击过的栏目，不循环点击
    :return:
    '''
    if wait.until(lambda x: x.find_element_by_xpath("//android.support.v7.widget.RecyclerView[@resource-id='com.luojilab.player:id/rv_content']")):
        columns = driver.find_element_by_xpath("//android.support.v7.widget.RecyclerView[@resource-id='com.luojilab.player:id/rv_content']")
        column_list = columns.find_elements_by_id("com.luojilab.player:id/home_newsub_item")
        for column in column_list:
            try:
                column_name = column.find_element_by_id("com.luojilab.player:id/column_name").get_attribute("text")
                if column_name not in no_crawl_columns:
                    # 点击栏目
                    column.find_element_by_id("com.luojilab.player:id/column_name").click()
                    time.sleep(2)

                    # 如果出现完成奖章页面
                    if '如此优秀的你学完了' in driver.page_source:
                        driver.back()

                    crawl_column(driver, crawled_article, 0)
                    driver.back()
                    no_crawl_columns.append(column_name)
                    crawl_columns_list(driver, no_crawl_columns)
            except:
                pass

def crawl_column(driver, crawled_article, token = 0):
    if token == 0:
        # 向上滑动，去到最顶端
        if wait.until(lambda x: x.find_element_by_id("com.luojilab.player:id/tv_sort")):
            sort_btn = driver.find_element_by_id("com.luojilab.player:id/tv_sort")
            sort_btn.click()
            time.sleep(3)
            sort_btn.click()
            time.sleep(1)
            # 向上滑动窗口
            l = get_size(driver)
            x1 = int(l[0] * 0.5)
            y1 = int(l[1] * 0.9)
            y2 = int(l[1] * 0.5)
            n = 0
            while n < 10:
                driver.swipe(x1, y2, x1, y1)
                time.sleep(0.3)
                n += 1

    # if wait.until(lambda x: x.find_element_by_id("com.luojilab.player:id/rv_flat_list")):
    if wait.until(lambda x: x.find_element_by_class_name("android.support.v7.widget.RecyclerView")):
        # rv_flat_list = driver.find_element_by_id("com.luojilab.player:id/rv_flat_list")
        rv_flat_list = driver.find_element_by_class_name("android.support.v7.widget.RecyclerView")
        articles = rv_flat_list.find_elements_by_class_name("android.widget.LinearLayout")
        for article in articles:
            try:
                title = article.find_element_by_id("com.luojilab.player:id/tv_title").get_attribute("text")
                if title not in crawled_article:
                    # 点击进去爬取
                    article.click()
                    time.sleep(3)
                    # 进行文章爬取
                    crawl_article(driver)
                    # time.sleep(3)

                    driver.back()
                    crawled_article.append(title)
                    with open('token.txt', 'wb') as f:
                        pickle.dump(crawled_article, f)
                    crawl_column(driver, crawled_article, token + 1)
            except:
                pass

def crawl_article(driver):
    l = get_size(driver)
    x1 = int(l[0] * 0.5)
    y1 = int(l[1] * 0.75)
    y2 = int(l[1] * 0.25)
    while True:
        temp = driver.page_source
        driver.swipe(x1, y1, x1, y2)
        time.sleep(0.2)
        if temp == driver.page_source and '点击加载留言' in driver.page_source:
            break
    # db_crawled_unfinished_columns = mysql.select('tb_column', ['column_name'], 'crawl_finished = 0')

def get_no_crawl_columns(driver, no_crawl_columns, target):
    if wait.until(lambda x: x.find_element_by_xpath("//android.view.ViewGroup")):
        view_group = driver.find_element_by_xpath("//android.view.ViewGroup")
        column_tabs = view_group.find_elements_by_class_name("android.widget.TextView")

        for column_tab in column_tabs:
            if target in column_tab.get_attribute("text"):
                column_tab.click()

                while True:
                    temp = driver.page_source

                    column_names = driver.find_elements_by_id("com.luojilab.player:id/column_name")
                    for column_name in column_names:
                        try:
                            no_crawl_columns.append(column_name.get_attribute("text"))
                        except:
                            pass
                    origin_el = column_names[0]
                    destination_el = column_names[len(column_names) - 2]

                    driver.drag_and_drop(destination_el, origin_el)

                    if temp == driver.page_source:
                        break
                print(no_crawl_columns)
                reset_columns(driver)

# 重置column列表
def reset_columns(driver):
    # 重置列表
    driver.back()
    # 点击课程
    if wait.until(lambda x: x.find_element_by_xpath(
            "//android.widget.TextView[@resource-id='com.luojilab.player:id/tv_course']")):
        driver.find_element_by_xpath(
            "//android.widget.TextView[@resource-id='com.luojilab.player:id/tv_course']").click()

    # 点击课程里面的最新购买
    if wait.until(lambda x: x.find_element_by_id("com.luojilab.player:id/nearBuyBtn")):
        driver.find_element_by_id("com.luojilab.player:id/nearBuyBtn").click()



if __name__ == '__main__':

    # 做爬取记录，爬取过的文章不再爬取
    if os.path.exists('token.txt'):
        with open('token.txt','rb') as f:
            crawled_article = pickle.load(f)
    else:
        crawled_article = []
    print(crawled_article)

    mysql = MySQL()
    try:
        mysql.get_connection()
        handle_dedao(driver)
    finally:
        mysql.close_connection()
