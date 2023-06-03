from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage
from model import Course, LinkedList
import threading
import json
import time
import datetime
import random
import pytz
import csv

app = Flask(__name__)

#line_bot的Token、Channel Secret
line_bot_api = LineBotApi('c/2axBtAYZQkLSDHOVVnBLXdJLs0RabigC1tvKtEbNb8/8P6f14yLRrfAQKKiUH6KgcdQp+bDHEyI7qP0/zHpvJflIKqIFRl/l2fbVvQS3txUy1LcNpHR/iCIjjmshTzt5zQQrjEGbsLx2MorQ6CcAdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('124fa4bcf00b1166c14eeea6bc6f2d00')

# 1A2B遊戲
ansNum = []
gameMod = False

# 初始化鏈結
headNode = None
curNode = None

# 讀取課程資訊
with open('courseInfo.csv', mode='r') as file:
   reader = csv.DictReader(file)
   for row in reader:
      if headNode == None:
         headNode = LinkedList(Course(row['name'], row['day'], row['startTime'], row['endTime'], row['location']))
         curNode = headNode
      else:
         curNode.next = LinkedList(Course(row['name'], row['day'], row['startTime'], row['endTime'], row['location']))
         curNode = curNode.next
   curNode = headNode
      
# 取得當前的系統時間
curTime = datetime.datetime.now()
# 設定 GMT+8 的時區
timezone = pytz.timezone("Asia/Taipei")
# 將系統時間轉換為 GMT+8 時區的時間
curTime = curTime.astimezone(timezone)
curWeekday = curTime.weekday() + 1
curHour = curTime.hour
curMinute = curTime.minute
# 初始化鏈結定位
while True:
   tempNode = curNode.value
   # 將LinkedList的資料轉成時間
   nodeTime = datetime.datetime.strptime(tempNode.startTime, "%H:%M")
   nodeHour = nodeTime.hour
   nodeMinute = nodeTime.minute
   if curWeekday == 6 or curWeekday == 7:
      break
   if curWeekday == tempNode.day and (curHour * 60 + curMinute) - (nodeHour * 60 + nodeMinute) > 30:
      break
   curNode = curNode.next

# 檢查課程時間
def checkTime():
   global headNode, curNode, line_bot_api
   while True:
      # 取得LinkedList的資料
      tempNode = curNode.value
      # 取得當前的系統時間
      curTime = datetime.datetime.now()
      # 設定 GMT+8 的時區
      timezone = pytz.timezone("Asia/Taipei")
      # 將系統時間轉換為 GMT+8 時區的時間
      curTime = curTime.astimezone(timezone)
      curWeekday = curTime.weekday() + 1
      curHour = curTime.hour
      curMinute = curTime.minute
      print(f"系統時間： Week: {curWeekday} Hour: {curHour} Minute: {curMinute}")
      # 將LinkedList的資料轉成時間
      nodeTime = datetime.datetime.strptime(tempNode.startTime, "%H:%M")
      nodeHour = nodeTime.hour
      nodeMinute = nodeTime.minute
      print(f"課程時間： Week: {tempNode.day} Hour: {nodeHour} Minute: {nodeMinute}")
      print()
      #判斷通知時間
      if int(curWeekday) == int(tempNode.day) and (nodeHour * 60 + nodeMinute) - (curHour * 60 + curMinute) == 30:
         messageStr = f"課程通知\n課程名稱：{tempNode.name}\n教室：{tempNode.location}\n上課時間：{tempNode.startTime}\n下課時間：{tempNode.endTime}\n祝您上課愉快！"
         line_bot_api.push_message('U3b706ee724da7f1ccaf51c2fb357d507', TextSendMessage(text=messageStr))
         #陣列指標往後移
         curNode = curNode.next
         if curNode == None:
            curNode = headNode
      # 系統休息10秒
      time.sleep(10)

# 查詢天氣
def checkWeather():
   pass

# 1A2B遊戲
def playGame(msg):
   global ansNum, gameMod
   numList = []
   countA = 0
   countB = 0
   try:
      for i in range(len(msg)):
         numList.append(int(msg[i]))
      for i in range(max(len(msg), len(ansNum))):
         if numList[i] == ansNum[i]:
            countA += 1
         elif numList[i] in ansNum:
            countB += 1
      if countA == 4:
         message = f"恭喜答對，答案是{msg}\n要再次遊玩的話，請重新輸入「1A2B遊戲」"
         gameMod = False
      else:
         message = f"{countA}A{countB}B"
   except:
      message = "輸入格式有誤，請重新輸入"
   print(f"輸出結果:{message}")
   return message

# 初始化1A2B遊戲數字
def initGame():
   global ansNum
   # 產生4個0~9之間的數，數字不會重複
   ansNum = random.sample(range(10), 4)
   print(f"答案：{ansNum}")

# 接受使用者訊息
@app.route("/", methods=['POST'])
def linebot():
   global line_bot_api, handler, gameMod
   body = request.get_data(as_text=True)
   json_data = json.loads(body)
   try:
      signature = request.headers['X-Line-Signature']
      handler.handle(body, signature)
      # 讀取回應Token
      replyTk = json_data['events'][0]['replyToken']
      # 讀取使用者輸入內容
      userMsg = json_data['events'][0]['message']['text']
      if gameMod:
         if userMsg == "退出":
            gameMod = False
            message = "遊戲退出"
            line_bot_api.reply_message(replyTk, TextSendMessage(text=message))
         else:
            message = playGame(userMsg)
            line_bot_api.reply_message(replyTk, TextSendMessage(text=message))
      else:
         # 判斷使用者輸入內容
         if userMsg == "查詢天氣":
            message = checkWeather()
         elif userMsg == "1A2B遊戲":
            gameMod = True
            initGame()
            message = "1A2B遊戲開始\n請輸入4個數字\n如果要退出的話請輸入「退出」"
            line_bot_api.reply_message(replyTk, TextSendMessage(text=message))
   except:
      print('error')
   return 'OK'

if __name__ == "__main__":
   # 定期偵測時間，每秒檢查一次
   check_thread = threading.Thread(target=checkTime)
   check_thread.start()

   # 啟動應用程式
   app_thread = threading.Thread(target=app.run)
   app_thread.start()