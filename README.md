<p align="center">
<img height="350" width="500" border="0" src="logo.png">
</p>

# Triple T  
#### 火車時刻小幫手

![alt text](https://img.shields.io/badge/python-3.6-blue.svg)
![alt text](https://img.shields.io/badge/coverage-81%25-yellow.svg)
![alt text](https://img.shields.io/badge/License-MIT-blue.svg)

## Purpose
You are able to search TRA's and THSR's train timetable on Line. 

To use this service, click the button or scan the QR Code below to join in right now!

<a href="https://line.me/R/ti/p/%40xgy8464m"><img height="36" border="0" alt="加入好友" src="https://scdn.line-apps.com/n/line_add_friends/btn/zh-Hant.png"></a>

<img width="150" border="0" alt="QR Code" src="https://i.imgur.com/oaRmKLX.png">


## Demo

<img width="250" border="0" alt="demo1" src="https://imgur.com/CByosTF.png">
<img width="250" border="0" alt="demo2" src="https://imgur.com/A4MNSdO.png">
<img width="250" border="0" alt="demo3" src="https://i.imgur.com/XDKX69r.png">
<img width="250" border="0" alt="demo4" src="https://imgur.com/DKWeHoC.png">


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