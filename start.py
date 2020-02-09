# !/usr/bin/python
# -*- coding:utf-8 -*-
import PIL
import csv
import hashlib
import os
import re
import requests
import sys

reload(sys)
sys.setdefaultencoding('utf8')
android_manifest_str = ''
apk_source_md5 = ''


def md5(str):
    md5 = hashlib.md5()
    md5.update(str)
    return md5.hexdigest()


# 下载图标
def download(url):
    icon = requests.get(url)
    pic_format = 'png'
    try:
        pic_format = (re.match(r'.*\.(.*)', url)).group(1)
    except Exception, e:
        print '无法识别图片格式'
    with open(apk_source_md5+'/icon/logo.'+pic_format, 'wb') as icon_file:
        for chunk in icon.iter_content(100000):
            icon_file.write(chunk)
    if pic_format not in ('jpg', 'png', 'jpeg'):
        PIL.ImageFile.LOAD_TRUNCATED_IMAGES = True
        try:
            PIL.Image.open(apk_source_md5+'/icon/logo.'+pic_format).save(apk_source_md5+'/icon/logo.png')
            return apk_source_md5+'/icon/logo.png'
        except Exception, e:
            raise RuntimeError('--->图标转换格式出错')
    else:
        return apk_source_md5+'/icon/logo.'+pic_format


# 修改应用名
def rename_app(name):
    global android_manifest_str
    if android_manifest_str == '':
        with open(apk_source_md5+'/app/AndroidManifest.xml', 'r') as androidManifest:
            android_manifest_str = androidManifest.read()
    new_android_manifest_str = android_manifest_str.replace('android:label="@string/app_name"', 'android:label="' + name + '"')
    with open(apk_source_md5+'/app/AndroidManifest.xml', 'w') as newAndroidManifest:
        newAndroidManifest.write(new_android_manifest_str)


# 写入信息到csv
def write_csv(csv_reader, apk_path):
    with open('apk_packed.csv', 'ab+') as apkPackedFile:
        csv_writer = csv.writer(apkPackedFile)
        if len(csv_reader) > 3:
            csv_reader[3] = apk_path
        else:
            csv_reader.append(apk_path)
        csv_writer.writerow(csv_reader)


# 打包
def pack(csv_reader):
    apk_name = md5(csv_reader[2])
    apk_path = 'apk/' + apk_name + '.apk'
    if csv_reader[0] == '' or os.path.exists(apk_path):
        print('第' + csv_reader[0] + '个包已经打过')
        return

    print('正在从' + csv_reader[1] + '下载图标>>')
    icon_path = download(csv_reader[1])

    os.system('rm -f '+apk_source_md5+'/app/res/drawable-xxhdpi-v4/logo.*')
    icon_index = -1
    try:
        icon_index = icon_path.rindex('/')
    except:
        pass
    os.system('mv -f ' + icon_path + ' ' + apk_source_md5 + '/app/res/drawable-xxhdpi-v4/' + icon_path[icon_index+1:])
    rename_app(csv_reader[2])
    print('正在重新打包>>')
    os.system('rm '+apk_source_md5+'/app/dist/app.apk')
    os.popen('apktool b '+apk_source_md5+'/app > /dev/null 2>&1')
    if not os.path.exists(apk_source_md5+'/app/dist/app.apk'):
        raise RuntimeError('--->重新打包失败')
    print('正在签名>>')
    os.popen('jarsigner -verbose  -sigalg SHA1withRSA -digestalg SHA1 -keystore sign.keystore -storepass 123456789 -keypass 123456789 -signedjar ' + apk_path + ' ' + apk_source_md5 + '/app/dist/app.apk android > /dev/null 2>&1')
    if not os.path.exists(apk_path):
        raise RuntimeError('--->签名失败')
    print('正在写入csv>>')
    write_csv(csv_reader, apk_path)
    print('第' + csv_reader[0] + '个包打包完成')


def main():
    # 到当前目录
    os.chdir(sys.path[0])
    cur_path = os.popen('pwd').read().strip()
    os.environ['JAVA_HOME'] = cur_path + '/jdk'
    os.environ['JRE_HOME'] = cur_path + '/jdk/jre'
    os.environ['PATH'] = cur_path + '/jdk/bin:' + cur_path + '/apktool:'+os.environ['PATH']
    # print os.environ['PATH']
    if len(sys.argv) > 1:
        apk_source = sys.argv[1]
    else:
        print '没有带上csv文件路径，请加上'
        return
    if not os.path.exists(apk_source):
        print apk_source+'不存在，请检查'
        return
    if not os.path.exists('app.apk'):
        print '没有源apk（app.apk）'
        return
    global apk_source_md5
    apk_source_md5 = md5(apk_source)
    if os.path.exists(apk_source_md5+'/app'):
        os.system('rm -rf '+apk_source_md5+'/app')
    os.popen('apktool d app.apk -o '+apk_source_md5+'/app > /dev/null 2>&1')
    if not os.path.exists(apk_source_md5):
        print '反编译失败，请检查'
        return
    if not os.path.exists('sign.keystore'):
        os.popen('keytool -genkey -dname "CN=Name, OU=Unit, O=Organization, L=City, ST=Province, C=Country" -alias android -keyalg RSA -validity 2000 -keystore sign.keystore -storepass 123456789 -keypass 123456789 > /dev/null 2>&1')
    if not os.path.exists('apk'):
        os.mkdir('apk')
    if not os.path.exists(apk_source_md5+'/icon'):
        os.mkdir(apk_source_md5+'/icon')
    os.popen('apktool empty-framework-dir --force > /dev/null 2>&1')
    with open(apk_source, 'rb') as apkDownloadFile:
        csv_reader = csv.reader(apkDownloadFile)
        for line in csv_reader:
            try:
                pack(line)
            except Exception, e:
                write_csv(line, '')
                print('打第' + line[0] + '个包出错了(' + repr(e) + ')，跳过')


if __name__ == '__main__':
    main()
