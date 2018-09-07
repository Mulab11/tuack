## 简介

更新到了 0.1.4.3 版本，新特性见最后。

一般在三个地方更新：

* [https://git.thusaac.org/publish/tuack](https://git.thusaac.org/publish/tuack)：主要的工作地址，所有分支都会在这里；非清华贵系算协成员不能提 issue。
* [https://gitee.com/mulab/oi_tools](https://gitee.com/mulab/oi_tools)：可以提 issue。
* [https://github.com/Mulab11/tuack](https://github.com/Mulab11/tuack)：可以提 issue，可能不会及时更新。

此外如果有任何疑问或建议，知道我 QQ 或微信的小伙伴也可以用这些工具告诉我。

这个轮子打算逐步实现：

* 合作：通过共同使用git和遵循一些约定，降低合作命题者之间版本控制，题面修改，代码、数据交换，bug修复等的成本。
* 题面：通过一些轮子搭建易于转换为多种格式的题面范式，用这套轮子造的题面可以转变到各种比赛格式。
* 适配：尽量支持从现有的各类评测工具导入数据和导出到各类评测工具中。

这个轮子主要是面向出题人和OJ站长，方便大家造题和分享题目。

目前这个轮子还在you开yi发dui中bug。如果希望我们支持其他格式的题面，其他工具的导入导出，对这个轮子有任何建议或意见，发现了任何bug，或是有兴趣加入我们，欢迎随时联系。

## 文档

[文档在这里](https://git.thusaac.org/publish/tuack/wikis/home)

## 更新记录

### v0.1.4.3

- 添加 `tuack.doc check` 的一些新检查。
- 渲染的 PDF 有代码高亮了。
- 添加题面快速访问各测试点参数的方法。
- 修复若干bug。

### v0.1.4.2

* 修复若干 bug，主要是对 python2 的一些支持。

### v0.1.4.1

* 添加了题面格式检查器的 mac 支持。

### v0.1.4

* 增加了烦死了题面格式检查器 `tuack.doc check`，为什么烦死了试一试就知道了。
* 调整了 PDF 封面的显示，现在应该更好看了。
* 修复若干 bug。

### v0.1.3

- 添加 `tuack.doc` 可以导入其他格式的题面和进行简单的格式化。这项功能还有一堆 bug，注意备份。
- 添加 `tuack.ren thuoj`，用于输出为 dokuwiki 的数据结构课程 OJ。

### v0.1.2.1~

* 修复若干 bug，尝试用此版本推到 pypi 上。
* 奇怪的版本号是开始不会用 pypi 产生的。

### v0.1.2

*   添加 yaml 格式的配置文件；
*   添加 `tuack.ren loj`，`tuack.gen auto`；
*   现在可以设置字体颜色了；
*   现在 json 里面的中文在 gen 之后还会变回中文而不会是 unicode 了；
*   去掉了 packed 标记，判断是否是打包评测只依赖于 score 字段是否设置；
*   修复了若干 bug，增加了一些小 feature。

### v0.1.1

*   添加了 pre-test 类型的数据；
*   题面可以用 `data`、`args`、`samples`、`pre` 等写法代替类似于 `prob['data']` 的写法；
*   添加了用户代码的期望得分标注；
*   添加了一个题解文件；
*   修复了若干 bug。
