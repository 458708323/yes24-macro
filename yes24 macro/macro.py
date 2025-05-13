import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import datetime

print("输入您的 Chrome 配置文件路径。您可以在 Chrome 地址栏中输入 chrome://version 来查看。")
print("例如：/Users/zhaohui/Library/Application Support/Google/Chrome/Default")
chromeDirec = input()

print("请输入您想要预订的站点地址。")
print("例如: http://ticket.yes24.com/Special/42452")
targetUrl = input()

print("请输入正确的座位等级优先级。")
print("例如：R 座位、E 座位、A 座位")
targetSeats = input().split(" ")

print("请输入您的预订日期。")
print("例如（第 10 或第 11 个）：10 11")
bookingDate = input().split(" ")

print("请输入您的预订时间。")
print("例如: 18 05")
bookingTime = input().split(" ")
bookingTime = int(bookingTime[0]) * 3600 + int(bookingTime[1]) * 60

defaultTimeout = 5 # 暂停
ticketClass = "rn-bb03" # 工单按钮类名

options = webdriver.ChromeOptions() # 驱动程序设置
options.add_argument("user-data-dir=" + chromeDirec) # 设置为使用您正在使用的 Chrome 打开
driver = webdriver.Chrome(options=options) # 使用 chromedriver
driver.get(targetUrl) # 转到目标 URL

def waitUntilLoad(target, timeout = 5, refresh = False, by = By.CLASS_NAME): # 目标加载等待函数
    elem = False
    try:
        print(target + "寻找..")
        elem = WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, target)))
        print(target + "成立")
    except TimeoutException:
        elem = False
        if refresh == True:
            print("超时，正在刷新。。")
            driver.refresh() # 超时刷新
            waitUntilLoad(target, timeout, refresh)
        else:
            print("暂停")
    finally:
        return elem

while True:
    currentTime = str(datetime.datetime.now().time())
    currentTime = currentTime.split(":")
    currentTime = int(currentTime[0]) * 3600 + int(currentTime[1]) * 60 + int(currentTime[2].split(".")[0])

    if currentTime - 3 >= bookingTime:
        driver.refresh()
        driver.implicitly_wait(1)
        ticketButton = driver.find_element(By.CLASS_NAME, ticketClass)
        if ticketButton:
            break

ticket = waitUntilLoad(ticketClass) # 预订按钮
if ticket:
    print("找到预订按钮")
    ticket.click()
    print("等待预订窗口..")
    while len(driver.window_handles) <= 1:
        driver.implicitly_wait(1)
    print("前往预订窗口。")
    driver.switch_to.window(driver.window_handles[1]) # 移至新窗口
    print("您已进入预订窗口。 " + driver.title)
    
    while len(driver.find_elements(By.TAG_NAME, "td")) < 35: # 直到所有日期都加载完毕
        driver.implicitly_wait(0.1)
    print("预订日期加载中")
    selects = driver.find_elements(By.CLASS_NAME, "select") # 预订日期按钮

    # print(selects)
    foundSeat = False
    seatSpace = waitUntilLoad(target="ulSeatSpace", by=By.ID)
    seatSelectBtn = waitUntilLoad(target="btnSeatSelect", by=By.ID)
    seatTiming = waitUntilLoad(target="ulTime", by=By.ID)
    if len(selects) > 0:
        print("有可预订的日期。")
        for select in selects: # 查看所有可用日期
            targetClass = False

            link = select.find_element(By.TAG_NAME, "a")
            if link:
                datePossible = False
                for dateCheck in bookingDate:
                    if link.text == dateCheck:
                        datePossible = True
                        break

                if datePossible == True:
                    print(link.text + "可预订一日")
                    select.click()
                    while len(seatTiming.find_elements(By.TAG_NAME, "li")) < 1: # 等到时区出现
                        driver.implicitly_wait(0.1)

                    for timing in seatTiming.find_elements(By.TAG_NAME, "li"):
                        print(timing.text + " 正在搜索..")
                        timing.click() # 选择时区
                        time.sleep(0.5)
                        while len(seatSpace.find_elements(By.TAG_NAME, "li")) < 1: # 等待直到出现您的座位等级
                            driver.implicitly_wait(0.1)
                        
                        # 提前查看是否有可预订的座位
                        print("座位等级目标{}".format(len(targetSeats)))
                        for seatClass in targetSeats: # 查看所有目标席位
                            for seat in seatSpace.find_elements(By.TAG_NAME, "li"):
                                # WebDriverWait(driver, defaultTimeout).until(EC.presence_of_element_located((By.TAG_NAME, "strong")))
                                currentClass = seat.find_element(By.TAG_NAME, "strong").text
                                seatText = seat.find_element(By.TAG_NAME, "span") # 当前座位容量
                                current = seatText.text.split("석")[0]
                                # print("目标:" + seatClass + "查看-" + currentClass + " " + current + "석")
                                if seatClass == currentClass: # 检查是否有空位以及是否是目标座位
                                # if current != "0" and seatClass == currentClass: # 检查是否有空位以及是否是目标座位
                                    print(seatClass + " 今天 {}석 남았습니다.".format(current))
                                    targetClass = seatClass # 提前选择座位
                                    break

                        # 如果有可预订的座位，开始选择座位
                        if targetClass != False:
                            print(targetClass + " 按等级选择区域。")
                            seatSelectBtn.click() # 点击座位选择按钮
                            iframe = waitUntilLoad(target="ifrmSeatFrame", by=By.NAME)
                            time.sleep(1)
                            driver.switch_to.frame(iframe) # 前往预订 iframe
                            seatPosList = waitUntilLoad(target="ulLegend", by=By.ID) # 按座位等级划分的座位列表
                            seatSelected = waitUntilLoad(target="liSelSeat", by=By.ID) # 已选座位列表
                            booking = waitUntilLoad(target="booking") # 选择完成按钮
                            while len(seatPosList.find_elements(By.TAG_NAME, "div")) < 1: # 座位等级等候
                                driver.implicitly_wait(0.1)
                            for seat in seatPosList.find_elements(By.TAG_NAME, "div"): # 打开右侧的座位等级列表即可查看
                                print(seat.find_element(By.TAG_NAME, "p").text.split(" ")[0] + " 正在搜索..")
                                if seat.find_element(By.TAG_NAME, "p").text.split(" ")[0] == targetClass: # 如果您要查找的座位等级正确
                                    seat.click() # 选择合适的座位等级
                                    seatLayer = waitUntilLoad(target="seat_layer") # 座位区 UL 路
                                    while len(seatLayer.find_elements(By.TAG_NAME, "li")) < 1: # 座位区列表等候
                                        driver.implicitly_wait(0.1)
                                    print("座位区列表已加载")
                                    seatAreaList = seatLayer.find_elements(By.TAG_NAME, "li") # 该舱位座位列表
                                    for seatArea in seatAreaList: # 查看所有座位区
                                        areaCurrent = seatArea.text.split("(")[1].split("석")[0] # 该区域席位数量
                                        if areaCurrent != "0": # 如果该区域有座位
                                            print(seatArea.text + " 选定")
                                            seatArea.click() # 单击该区域的按钮

                                            # 前往区域座位列表窗口进行预订
                                            seatList = waitUntilLoad(target="divSeatArray", by=By.ID) # 座位位置列表
                                            while len(seatList.find_elements(By.TAG_NAME, "div")) < 1: # 座位位置列表等候
                                                driver.implicitly_wait(0.1)
                                            for seatPos in seatList.find_elements(By.TAG_NAME, "div"):
                                                seatTitle = seatPos.get_attribute("title")
                                                if len(seatTitle) != 0:
                                                    seatPos.click() # 点击座位位置
                                                    driver.implicitly_wait(0.1)
                                                    selected = seatSelected.find_elements(By.TAG_NAME, "p")
                                                    if len(selected) > 0:
                                                        print(seatTitle + " 选定")
                                                        booking.click() # 点击座位选择按钮
                                                        foundSeat = True
                                                        break

                                            if foundSeat == True:
                                                break
                                    print("座位搜索完成")
                                    break # 我检查了座位，所以我退出了
                        else:
                            print("您目标班级已无空位。请移至下一日期。.")

                        if foundSeat == True:
                            break
                    if foundSeat == True:
                        break
                
        if foundSeat == True:
            print("您已选择座位。请付款。.")
            while True:
                time.sleep(600)
    else:
        print("没有可用的日期。")
else:
    print("找不到预订按钮。")