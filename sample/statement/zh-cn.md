{{ self.title() }}

## {{ _('Background') }}

这样的子标题是带国际化的，为了方便翻译和提取每个部分等。如果你的子标题不是本文中的这些，并且不需要国际化的话，你可将这些子标题直接写成这样：

```
## 题目背景
```

If you want an English statement file, just copy this file as `en.md` and replace any Chinese text into English.

如果你不需要某些章节，可以直接删除。比如这一段是“题目背景”，很多题目其实并不需要这一段。

*子标题请不要自己手动加方括号 `【】` 。*

## {{ _('Description') }}

**要强调的东西**这么写。

行内的公式：$\sin \left(a x + b \right)$。

行间的公式：
$$
\frac{-b\pm\sqrt{b^2-4ac} }{2a}
$$

1. 第一点
2. 第二点

* 第一点
* 第二点

字符串或代码 `This is a string`

```
int main(int argc, char** argv);
```

除公式内可以使用tex的部分语法外，不要直接使用任何html语法和tex语法。替代方案如下：

不要用markdown自带的语法插入图片（因为目前支持不好），用下列语法插入图片：

{{ img('sample.png', size = 0.5, align = 'middle', inline = False) }}

其中 `inline` 为 `False` 表示这是一个独占一行的图片，此时支持 `align`，选项为 `left`，`middle` 或 `right`。后面这些参数可以不写。

图片需要保存在试题目录的 `resources` 子目录下。

如果有本工具不能提供的功能，需要直接使用 tex 或 html 代码的，请使用下列方式以免另外一种格式下出错。（注意代码不要放在```中）

```python
{{ render(json.dumps('\\clearpage'), 'tuoi') }}
{{ render(json.dumps('<a href="http://oj.thusaac.org">TUOJ</a>'), 'html') }}
```

上述第一个例子是为了排版好看强行加入一个分页符的意思，其中 `tuoi` 表示只在生成 TUOI 风格题面的时候使用这个；第二个例子是在生成任何 html 格式题目的时候加入一个广告（雾）。

可选的参数有 `html`，`md`，`tex`，`noi`，`uoj`，`ccpc`，`ccc`，`tuoj`，`ccc-tex`，`ccc-md`，`tuoi`，`tupc`。

**不要在题面里直接写tex或html代码！**

## {{ _('Input Format') }}

{{ self.input_file() }}

上面会根据具体的评测环境说明输入是文件还是标准输入等。

输入第一行包含一个正整数 $n$，保证 $n \le {{ tools.hn(prob.args['n']) }}$。←这是引用 `conf.json` 中的 `args` 的 `n` 项，然后用“好看”的格式输出。“好看”的格式如 `$10^9$`，`1,000,000,007`。

## {{ _('Output Format') }}

{{ self.output_file() }}

下面是自动读入样例 `1.in/ans`（存储在 `down` 文件夹内） 然后渲染到题面中；如果只有一组样例，则去掉前两行，样例仍然保存成 `1.in/ans`。其中 `1` 可以是字符串。

{% set vars = {} -%}
{%- do vars.__setitem__('sample_id', 1) -%}
{{ self.sample_text() }}

{{ self.title_sample_description() }}

这是第一组数据的样例说明。

下面是只提示存在第二组样例，但不渲染到题面中。

{% do vars.__setitem__('sample_id', 2) -%}
{{ self.sample_file() }}

## {{ _('Subtasks') }}

不要使用markdown原生的表格，使用下列方式渲染一个表格，其中表格存放在试题目录的 `tables` 子目录下。

{{ tbl('data') }}

{{ tbl('table', {'width' : [1, 6]}) }}

表格的例子见 `oi_tools/sample/tables`。原理上用一个二维的json表格存储，`null` 表示和上一行合并，不支持横向合并。建议用python的格式写，如例子中的 `data.py`，这样可以根据数据生成；跟数据无关的表格则可以像 `table.json` 那样存储。

## {{ _('Scoring') }}

这是评分方法，如果有必要的话。

## {{ _('Hint') }}

这里是一个非常温馨的提示。