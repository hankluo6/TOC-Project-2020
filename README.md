# TOC Project 2020

## 前言

目前市面上的交通工具動態 APP 大多以單一交通工具為主，但在生活上常常會遇到需要轉乘的情況發生，故希望能設計一個聊天機器人，串接[公共運輸整合資訊流通服務平臺](https://ptx.transportdata.tw/PTX/) API，並統整常見的交通工具時刻表來幫助我們更快速的規劃行程。

---

## 功能

* 輸入任意文字啟動，並支援三種常用大眾運輸工具

    ![](https://i.imgur.com/9lHM8Lb.png)

* 分別有以下功能
    * 公車動態
    * 台鐵時刻表
    * 高鐵時刻表


### 公車

![](https://i.imgur.com/fezfZs8.png)

提供兩種方法搜尋公車，支援台南地區所有公車站

* 以站牌搜尋
    
    列出可以到達輸入站牌的路線以供選擇
    ![](https://i.imgur.com/1Ie2Dxa.png)
* 以路線搜尋

    列出輸入路線可到達的所有站牌以供選擇
    ![](https://i.imgur.com/C1KYu7r.png)

* 輸入欲查詢的方向

    ![](https://i.imgur.com/gyRbiru.png)

* 列出該路線時刻表資料，搜尋的站牌會顯示在中間，方便查看前站及後站的時間情形

### 火車


* 輸入起訖站
    ![](https://i.imgur.com/ONiOt1f.png)

* 選擇時間
    ![](https://i.imgur.com/tJx6PWw.png)

* 提供視覺化結果，狀態欄位顯示該列車的誤點情形
    ![](https://i.imgur.com/RWvMiIA.png)

### 高鐵

* 輸入起訖站
    ![](https://i.imgur.com/xE9xrEL.png)

* 選擇時間
    ![](https://i.imgur.com/KUkrpqS.png)

* 提供時間表，並顯示該車是否有剩餘座位可訂購
    ![](https://i.imgur.com/N3G5hbT.png)

---

## 使用說明

* 輸入 `reset` 返回到開頭選單
* 依據指示文字回傳訊息

---

## Finite State Machine

![](https://i.imgur.com/btBMubG.png)

---

## Try it!

![](https://i.imgur.com/YpyUbmN.png)
