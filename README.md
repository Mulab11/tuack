我们推荐将oi_tools的路径加到PYTHONPATH环境变量中。

也可以把oi_tools的父路径加到PYTHONPATH中，这样可以防止污染名称。相应的，下文中所有形如 `python -m tester` 的命令都要改成  `python -m oi_tools.tester`。

还可以用下列方式使用oi_tools：

oi_tools已经被加到某个工程的submodule，那么你可以用下面的方式把这个工程也clone下来

```
git clone --recusive 父工程的仓库地址
```

如果已经clone下来了父工程，发现这个子工程是空的，可以用这个方式clone子工程

```bash
cd oi_tools
git submodule update --init
```

相应的，下文中所有形如 `python -m tester` 的命令都要改成  `python oi_tools/tester.py`。

### 造题存储原则

对于日常出题，我们建议使用下列原则；对于正式使用的题目，我们**要求遵守**下列原则：

**任何重复性的东西的原生状态只能出现一次，所有可能改变的东西都应当自动化。**

我们举一些例子说明如何做到自动化以及为什么要做到自动化：

1.  样例文件要出现在题面里，要放到下发文件中，还要拿给程序去跑测试。在这套轮子中，这些文件存放在下发文件目录down中。在题面的编写方法中，有对这些文件的引用方式，在生成网页版或是打印版题面会读取这些文件。在conf.json中配置了的前提下，我们的测试器tester.py也会对你的所有程序测试down中的输入输出文件。*错误提示：出现过多次出题人手打样例然后错了，或是下发的文件和题面的文件不一致，或是样例和评测数据的格式或是限制条件不一致的情况。*
2.  数据应当是运行一个程序或脚本生成的（当然可以是一个程序调用了多个程序生成）。*错误提示：出现过多次出题人手造数据，然后格式错误或答案错误或不符合约束条件的情况，当然自己在造题的时候也可能不小心覆盖以后改不回原先奇妙数据的情况。*
3.  题目的部分分参数应当存储在conf.json中，数据生成器和题面都从这里读取。如果数据规模是有规律的，甚至可以程序生成这个json的一部分（例如用python读入这个json，加上data字段以后写回去）。这样可以保证题面里的子任务描述和评测数据中的数据规模是一致的。*错误提示：同样，这里也出现了很多次不一致……*
4.  做一些兼容性的工作。例如，这个轮子在每道题下每个出题人/验题人一个独立文件夹，文件夹中对每个算法放一个文件夹，每个文件夹中放对应题目的代码。这个要求可能和某些评测工具的要求是不同的。为了可以使用其他评测工具，我们建议你写一个脚本自动将本存储格式复制到你想用的工具的格式，而不是直接存储成别的格式。当然我们也建议你就使用这个轮子，更欢迎你来改进这个轮子。

造这套轮子有很大一个目的就是帮助大家解决包括但不限于上面的问题。当然这个轮子还不是很好用，如果有疑问或建议也欢迎随时提出。

## 基本使用方式

**所有基于文本的文件如果含有中文，必须用UTF-8编码。**

### 建立工程

一般来讲，你可以用类似于下面的方式在当前目录下建立一场比赛的工程。

```bash
python -m generator contest
python -m generator day day0 day1 day2
cd day1
python -m generator problem p1 p2 p3
```

这三种命令如果不带参数则表示在当前目录下建立一个比赛/比赛日/题目，否则表示建立子目录并在配置文件中建立连接。你可以建立单独的比赛日或题目，而不依赖于一个比赛或比赛日。

### 寻找文件

我们提供了一个笨拙的工具，可以试图寻找数据、样例和源程序，只要你将它们放在了 `data`、`down`、题目根目录的某个子目录中，并且不是明显不是源程序的文件，那么可以被以下方式找到并添加进 `conf.json`。

```bash
python -m generator data
python -m generator samples
python -m generator code
```

### 文件样例

我们提供了一些文件的样例，放在 `sample` 文件夹下。一般情况下你只要用 `generator` 生成了工程，工程中就会自带这些样例。如果工程中找不到的话，可以参看下面：

-   `.gitattributes`：描述大文件存储所需的信息。
-   `*.gitignore`：三类文件夹中防止把多余的文件存到git仓库中所需的描述文件，改成 `.gitignore` 使用。
-   `*.json`：三类文件夹的描述文件例子，改成 `conf.json` 使用。
-   `statement/`：题面的例子。
-   `tables/`：表格的例子。
-   `uoj.json`：复制到根目录下使用，描述配置UOJ的关联，暂时弃用。

### 导入工程

用 `generator` 建好工程以后，可以用 `loader` 导入某个其他格式的题目或比赛。

```bash
python -m loader 类型 来源路径
```

其中 `来源路径` 是存放原始工程的路径。

本功能开发中，目前支持的类型有：`tsinsen-oj`。

### 导出工程

一个造好的工程可以用 `dumper` 导出成其他某种格式。

```bash
python -m dumper 类型1,类型2,...
```

本功能开发中，目前支持的类型有：`lemon`（spj还没做），`arbiter`。

老版的oi_tools有一个导出工具 `packer`，此项功能目前弃用，将会更新合并至 `dumper`（用于输出成其他题目存储格式的工具，目前开发中），下面将列举出它的用法。但因为并没有维护这段代码，因此不保证能够成功运行。

可以在根目录下运行下列命令生成对应的数据包：

```bash
python -m packer uoj,noi,release
```

表示生成uoj、noi和发布使用的数据包，生成多种包之间用逗号隔开。

目前支持输出下列种类的数据包：

-   `test`：用于 `tester.py` 的数据包；
-   `release`：用于发布的zip包；
-   `noi`：noi风格的数据包；
-   `pc2`：$pc^2$风格的数据包；
-   `uoj`：uoj风格的数据包，并自动上传到uoj。如果需要上传到uoj，需要配置文件 `uoj.json`，安装svn，并在 `conf.json` 中添加 `uoj id` 参数。

### 测试

可以在根目录下运行下列命令进行测试：

```bash
python -m tester
```

其中结果将输出到对应天目录下的 `result` 目录下，并会自动打开。要想不自动打开则在后面加上 `-s`。

### 题面生成

可以在根目录下运行下列命令生成对应的题面：

```bash
python -m renderer noi,uoj
```

表示生成uoj和noi风格的题面，生成多种包之间用逗号隔开。生成好以后会自动打开，要想不自动打开则在后面加上 `-s`。

生成题面时，python必须安装 `jinja2` 包（`pip install jinja2`）。

目前支持两类题面：

-   `tex`：最终会生成成PDF格式。需要安装 `pandoc` 和 `xelatex`。其中 `pandoc` Windows下直接搜官网下载，Ubuntu下直接 `apt install pandoc`； `xelatex` 的安装方式见下。具体的风格有：`noi`，`noip`，`ccpc`，`ccc-tex`。
-   `html`：会生成带html标签的markdown。不需要特别安装东西。具体的风格有：`uoj`，`ccc-html`。

题面的书写后文将有详细说明。

### 安装XeLaTeX

Windows下可以安装MiKTeX，在首次运行的时候会再提示安装后续文件。

Ubuntu下先运行下列命令：

```bash
sudo apt install texlive-xetex,texlive-fonts-recommended,texlive-latex-extra
```

然后可能会因为缺少有些字体而报错，可以使用[这个方法](http://linux-wiki.cn/wiki/zh-hans/LaTeX%E4%B8%AD%E6%96%87%E6%8E%92%E7%89%88%EF%BC%88%E4%BD%BF%E7%94%A8XeTeX%EF%BC%89)安装缺少的字体或是把win下的字体复制过来。

MacOS下待研究。

### 只对特定的题目进行操作

前面几个工具都可以使用类似于 `-p day1,day2` 和 `-p day1/excellent,day2/drink,day1/grid` 来指定特定的天数或题目。对于 `tester`，还可以指定评测用户或是算法。例如：

```bash
python -m packer noi,release,test -p day1,day2
python -m tester -p day1/excellent,day2/drink
python -m tester -p day1/excellent/saffah
python -m tester -p day1/excellent/saffah/std
```

注意所有指定的命令全部都改成了 `-p`，而且现在三种类型的文件夹都可以使用这个命令。例如你现在在 `day1` 文件夹下的话，要指定测试 `excellent` 一题 `saffah` 的程序，那么使用的命令是

```bash
python -m tester -p excellent/saffah
```

需要注意的是，这里的路径不是**绝对或相对路径**，而是**题目的组织层次**，即就算你不按照规定的层次存储文件夹（主要是为了继承），你也需要写成上文中的这种层次。

### 指定操作系统

这几个工具都可以指定操作系统，使用命令如 `-o Windows` 。其中操作系统的名称与python的 `platform.system()` 调用结果一致；目前只判断了Windows和非Windows。默认是当前操作系统。

对于  `packer`，将会把所有数据转成指定操作系统的换行符；对于 `renderer`，会按指定的操作系统习惯输出题面。

注意：编译的chk等只跟运行环境的操作系统有关，不能指定操作系统。

## 文件的存放和定义

### 文件路径

如果你按照前文所述进行了操作，那么你一般不用担心文件的存放问题，否则请参看这里讲到的文件存放路径规定。

**所有数据文件，必须用大文件系统 `git lfs` 管理。**一般地，如果你只在下文规定的地方存放数据文件，那么你可以将 `samples/.gitattributes` 复制到每道题的目录下，git会自动帮你进行管理。当然事实上，如果你使用 `generator` 生成一个工程，本部分大多数事情都不用太关心。第一次使用参考[这里](https://github.com/git-lfs/git-lfs/wiki/Installation)安装。

```
conf.json	//每层文件夹都有一个配置文件，这是一个“比赛”工程
title.tex	//如果要输出NOI风格的pdf，需要在这里定义比赛的名字，否则不需要这个文件
oi_tools	//把工具包放在这个位置
day1		//和conf.json的subdir匹配的路径，表示这个比赛工程的子“比赛日”
day2		//匹配的另一个“比赛日”工程
	conf.json		//这是一个“比赛日”的工程，一个比赛日可以单独存放
	interval		//和比赛日conf.json的subdir匹配的路径，表示这个比赛工程的“题目”
	drink
	nodes			//这个比赛日有3个题目
		conf.json	//这是一个“题目”的工程，一个题目也可以单独存放
		statement	//题面，用markdown+jinja模板做（可以纯markdown，但不能包含html），详见generator生成出来的例子
			zh-cn.md	//一般使用这一个
			en.md		//如果是英文题面用这个
		assignment[.pdf]		//命题报告，一个文件或文件夹，单文件用pdf、pptx、html等可以直接看的格式，文件夹必须用.dir结尾，下同
		discussion[.pdf]		//讲题/题目讨论PPT，一个文件或文件夹
		solution[.docx]			//题解
		data			//一定包含一个评测用数据的文件夹
			1.in	//文件推荐用<编号>.<后缀名>的格式命名，也可以用别的方式
			1.ans	//标准输出文件是.ans
			...
			10.ans
			chk		//checker统一使用chk命名，需要编译的话提供一个同名文件夹。!TODO：这里未来会增加对不同评测环境的支持，用make <环境名称>生成对应环境的chk，没有makefile则用g++进行编译。
				chk.cpp			//如果用正常的g++命令编译，就这么放
				testlib.h		//可以有其他文件
		down	//一定包含一个下发文件夹
			1.in	//第一个样例；对于提交答案题，这不是第一个下发数据
			1.ans	//这里的编号和题面中的样例编号相同，题面中出现的样例也要在这里给出
			2.in
			...
			decimal.cpp	//这道题没有这个啦，这个是要下发的代码，其他任何要下发的文件同理
			checker		//对于需要编译后下发的，仍然是提供一个文件夹
				checker.cpp	//和上面一样，正常编译就这样，否则提供makefile
				testlib.h
			sample_programs.dir	//极少的题目需要下发一个目录，规定这样的目录+.dir好了，下发时会删除.dir
				sample.cpp	//这些完全可以不放在目录中下发
				sample.pas
		gen		//如果出题人写了数据生成器，放在这里，不规定格式
		vfk		//每个出题人/验题人建立一个目录
		picks	//这是另一个验题人
			val 	//如果你写了数据检查器请放在这样命名的文件夹下，具体格式见后文
			data.test		//如果你不是出题人但是出了数据
			chk.test		//如果你写了checker的测试，装在这个文件夹下
			checker.test	//同理，不要问我同名怎么办
			n_log_n			//每个模拟选手的测试用一个文件夹装，现在因为要配置，因此不严格要求这么存
				nodes.cpp或1.out	//这就是一个模拟选手，用标准IO
			Dinic	//另一个模拟选手，名称随意，不要匹配到上文和下文的名称就行
				1.out
				...
			SPFA.cpp	//现在也可以这么放置源代码了
			hehe.dir	//如果你有其他文件夹，觉得想分享给大家，又不是模拟选手，用.dir
			rename.py	//可以有其他想要分享的文件
		resources		//题面中使用的外部资源，例如图片、html或tex的模板（对于md无法表示的东西，需要分别写html和tex）
			1.jpg		//和题面中名称相同的图片
		tables			//需要用到的表格
			data.json	//和题面中名称相同的表格，用json+jinja模板做（可以纯json）
precautions		//此次比赛的选手注意事项，会根据模板渲染到相应的位置
	zh-cn.md
lectures	//有讲座的活动（WC、APIO等），讲座的东西（包括集训队交流）
	picks	//装在一个自己名字命名的文件夹里面
	vfk		//名字应该不会重复吧2333
```

### 题目描述文件

`conf.json` 是一个工程或其子工程的描述文件，你总是可以手工编辑这个文件来实现所想要的功能。

`conf.json` 必须是一个json文件，恰好包含一个dict/object，并且有一个元素为 `"folder" : "类型"`。`类型` 必须为 `contest`，`day`，`problem`，`extend` 中的一种。如果不含有 `folder` 元素，则认为是 `problem`。

下面是 `conf.json` 的格式要求（注意json文件**不能包含注释**，下面的注释是为了说明用法和规定，使用时必须删除；程序运行前会验证json文件的合法性）：

```js
{
	"folder" : "contest",
	"name" : "NOI2016TEST",					//这个是比赛的名字，用于输出的文件夹名字等
	"subdir" : ["day0", "day1", "day2"],	//包含的比赛场次的文件夹名称
	"title" : {								//名称用于渲染题面，注意标题和名字是不同的东西
		"zh-cn" : "NOI2016模拟赛"			//不同语言不会出现在同一份题面中，即使有字母也是中文
	},
	"short title" : {						//这个是标题的简写，一般是官方给的
		"zh-cn" : "NOI-2016-TEST"
	},
	"subtitle" : {							//与前面简写区分开的，这是子标题，例如“冬令营”
		"zh-cn" : "by zgg"
	}
}
```

```js
{
	"folder" : "day",
	"name" : "day1",
	"subdir" : ["excellent", "grid", "cyclic"],	//包含的题目的文件夹名称
	"title" : {									//用来渲染题面，如果不造题面可以不写
		"zh-cn" : "第一试",						//用dict来描述国际化，可以单用一个字符串
		"en" : "Day 1"							//只写语言不写地区表示所有使用该语言的地区
	}
	"start time" : "2016-07-24 08:00:00+0800",	//目前用于渲染题面，不排除可以用于比赛，需要严格按格式写
	"end time" : "2016-07-24 13:00:00+0800",
}
```

```js
{
	"folder" : "problem",
  	"type" : "program",			//program传统，output提交答案，alternately交互
	"name" : "excellent",		//建议加上题目名称，没有的话默认是文件夹名字
	"title" : {					//现在标题要区分语言，原来的中文名称cnname停用
		"zh-cn" : "优秀的拆分"
	},		
	"time limit" : 1.5,			//时间限制，uoj会自动向上取整（如果不同环境限制不同，用继承）
	"memory limit" : "512 MB",	//空间限制，必须加上单位
								//测试点数量不再使用
	"partial score" : false,	//是否有部分分，默认没有，只用于显示在题面上
	"packed" : false,			//是否是打包评测，默认不是
	"compile" : {				//各个语言的编译开关
		"cpp" : "-O2 -lm",
		"c" : "-O2 -lm",
		"pas" : "-O2"
	},
								//样例的数量不再使用
    "samples" : [...],			//格式同data
	"args" : [10, 30000],		//这是全局参数，由出题人自定义，也可以在题面中引用；TODO：未来会传给val
	"data" : [					//这是每个测试点的参数，注意只有args是出题人自己定义的
		{
			"cases" : [1, 2],	//这是测试点1和2的公共参数；如果打包评测则是一个包
			"score" : 11,		//如果打包评测是这个包的分数，否则没用；没有这项参数的包将假设满分是100分然后平分剩下的分数（可能为负数）
			"args" : [300, 1],	//这些测试点的参数，由出题人自定义，会传给val，也可以在题面中引用
			"time limit" : 1.0,	//可选，有的话将覆盖全局变量，全有可不设全局变量，下同（tester还没写）
			"memory limit" : "64 MB"
		},
		{
			"cases" : [3, 4],
			"score" : 19,
			"args" : [200, 1]
		},
		...
		{
			"cases" : [20],
			"score" : 5,
			"args" : [30000, 0]
		}
	],
	"users" : {					//验题人
		"vfk" : {				//一个验题人写了多个算法
			"std" : "vfk/std.cpp"//算法的名称和路径，非传统题必须是文件夹路径，传统题是文件名
		},
		"picks" : {
			"n_log_n" : "picks/n_log_n/excellent.cpp",
			"Dinic" : "picks/Dinic/hehe.cpp"
		}
    },
	"uoj id" : 3				//如果要使用上传到uoj的功能，需要填写这道题目的uoj题目id
}
```

```js
{
	"folder" : "extend",		//继承类型，可以继承上面任何一种
	"base path" : "cyclic",
	"time limit" : 3,			//同名字段表示覆盖，例如换了评测环境以后时限变长了
	"title+" : {				//字段后加"+"表示合并，dict是递归合并，即子字段用同样方式
		"en" : "This problem has a new English name now",
		"zh-cn" : "我要换个中文名字"	//原来有的字段在子结构中递归覆盖
	},
	"data+" : [					//现在想要增加一些数据，array是直接加到后面合并
		{
			"cases" : ["ex1", "ex2"]	//出了几个加强数据
		}
	]
}
```

关于 `args` 和 `data` 中 `args` 的说明：这两个参数全部是出题人自己定义的，这意味着 `args` 下的数据结构可以由你自己定义。原理上你可以根本不定义这些参数，但为了达到后文的文件存储原则，我们建议或要求这么做。

但是我们推荐将所有数据的参数全部放在这里，题面的书写工具提供了获取这些参数的方法，你的数据生成器一般也有方法读取这个json文件（虽然C++也有相关的轮子，但如果不会的话你可以用python读了传给C++），未来我们还会将这些参数传给val。

注意在这些json文件中，经过程序处理的中文会转成unicode字符串如 `\u7b2c\u4e00\u8bd5`，这除了你看不懂以外并不影响什么，你仍然可以在json中用utf-8格式写中文，甚至在一个字符串中混用这样的字符串和中文。

## 基本使用方式

### 建立工程

一般来讲，你可以用类似于下面的方式在当前目录下建立一场比赛的工程。

```bash
python -m generator contest
python -m generator day day0 day1 day2
cd day1
python -m generator problem p1 p2 p3
```

这三种命令如果不带参数则表示在当前目录下建立一个比赛/比赛日/题目，否则表示建立子目录并在配置文件中建立连接。你可以建立单独的比赛日或题目，而不依赖于一个比赛或比赛日。

### 寻找文件

我们提供了一个笨拙的工具，可以试图寻找数据、样例和源程序，只要你将它们放在了 `data`、`down`、题目根目录的某个子目录中，并且不是明显不是源程序的文件，那么可以被以下方式找到并添加进 `conf.json`。

```bash
python -m generator data
python -m generator samples
python -m generator code
```

### 文件样例

我们提供了一些文件的样例，放在 `sample` 文件夹下，其中：

* `.gitattributes`：描述大文件存储所需的信息。
* `*.gitignore`：三类文件夹中防止把多余的文件存到git仓库中所需的描述文件，改成 `.gitignore` 使用。
* `*.json`：三类文件夹的描述文件例子，改成 `conf.json` 使用。
* `statement/`：题面的例子。
* `tables/`：表格的例子。

* `uoj.json`：复制到根目录下使用，描述配置UOJ的关联，暂时弃用。

### 数据包生成

*此项功能目前弃用，将会更新合并至 `dumper`（用于输出成其他题目存储格式的工具，目前开发中），本节仅供参考，不保证能够成功运行。*

可以在根目录下运行下列命令生成对应的数据包：

```bash
python -m packer uoj,noi,release
```

表示生成uoj、noi和发布使用的数据包，生成多种包之间用逗号隔开。

目前支持输出下列种类的数据包：
* `test`：用于 `tester.py` 的数据包；
* `release`：用于发布的zip包；
* `noi`：noi风格的数据包；
* `pc2`：$pc^2$风格的数据包；

* `uoj`：uoj风格的数据包，并自动上传到uoj。如果需要上传到uoj，需要配置文件 `uoj.json`，安装svn，并在 `conf.json` 中添加 `uoj id` 参数。

### 导入工程

用 `generator` 建好工程以后，可以用 `loader` 导入某个其他格式的题目或比赛。

```bash
python -m loader 类型 来源路径
```

其中 `来源路径` 是存放原始工程的路径。

本功能开发中，目前支持的类型有：`tsinsen-oj`。

### 导出工程

一个造好的工程可以用 `dumper` 导出成其他某种格式。

```bash
python -m dumper 类型
```

本功能开发中，目前支持的类型有：`lemon`,`arbiter`,`down`（spj还没做）。

### 测试

可以在根目录下运行下列命令进行测试：

```bash
python -m tester
```

其中结果将输出到对应天目录下的 `result` 目录下，并会自动打开。要想不自动打开则在后面加上 `-s`。

### 题面生成

可以在根目录下运行下列命令生成对应的题面：

```bash
python -m renderer noi,uoj
```

表示生成uoj和noi风格的题面，生成多种包之间用逗号隔开。生成好以后会自动打开，要想不自动打开则在后面加上 `-s`。

生成题面时，python必须安装 `jinja2` 包（`pip install jinja2`）。

目前支持两类题面：
* `tex`：最终会生成成PDF格式。需要安装 `pandoc` 和 `xelatex`。其中 `pandoc` Windows下直接搜官网下载，Ubuntu下直接 `apt install pandoc`； `xelatex` 的安装方式见下。具体的风格有：`noi`，`noip`，`ccpc`，`ccc-tex`。
* `html`：会生成带html标签的markdown。不需要特别安装东西。具体的风格有：`uoj`，`ccc-html`。

题面的书写后文将有详细说明。

### 安装XeLaTeX

Windows下可以安装MiKTeX，在首次运行的时候会再提示安装后续文件。

Ubuntu下先运行下列命令：

```bash
sudo apt install texlive-xetex,texlive-fonts-recommended,texlive-latex-extra
```

然后可能会因为缺少有些字体而报错，可以使用[这个方法](http://linux-wiki.cn/wiki/zh-hans/LaTeX%E4%B8%AD%E6%96%87%E6%8E%92%E7%89%88%EF%BC%88%E4%BD%BF%E7%94%A8XeTeX%EF%BC%89)安装缺少的字体或是把win下的字体复制过来。

MacOS下待研究。

### 只对特定的题目进行操作

前面几个工具都可以使用类似于 `-p day1,day2` 和 `-p day1/excellent,day2/drink,day1/grid` 来指定特定的天数或题目。对于 `tester`，还可以指定评测用户或是算法。例如：

```bash
python -m packer noi,release,test -p day1,day2
python -m tester -p day1/excellent,day2/drink
python -m tester -p day1/excellent/saffah
python -m tester -p day1/excellent/saffah/std
```

注意所有指定的命令全部都改成了 `-p`，而且现在三种类型的文件夹都可以使用这个命令。例如你现在在 `day1` 文件夹下的话，要指定测试 `excellent` 一题 `saffah` 的程序，那么使用的命令是

```bash
python -m tester -p excellent/saffah
```

需要注意的是，这里的路径不是**绝对或相对路径**，而是**题目的组织层次**，即就算你不按照规定的层次存储文件夹（主要是为了继承），你也需要写成上文中的这种层次。

### 指定操作系统

这几个工具都可以指定操作系统，使用命令如 `-o Windows` 。其中操作系统的名称与python的 `platform.system()` 调用结果一致；目前只判断了Windows和非Windows。默认是当前操作系统。

对于  `packer`，将会把所有数据转成指定操作系统的换行符；对于 `renderer`，会按指定的操作系统习惯输出题面。

注意：编译的chk等只跟运行环境的操作系统有关，不能指定操作系统。

## 题面的书写

如果你不使用任何的特性，你可以用纯 markdown 书写题面，并将以 `description.md` 命名保存在试题目录下。
此外还提供了少量的工具以扩展 markdown 不支持的功能。

注意：**不要在题面里直接插入任何html代码**。因为虽然markdown原生支持嵌入html，但因为我们要渲染成tex，所以不能直接使用任何原生html语法，例如表格、带格式的图片等都需要特殊处理，具体可以参考后文的“两轮渲染”。

注意：**不要在题面里直接插入任何markdown的原生表格**。因为markdown表格的方言相当多，加上我们建议**所有参数全部来源于同一个地方**，因此请尽量按照后文的“表格”。

目前两种输出类型渲染的步骤为：
* `tex`：md+jinja+\*jinja → md+jinja → tex+jinja → tex → pdf；
* `html`：md+jinja+\*jinja → md+jinja → md+html。

其中\*jinja表示经过jinja渲染会变成jinja模板的代码。

jinja2的安装用 `pip install jinja2`，jinja2本身的语法戳[这里](http://docs.jinkan.org/docs/jinja2/templates.html)学习。

所有的模板都存在该工程的templates目录下，有兴趣开发模板或是想修改的话欢迎联系我入坑。

### description.md

可以参考NOI2016网格这题，下面提到的大部分功能在这个题目中都有使用，详细代码见NOI2016的[git工程](http://git.oschina.net/mulab/NOI2016)。

`{% block title %}{% endblock %}` 表示使用名为 `title` 的子块，这个子块在uoj模式下会渲染成时间、空间限制和题目类型（如果不为传统型的话），在noi模式下会留空。
这些子块定义在 `problem_base.md.jinja` 中，可用的还有：
* `input_file` 输入文件的描述，根据平台说明是标准输入还是从文件输入。
* `output_file` 输入文件的描述，根据平台说明是标准输入还是从文件输入。
* `user_path` 选手目录，如果是noi会变成“选手目录”这几个字，uoj会变成下载链接。
* `sample_text` 样例自动渲染，会自动从 `down` 中读入样例文件并添加到题面中，需要下面提到的前置变量。支持参数 `sample_id` 设置样例的编号（同时也是样例文件名）；`show space` 如果为真则会在PDF格式中将空格显示出来。
* `title_sample` uoj的“样例输”是拆分成两级名称的，所以蛋疼地需要多一级，这里专指“【样例】”这个标签；其他环境下则会被渲染成空的。
* `sample_input_text` 样例输入自动渲染。
* `sample_output_text` 样例输入自动渲染。
* `sample_text` 样例自动渲染，会自动从 `down` 中读入样例文件并添加到题面中，需要下面提到的前置变量。
* `sample_file` 一个不出现在题面，但是以文件形式提供的样例，同样需要下面提到的前置变量。
* `title_sample_description` uoj的“样例说明”是拆分成两级名称的，所以蛋疼地需要多一级。
* `title` 标题，包括时空限制、题目类型等。

一个块只能在代码中直接出现一次，如果需要多次使用，需要写成 `{{ self.块名称() }}` ，例如 `{{ self.title() }}`。
事实上，可以总是使用这种方式输出一个块，上面那种方式是为了更好地支持继承，因此我们推荐在造题的时候始终使用这种方式引用块。

有的块需要用到前置的变量，例如文字样例自动渲染需要提供样例的编号 `sample_id` 作为变量，具体会写成这样：
```
{% set vars = {} -%}
{%- do vars.__setitem__('sample_id', 1) -%}
{{ self.sample_text() }}
```

如果只有一组样例，应当不设置样例编号，像这样：
```
{% set vars = {} -%}
{{ self.sample_text() }}
```

但请注意，在 `down` 文件夹中仍然需要以 `1` 标号。

### 一些约定

题目标题用一级标题 `#`，在题面书写的时候并不需要加上，而应该用标题子块代替。

每个小节标题，如 `【题目描述】` 用二级标题 `##`，会被渲染成Latex的subsection和html的h2。
（不要吐槽这样在uoj上字体太大了，这里最好是uoj改css，或者你有兴趣的话可以造一个模板来造标题，其实挺简单的）

小节下的标题用三级标题 `###`，会被渲染成Latex的subsubsection和html的h3。
对于uoj，`【样例】` 下的 `输入` 会使用比上面低一级的标题，而这个在noi style的题面中会不单列一级标题；为了通用，建议使用上面提到的子块生成样例。

样例使用三个反引号（不知道markdown里面怎么打这几个字符）括起来的pre来装，同样建议用子块而非自己做样例。

公式用 `$` 括起来，单独占行的公式用单独占行的 `$$` 括起来，例如 `$1 \le a_i \le n$`。

### 外部变量和小工具

通过变量 `prob` 可以获取你在 `conf.json` 中的各项参数，例如要输出题目的中文名，可以用下列写法（两种方法等价）：
```
{{ prob['cnname'] }}
{{ prob.cnname }}
```

获取当前的渲染环境，可以用变量 `comp`（会被赋值为 `noi`、`uoj` 等），输入输出方式用变量 `io_style`（会被赋值为 `fio`、`stdio` 等）。

如果需要以文本的形式展示某个下发的文件，提供了一个函数 `down_file(file_name)`，例如：
```
## 【样例输出】
//这里应该有3个`
{{ down_file('1.ans') }}
//这里应该有3个`
```

考虑到不同情况下下发文件存储的位置不同，用函数 `file_name` 根据具体的环境生成具体的路径。
类似的还有 `resource` 函数，可以根据具体情况获取存储在 resources 文件夹中的资源（图片、模板等）。

此外，还有一组工具 `tools`，其中包括一些小轮子，具体可以阅读 `tools.py`。例如下列调用可以生成一个数适合阅读的格式：
```
${{ tools.hn(1000000) }}$
```

此外你还可以从 `common` 中读取公共的任何全局变量，例如 `common.out_system` 可以读取要输出到的系统，你可根据不同的系统写不同的题面（例如checker在不同系统中的用法不同）。

### 两轮渲染

图片、表格等东西markdown原生支持不太好（图片无法改变大小，表格无法合并单元格），因此提供了两轮渲染的方式，
即在两条路线共同的渲染之后，使用tex或html的模板再渲染一次。

例如提供了一对简单的图片模板 `image.tex.jinja` 和 `image.html.jinja`，使得可以使用以下语法渲染一张图片
```
{{ render("template('image', resource = resource('3.jpg'), size = 0.5, align = 'middle', inline = False)") }}
```
其中 `render` 函数中的串会在被渲染成tex或html之后会被渲染成一个模板项，从而进一步被渲染。

如果要写一段自用的tex或html模板（当然你如果只需要嵌入tex或html，只需要再模板中不填入任何模板语法即可），
你可以在 `resources` 文件夹中写 `名称.tex.jinja` 和 `名称.html.jinja`，然后用下列方式插入：
```
{{ render("template(resource('名称'), 模板参数表...)") }}
```
`render` 函数还可以传第二个参数，表示只在特定的环境下渲染，例如

```
{{ render(''' '<a href="http://uoj.ac">UOJ</a>' ''', 'html') }}
```

上例表示只在html中渲染一个指向UOJ的超链接，当然UOJ中你还可以用md的超链接语法。第二个参数支持单个表示类型的字符串或是一个这样的字符串组成的list。其中支持的字符串包括：`html`，`tex`，`noi`，`uoj`，`ccpc`，`ccc`，`tuoj`，`ccc-tex`，`ccc-html`，`tuoj-tex`，`tuoj-html` 等。

### 表格

表格当然可以使用原生的 markdown 或是上文提到的两轮渲染进行，但考虑到题目中表格的特殊性，我们提供一种方式用 json 描述表格。
具体将 json 的模板放在 `tables` 目录下，用 `名称.json` 命名，下例为 `data.json`（同样，不含任何模板语法就是一个json），使用 null 表示和上一行合并单元格。
因此可以写成类似于下面的格式：
```js
[	
	["测试点", "$n, m$"]
	{%- set last = None -%}
	{% for datum in prob['data'] %}
	,[
		{%- for i in datum['cases'] -%}
			{{- i -}}
			{%- if not loop.last -%}
				,
			{%- endif -%}
		{%- endfor -%}",
		{%- if last and datum.args[0] == last[0] and datum.args[1] == last[1] -%}
			null
		{%- elif datum.args[0] == -1 and datum.args[1] == -1 -%}
			"无约束"
		{%- else -%}
			"
			{%- if datum.args[0] != -1 -%}
				$n,m \\le {{ tools.js_hn(datum.args[0]) }}$
			{%- endif -%}
			{%- if datum.args[0] != -1 and datum.args[1] != -1 -%}
				并且
			{%- endif -%}
			{%- if datum.args[1] != -1 -%}
				$nm \\le {{ tools.js_hn(datum.args[1]) }}$
			{%- endif -%}
			"
		{%- endif -%}
	]
	{% endfor %}
]
```

引用模板的地方，除了调用的函数改成了 `table`，其他和二次渲染类似。例如：
```
{{ render("table('data')") }}
```
