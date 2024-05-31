# -*- encoding: utf-8 -*-
'''
@File    :   flomo2Obsidian.py
@Time    :   2024/05/31 23:12:37
@Author  :   Lin Guo Guang 
@Version :   1.0
@Contact :   739217783@qq.com
@License :   (C)Copyright 2017-2018, Liugroup-NLPR-CASIA
@Desc    :   None
'''

# here put the import lib


import os
import re
import shutil
import time

from bs4 import BeautifulSoup


def c_yaml(x, c_time, tags=None):
    """
    创建Front-matter
    @param x: 文件名
    @param c_time: 文件创建时间，由flomo的创建时间得出
    @param tags: 标签
    @return:
    """
    yaml = f"""---
    name: {x}
    date created: {c_time}
    date updated: {time.strftime("%Y-%m-%d %H:%M", time.localtime(time.time()))}
    """
    yaml = re.sub(r"^\s+", "", yaml, flags=re.M)

    if tags:
        # 有tag的话，生成tag属性
        yaml += f"tags:\n{tags}\n"

    yaml += "---\n"
    print(yaml)
    return yaml


def create_toc():
    """
    写入目录笔记
    @return:None
    使用目录注意事项，可能会覆写原来的日记文件，例如原先存在2023.01.01，又生成2023.01.01,就覆盖了
    使用前最好检查本月有没有在Obsidian创建的日记
    """
    dict1 = {}
    list1 = []  # 用于写入链接
    tag = "  - 目录"

    # 统计数量
    # 截取所有日记文件名前10进行计算，例如2013.01.01 010101、2013.01.01 020202
    # 会统计成："2013.01.01":2
    for i in os.listdir(save_path):
        if i.endswith(".md") and os.path.splitext(i)[0].find(".") > -1:
            file_name = i[:10]
            dict1.setdefault(file_name, 0)
            dict1[file_name] = dict1[file_name] + 1
            list1.append(os.path.splitext(i)[0])

    # 当天MEMO记录>1的，创建个目录笔记
    for toc in dict1:
        if dict1[toc] > 1:
            # 检测下当天是否有Obsidian中创建的日记（有加个目录后缀），防止覆写
            if os.path.exists(os.path.join(save_path, toc + ".md")):
                toc += " 目录"
            with open(
                f"{os.path.join(save_path, toc + '.md')}", mode="w", encoding="utf-8"
            ) as md:
                # 写入Front-matter
                md.write(
                    c_yaml(
                        toc,
                        time.strftime("%Y-%m-%d %H:%M",
                                      time.localtime(time.time())),
                        tag,
                    )
                )
                md.write("\r\n")

                """
                遍历所有日记文件
                如果日记文件包含目录文件名称的，那么写入将日记名称作为链接形式写入目录笔记
                例如目录笔记为2022.07.01
                那么2022.07.01 110102 包含 2022.07.01，所以写入
                """
                for i in list1:
                    if (i.find(toc.replace(" 目录", "")) > -1) and (len(i) > 10):
                        # md.write(f"- [{i}]({i.replace(' ', '%20')}.md)\n") # 标准Markdown超链接[]()
                        md.write(f"- [[{i}]]\n")  # 双链形式


def main():
    # 解析HTML
    with open(file_path, "r", encoding="utf-8") as f:
        html = f.read()
    soup = BeautifulSoup(html, "html.parser")

    # 检测是否库是否有附件文件夹
    photo_dir = f"{save_path}/assets"
    if not os.path.exists(photo_dir):
        os.mkdir(photo_dir)

    for memo in soup.find_all(class_="memo"):
        # 元信息处理
        _time = memo.find(class_="time").text  # memo 时间
        file_name = _time.replace(":", "").replace("-", ".")  # 文件名
        # print(_time)
        # print(file_name)

        # 单个文件归档使用
        # if file_name != "2024.05.31 163811":
        #     continue

        # 正文处理
        content = ""
        for i in memo.find(class_="content"):
            if i.name == "p":
                content += i.get_text() + "\n"

            elif i.name == "ul":
                for li in i.find_all("li"):
                    content += "- " + li.get_text() + "\n"
            elif i.name == "ol":
                for index, val in enumerate(i.find_all("li")):
                    content += f"{index+1}. " + val.get_text() + "\n"

        # 图片处理
        photo_content = ""
        for i in memo.find(class_="files"):
            local_photo_path = os.path.join(
                os.path.split(file_path)[0], i.attrs["src"])
            print(local_photo_path)
            print(i.attrs["src"].split("/")[-1])
            photo_content += f"![[{i}]]\n"
            shutil.copyfile(
                local_photo_path, f'{photo_dir}/{i.attrs["src"].split("/")[-1]}'
            )

        # 写入文件
        with open(
            f"{os.path.join(save_path, file_name + '.md')}", mode="w", encoding="utf-8"
        ) as md:
            # 添加Front-matter
            # 有标签的话添加标签，并且移除正文中的标签，没有的话采用null
            if (r_result := re.search(r"#.+", content)) is not None:
                # 使用正则搜索得到的标签(str)
                tag_str = r_result.group()
                tags = "\n".join(
                    ["  - " + i for i in tag_str.replace("#", "").split()]
                )  # 转换成YAML
                md.write(c_yaml(file_name, _time[:-3], tags))
                content = content.replace(tag_str, "")
            else:
                md.write(c_yaml(file_name, _time[:-3]))

            # 写入正文
            md.write("\r\n")
            md.write(content)

            # 写入图片
            md.write("\r\n")
            md.write(photo_content)


if __name__ == "__main__":

    # flomo导出的html位置
    file_path = (
        r"D:\systemLibrary\Download\新建文件夹\flomo@lin-20240531\lin的笔记.html"
    )

    # Markdown 存储位置
    save_path = r"D:\systemLibrary\Desktop\Demo"

    main()
    # create_toc()
