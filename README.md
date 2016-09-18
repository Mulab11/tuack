#oi_tools

## 目录结构

请严格遵循下列路径结构保存你的文件，否则部分工具无法正确运行。具体的某些文件格式见后文。

**所有基于文本的文件如果含有中文，必须用UTF-8编码。**

```
probs.json	//必须有一个文件说明每场比赛题目的顺序，具体格式见后文
title.tex	//如果要输出NOI风格的pdf，需要在这里定义比赛的名字，否则不需要这个文件
oi_tools	//把工具包放在这个位置
day1		//第一层是不同天/场次，如果只有一场，仍然需要一个文件夹
day2		//这层目录下可以有没有用的目录
	day_title.tex	//如果要输出NOI风格的pdf，需要在这里定义这一天的名字、时间等
	interval		//第二层目录是题目
	drink
	nodes			//注意这层目录下不要出现除了下述目录以外的目录，否则会被当做测试选手
		prob.json	//必须有一个文件说明这道题目的信息
		assignment[.pdf]		//命题报告，一个文件或文件夹，单文件用pdf、pptx、html等可以直接看的格式，文件夹必须用.dir结尾，下同
		discussion[.pdf]		//讲题/题目讨论PPT，一个文件或文件夹
		solution[.docx]			//题解
		data			//一定包含一个评测用数据的文件夹
			nodes1.in	//文件一定用<题目名称><编号>.<后缀名>的格式命名
			nodes1.ans	//标准输出文件是.ans
			...
			nodes10.ans
			chk		//checker统一使用chk命名，需要编译的话提供一个同名文件夹。!TODO：这里未来会增加对不同评测环境的支持，用make <环境名称>生成对应环境的chk，没有makefile则用g++进行编译。
				chk.cpp			//如果用正常的g++命令编译，就这么放
				testlib.h		//可以有其他文件
		down	//一定包含一个下发文件夹
			nodes1.in	//对于非提交答案题，这是第一个样例；对于提交答案题，这是第一个下发的输入，注意评测和下发的输入可以不同，因此要两个地方都放上in
			nodes1.ans	//这里的编号和题面中的样例编号相同，题面中出现的样例也要在这里给出
			nodes2.in
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
			n_log_n		//每个模拟选手的测试用一个文件夹装
				nodes.cpp或nodes1.ans	//这就是一个模拟选手，以后会改成用标准IO
			Dinic	//另一个模拟选手，名称随意，不要匹配到上文和下文的名称就行
				nodes1.ans
				...
			hehe.dir	//如果你有其他文件夹，觉得想分享给大家，又不是模拟选手，用.dir
			rename.py	//可以有其他想要分享的文件
		description.md	//题面，用markdown+jinja模板做（可以纯markdown）
		resources		//题面中使用的外部资源，例如图片、html或tex的模板（对于md无法表示的东西，需要分别写html和tex）
			1.jpg		//和题面中名称相同的图片
		tables			//需要用到的表格
			data.json	//和题面中名称相同的表格，用json+jinja模板做（可以纯json）
lectures	//有讲座的活动（WC、APIO等），讲座的东西（包括集训队交流）
	picks	//装在一个自己名字命名的文件夹里面
	vfk		//名字应该不会重复吧2333
```

需要两个题目描述文件，在根目录下的 `probs.json` 和每道题目目录下的 `prob.json`。

以下是 `probs.json` 的格式要求：

```js
{
	"day1" : ["excellent", "grid", "cyclic"],	//每天按照顺序放置题目的英文名称，必须要和目录的名称相同
	"day2" : ["interval", "drink", "nodes"]
}
```

以下是 `prob.json` 的格式要求：

```js
{
	"type" : "program",			//program传统，output提交答案，alternately交互
	"cnname" : "优秀的拆分",	//中文名称
	"time limit" : 1.5,			//时间限制，uoj会自动向上取整；TODO：如果不同环境限制不同，用{'noi' : 1.5, 'uoj' : 2.0}
	"memory limit" : "512 MB",	//空间限制，必须加上单位
	"test cases" : 20,			//测试点数量，TODO：如果不同测试点得分不同，或是打包评测，或是不按标准命名数据，则不加这一项
	"partial score" : false,	//是否有部分分，默认没有
	"compile" : {				//各个语言的编译开关
		"cpp" : "-O2 -lm",
		"c" : "-O2 -lm",
		"pas" : "-O2"
	},
	"sample count" : 3,			//样例的数量，提交答案题这里写0，如果要提供样例下发只在题面里引用就可以了
	"args" : [10, 30000],		//这是全局参数，由出题人自定义，会传给val，也可以在题面中引用
	"data" : [					//这是每个测试点的参数
		{
			"cases" : [1, 2],	//这是测试点1和2的公共参数
			"args" : [300, 1]	//这些测试点的参数，由出题人自定义，会传给val，也可以在题面中引用
		},
		{
			"cases" : [3, 4],
			"args" : [200, 1]
		},
		...
		{
			"cases" : [20],
			"args" : [30000, 0]
		}
	],
	"uoj id" : 3				//如果要使用上传到uoj的功能，需要填写这道题目的uoj题目id
}
```

## 基本使用方式

### 数据包生成

可以在根目录下运行下列命令生成对应的数据包：

```bash
python oi_tools/packer.py uoj,noi,release
```

表示生成uoj、noi和发布使用的数据包，生成多种包之间用逗号隔开。

目前支持输出下列种类的数据包：
* `test`：用于 `tester.py` 的数据包；
* `release`：用于发布的zip包；
* `noi`：noi风格的数据包；
* `uoj`：uoj风格的数据包，并自动上传到uoj。

如果需要上传到uoj，需要配置文件 `uoj.json`，安装svn，并在 `prob.json` 中添加 `uoj id` 参数。

### 测试

可以在根目录下运行下列命令进行测试：

```bash
python oi_tools/tester.py
```

其中结果将输出到对应天目录下的 `result` 目录下。

### 题面生成

可以在根目录下运行下列命令生成对应的题面：

```bash
python oi_tools/renderer.py uoj,noi
```

表示生成uoj和noi风格的题面，生成多种包之间用逗号隔开。

生成题面时，python必须安装 `jinja2` 包。

目前支持输出下列种类的数据包：
* `noi`：noi风格的题面，必须能使用 `pandoc` 和 `pdflatex` 命令；
* `uoj`：uoj风格的题面。

题面的书写后文将有详细说明。

### 只对特定的题目进行操作

前面几个工具都可以使用类似于 `-d day1,day2` 和 `-p day1/excellent,day2/drink,day1/grid` 来指定特定的天数或题目。例如：

```bash
python oi_tools/packer.py noi,release,test -d day1,day2
python oi_tools/tester.py -p day1/excellent,day2/drink
```

不要同时使用 `-d` 和 `-p`，`packer.py` 生成 `release` 时不能使用 `-p`。

## 题面的书写

如果你不使用任何的特性，你可以用纯 markdown 书写题面，并将以 `description.md` 命名保存在试题目录下。
此外还提供了少量的工具以扩展 markdown 不支持的功能。

注意：markdown原生支持嵌入html，但如果要渲染成tex，就不能直接使用任何原生html语法，具体可以参考后文。

目前两种输出类型渲染的步骤为：
* `noi`：md+jinja+\*jinja → md+jinja → tex+jinja → tex → pdf；
* `uoj`：md+jinja+\*jinja → md+jinja → md+html。

其中\*jinja表示经过jinja渲染会变成jinja模板的代码。

jinja2本身的语法戳[这里](http://docs.jinkan.org/docs/jinja2/templates.html)学习。

所有的模板都存在该工程的templates目录下，有兴趣开发模板或是想修改的话欢迎联系我入坑。

### description.md

可以参考NOI2016网格这题，下面提到的大部分功能在这个题目中都有使用，详细代码见NOI2016的[git工程](http://git.oschina.net/mulab/NOI2016)。

`{% block title %}{% endblock %}` 表示使用名为 `title` 的子块，这个子块在uoj模式下会渲染成时间、空间限制和题目类型（如果不为传统型的话），在noi模式下会留空。
这些子块定义在 `problem_base.md.jinja` 中，可用的还有：
* `input_file` 输入文件的描述，根据平台说明是标准输入还是从文件输入。
* `output_file` 输入文件的描述，根据平台说明是标准输入还是从文件输入。
* `user_path` 选手目录，如果是noi会变成“选手目录”这几个字，uoj会变成下载链接。
* `sample_text` 样例自动渲染，会自动从 `down` 中读入样例文件并添加到题面中，需要下面提到的前置变量。
* `sample_file` 一个不出现在题面，但是以文件形式提供的样例，同样需要下面提到的前置变量。
* `title_sample_description` uoj的“样例输入”是拆分成两级名称的，所以蛋疼地需要多一级。
* `title` 标题，包括时空限制、题目类型等。

一个块只能在代码中直接出现一次，如果需要多次使用，需要写成 `{{ self.块名称() }}` ，例如 `{{ self.title() }}`。
事实上，可以总是使用这种方式输出一个块，上面那种方式是为了更好地支持继承，因此我们推荐在造题的时候始终使用这种方式引用块。

有的块需要用到前置的变量，例如文字样例自动渲染需要提供样例的编号 `sample_id` 作为变量，具体会写成这样：
```
{% set vars = {} -%}
{%- do vars.__setitem__('sample_id', 1) -%}
{{ self.sample_text() }}
```

### 一些约定

题目标题用一级标题 `#`，在题面书写的时候并不需要加上。

每个小节标题，如 `【题目描述】` 用二级标题 `##`，会被渲染成Latex的subsection和html的h2。
（不要吐槽uoj上字体太大了，这里应该是uoj改css）

小节下的标题用三级标题 `###`，会被渲染成Latex的subsubsection和html的h3。
对于uoj，`【样例】` 下的 `输入` 会使用比上面第一级的标题，而这个在noi style的题面中会不单列一级标题；为了通用，建议使用上面提到的子块生成样例。

样例使用三个反引号（不知道markdown里面怎么打这几个字符）括起来的pre来装，同样建议用子块而非自己做样例。

公式用 `$` 括起来，单独占行的公式用 `$$` 括起来，例如 `$1 \le a_i \le n$`。

### 外部变量和小工具

通过变量 `prob` 可以获取你在 `prob.json` 中的各项参数，例如要输出题目的中文名，可以用下列写法（两种方法等价）：
```
{{ prob['cnname'] }}
{{ prob.cnname }}
```

获取当前的渲染环境，可以用变量 `io_style`（会被赋值为 `noi` 或 `uoj`）。

如果需要以文本的形式展示某个下发的文件，提供了一个函数 `down_file(file_name)`，例如：
```
## 【样例输出】
//这里应该有3个`
{{ down_file('grid1.ans') }}
//这里应该有3个`
```

考虑到不同情况下下发文件存储的位置不同，用函数 `file_name` 根据具体的环境生成具体的路径。
类似的还有 `resource` 函数，可以根据具体情况获取存储在 resources 文件夹中的资源（图片、模板等）。

此外，还有一组工具 `tools`，其中包括一些小轮子，具体可以阅读 `tools.py`。例如下列调用可以生成一个数适合阅读的格式：
```
${{ tools.hn(1000000) }}$
```

### 两轮渲染

图片、表格等东西markdown原生支持不太好（图片无法改变大小，表格无法合并单元格），因此提供了两轮渲染的方式，
即在两条路线共同的渲染之后，使用tex或html的模板再渲染一次。

例如提供了一对简单的图片模板 `image.tex.jinja` 和 `image.html.jinja`，使得可以使用以下语法渲染一张图片
```
{{ '{{' }} template('image', resource = resource('3.jpg'), size = 0.5, align = 'middle', inline = false) {{ '}}' }}
```
其中 `{{ '{{' }}` 使得这段文字在被渲染之后会被渲染成一个模板项。

如果要写一段自用的tex或html模板（当然你如果只需要嵌入tex或html，只需要再模板中不填入任何模板语法即可），
你可以在 `resources` 文件夹中写 `名称.tex.jinja` 和 `名称.html.jinja`，然后用下列方式插入：
```
{{ '{{' }} template(resource('image'), 模板参数表...) {{ '}}' }}
```
注意在tex中大括号会被转义，所以参数表不要使用大括号传，而使用变量赋值的方式传入。

### 表格

表格当然可以使用原生的 markdown 或是上文提到的两轮渲染进行，但考虑到题目中表格的特殊性，我们提供一种方式用 json 描述表格。
具体将 json 的模板放在 `tables` 目录下（同样，不含任何模板语法就是一个json），使用 null 表示和上一行合并单元格。
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
{{ '{{' }} table('data') {{ '}}' }}
```
