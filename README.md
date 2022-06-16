# 通过云函数运行 Headless Chromium


## 简介

SCF中可以执行 `Chromium` 进行网页访问等操作，有两种使用方法：

- 把 Chromium 作为Layer进行安装
- 把 Chromium 放到共享存储CFS从而避免代码包的限制

-----

注意⚠️：: 初始化的 `browser` 实例在多次请求之前是可以复用的，没必要每次都要新建一个浏览器实例，可以通过缓存 `browser` 到全局变量中实现多次请求之间复用，只有在全局变量未设置的时候再进行初始化。


两种方式 `chrome` 可执行文件的位置不同，需要修改对应的代码配置：

index.py

```python
async def test():
    
    # Config for headless mode
    browser = await launch(headless=True, 
        userDataDir= '/tmp/pyppeteer/', 
        logLevel=logging.ERROR, 
        # 把 chrome 提前放到层中并进行绑定，同时配置环境变量禁止自动下载
        # 如果采用层的方式安装，二进制文件在 /opt 目录
        # 如果采用CFS的方式安装，二进制文件在 /mnt 目录
        executablePath='/opt/chrome-linux/chrome', 
        env={'PUPPETEER_SKIP_CHROMIUM_DOWNLOAD':'true'}, 
        args=['--no-sandbox', '--window-size=1920,1080', '--disable-infobars', '--disable-dev-shm-usage'])

    page = await browser.newPage()
    await page.goto('http://baidu.com')
    title = await page.title()
    print("Page title is " + title)
    await browser.close()
```


## 部署函数

1. 创建Zip包

    ```bash
    zip -r headless_chrome_python.zip . -x "*vendor*" -x "*.git*"
    ```
2. 创建 Web 函数

    ```bash
    函数类型	    Event 函数
    运行环境	    Python 3.7
    内存	    512MB
    执行超时时间  10秒
    ```

3. 自动在线安装依赖

    通过 Shell 的方式在终端按照

    ```bash
    cd src
    pip3 install -r requirements.txt -t vendor
    ```
4. 重新部署

## 下载 Chromium

**备注：也可以直接下载经过测试验证的 chromium 二进制文件:**

chrome_r961656: [Download LInk](https://github.com/ServerlessBravo/scf-python-headless-chrome-demo/releases/download/v1.0/chrome_r961656.zip)

下载之后，可以用于创建 Layer 并绑定到函数进行使用。

### 1.找到对应的 `Chromium` 版本

⚠️ 注意下载的版本和 `puppeteer` 之间的 [映射关系](https://github.com/puppeteer/puppeteer/blob/main/versions.js):

```js
    ['100.0.4889.0', 'v13.5.0'],
    // 该版本为Demo的Pupeteer版本
    ['99.0.4844.16', 'v13.2.0'],
    ['98.0.4758.0', 'v13.1.0'],
    ['97.0.4692.0', 'v12.0.0'],
    ['93.0.4577.0', 'v10.2.0'],
    ['92.0.4512.0', 'v10.0.0'],
```

### 2.找到对应的 `Bulild` 

- 链接：https://vikyd.github.io/download-chromium-history-version/#/
- 搜索版本对应的 `Build`

  ![Build 链接](https://user-images.githubusercontent.com/251222/158581688-b5a390aa-e969-4181-a8cc-428c65bf839a.png)

- 获得下载链接，例如：[r961656](https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2F961656%2Fchrome-linux.zip)

### 3.下载对应文件：

![](https://user-images.githubusercontent.com/251222/158582196-fb7c90bc-75b0-40f1-9d3a-cbf78611781f.png)


## 通过层安装

### 1. 创建层

通过控制台创建有50MB的限制，需要选择通过COS创建Layer的方式，提前把 Zip 文件放到 COS，然后按照下面的方式创建 Layer：

***备注：替换绑定语言为Python版本*** 


![](https://user-images.githubusercontent.com/251222/158583758-530e1d1d-41a1-4e38-82c4-3eb1f6c59aa3.png)

### 2. 绑定层

![](https://user-images.githubusercontent.com/251222/158590530-f592f3d2-a47a-421b-bc5d-230c963178a4.png)


## 通过CFS 安装

- ⚠️ 如果总的文件大小超过500MB，需要把 Chromium 放到 CFS上，减少代码包的体积
- 创建CFS之后，可以通过虚拟机挂载 CFS，然后把下载的Zip包上传到对应的目录
- 然后配置函数，函数启动的时候自动挂载 CFS:

  ![](https://user-images.githubusercontent.com/251222/158591094-ef6d5595-ee95-4594-b99c-0e85ee98e1d8.png)

## 测试

触发函数，查看函数日志：

```
Page title is 百度一下，你就知道

client > Frame(fin=True, opcode=<Opcode.TEXT: 1>, data=b'{"id": 17, "method": "Browser.close", "params": {}}', rsv1=False, rsv2=False, rsv3=False)
...
client x code = 1006, reason = [no reason]

百度一下，你就知道

Response RequestId: 3346b9ff-f4d7-492f-9b89-f4d46a3c43f5 RetMsg: ""
```


## 其他

### 开启详细日志模式

配置环境变量：

```bash
DEBUG=puppeteer:*

```

### CFS 写入出错

报错信息：

```bash
 [Error: EACCES: permission denied, open '/mnt/xxx.jpg'] {

  errno: -13,

  code: 'EACCES',

  syscall: 'open',

  path: '/mnt/xxx.jpg'

}

```

检查步骤：

- 查看函数的角色配置：查看云函数的执行角色配置，是否设置为 `SCF_QcsRole`
- 查看角色权限：在 `CAM` 查看该角色是否关联了 CFS 的写入权限
- 查看文件权限：在一台虚拟机挂载 CFS 之后，运行命令更改文件的用户名和用户组

```bash

## 其中 10000:10000 为云函数读写 CFS 文件时的用户名和用户组Id

chmod 10000:10000 -R /mnt/foler
ls -al /mnt/folder

```
