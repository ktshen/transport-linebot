<p align="center">
<img height="350" width="500" border="0" src="logo.png">
</p>

# Triple T  
#### 火車時刻小幫手

![alt text](https://img.shields.io/badge/python-3.6-blue.svg)
![alt text](https://img.shields.io/badge/coverage-81%25-yellow.svg)
![alt text](https://img.shields.io/dub/l/vibe-d.svg)

## Purpose
You are able to search TRA's and THSR's train timetable on Line. 

To use this service, click the button or scan the QR Code below to join in right now!

<a href="https://line.me/R/ti/p/%40xgy8464m"><img height="36" border="0" alt="加入好友" src="https://scdn.line-apps.com/n/line_add_friends/btn/zh-Hant.png"></a>

<img width="150" border="0" alt="demo4" src="https://i.imgur.com/oaRmKLX.png">


## Example

```text

【使用範例】
> hi~ 我是火車時刻機器人
輸入: 大寫或小寫T 就可以呼叫我喔

>> t

> 請選擇查詢交通類型
  ------台鐵-------
  ------高鐵-------

>> （點擊台鐵)

> 請輸入起程站

>> 新竹

> 請輸入目的站

>> 臺北

> 選擇搭乘時間: 新竹 → 臺北

>> (點擊選擇時間)

> 適合班次如下  新竹 → 臺北
車次   車種  開車時間  抵達時間
0144  自強     20:48        22:01
1264  區間     20:53        22:26
1272  區間     21:08        22:49
0146  自強     21:27        22:35
2254  區間     21:34        23:07
0150  自強     22:07        23:17
1278  區間     22:10        23:42
0524  莒光     22:22        23:50
1274  區間     22:27        23:58


```

## Development

### Setup
1. Duplicate ".env.example" file and rename it to ".env"
2. Fill up the variable in .env file
3. Create a file name "ptx_keys.txt" and add ID Key pair on every two line (if more than one pair)

### Run

Using Docker
```
docker-compose build
docker-compose up
```

### Testing
- In ".env", set POSTGRES_DB=testing
- Run test in docker container
```
docker-compose -f testing-compose.yml build
docker-compose -f testing-compose.yml up
```
- When the test is finished, <ctrl+c> to close it

## License

MIT