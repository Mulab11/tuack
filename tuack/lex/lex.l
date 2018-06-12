%{
#include "main.h"
#include "yacc.tab.h"

#undef YY_INPUT
#define YY_INPUT(buf,result,max_size) { \
	int c = fgetc(yyin); \
	result = (c == EOF) ? YY_NULL : (buf[0] = c, 1); \
	myoffset++;\
	}

extern "C" {
	int yywrap(void);
	int yylex(void);
	ostream& warn();
	ostream& info();
	ostream& error();
	int myoffset;
}

%}

%x TXT1
%x EQU1
%x EQU1T

%x TXTS
%x EQUS
%x EQUST

%x JJV
%x JJC

zhpunc		(，|。|《|》|？|；|〈|〉|：|“|”|‘|’|【|】|（|）|、|！|—|·|…|「|」|『|』|〔|〕|–|．)
zhchar		(\xE2[\xBA-\xBF][\x80-\xBF]|\xE3\x80\x87|\xE3[\x81-\xBF][\x80-\xBF]|[\xE4-\xEE][\x80-\xBF][\x80-\xBF]|\xEF[\x80-\xAB][\x80-\xBF])
elchar		([Α|Β|Γ|Δ|Ε|Ζ|Η|Θ|Ι|Κ|Λ|Μ|Ν|Ξ|Ο|Π|Ρ|Σ|Τ|Υ|Φ|Χ|Ψ|Ω|α|β|γ|δ|ε|ζ|η|θ|ι|κ|λ|μ|ν|ξ|ο|π|ρ|σ|τ|υ|φ|χ|ψ|ω])
enpunc		([,.?;:'"'!]|\\`)
symbol		([/\\<>\|=_@#&]|\\~|\\\$)
enchar		([A-Za-z])
sp			(\ )
tab			(\t)
fbblank		([\f\r\v])
blank		([\ \t\f\r\v])
digit		([0-9])
langchar	(digit|enpunc|enchar)

number		([+-]?((({digit}|,)+\.?{digit}*|\.{digit}+))(e[+-]?{digit}+)?)
enword		({enchar}+)
langname	({langchar}+)

jjvlq		(\{\{)
jjvrq		(\}\})
jjclq		(\{%)
jjcrq		(%\})

ltxtq		(```)
stxtq		(`)
lequq		(\$\$)
sequq		(\$)
ltxtt		(    )

%%

^[ \t]*([-+*]|{digit}+\.){sp}	{
	//cout << "【首】" << yytext;
}

，，|，。|，；|，：|，！|，、|，！|。，|。。|。？|。；|。：|。、|。！|？，|？。|？；|？：|？、|；，|；。|；？|；；|；：|；、|；！|：，|：。|：？|：；|：：|：、|：！|、，|、。|、？|、；|、：|、、|、！|！，|！。|！；|！：|！、		{
	warn() << "下列标点不应该连用`" << yytext << "`。" << endl;
}

！！|！？|？！|？？		{
	info() << "下列标点连用前请认真检查语气是否足够强烈`" << yytext << "`。" << endl;
}

({zhchar}|{zhpunc}){blank}({zhchar}|{zhpunc})		{
	warn() << "下列中文或标点之间不应该插入空白符`" << yytext << "`。" << endl;
}

({enword}|{elchar}){blank}{zhpunc}		{
	warn() << "下列外文和标点之间不应该插入空白符`" << yytext << "`。" << endl;
}

{zhpunc}{blank}({enword}|{elchar})		{
	warn() << "下列标点和外文之间不应该插入空白符`" << yytext << "`。" << endl;
}

{zhchar}({enchar}|{elchar})|({enchar}|{elchar}){zhchar}					{
	warn() << "下列中文和外文之间应当插入空格`" << yytext << "`。" << endl;
}

({zhchar}|{enword}|{elchar})$		{
	warn() << "行末应当有标点符号`" << yytext << "`。" << endl;
}

{zhchar}		{
	//cout << yytext;
}

{zhpunc}		{
	//cout << "【标】" << yytext;
}

{enword}		{
	//cout << "【词】" << yytext;
	if(yyleng == 1 && (('b' <= yytext[0] && yytext[0] <= 'z') || ('K' <= yytext[0] && yytext[0] <= 'N')))
		info() << "字符`" << yytext << "`可能是一个变量，是的话请放在公式中。" << endl;
}
				
{number}		{
	if(yyleng >= 3)
		warn() << "数`" << yytext << "`比较长，考虑放入公式中并使用变量保存。" << endl;
	//cout << "【数】" << yytext;
}

{enpunc}		{
	warn() << "一般不应该出现英文标点`" << yytext << "`。" << endl;
}

\t				{
	warn() << "非行首一般不应该出现制表符。" << endl;
}

{symbol}		{
	//cout << "【符】" << yytext;
}

{ltxtq}{langname}?$			{
	//cout << "【↓块1】" << yytext + 3;
	BEGIN TXT1;
}

<TXT1>{ltxtq}$			{
	//cout << "【↑块1】" << endl;
	BEGIN INITIAL;
}

<TXT1>.					{
	//cout << yytext;
}

({zhchar}|{enword}|{elchar}){stxtq}		{
	warn() << "文字和字符串之间应当插入空格`" << yytext << "`。" << endl;
	BEGIN TXTS;
}

{zhpunc}{blank}{stxtq}		{
	warn() << "标点和字符串之间不应当插入空格。" << endl;
	BEGIN TXTS;
}

{stxtq}			{
	//cout << "【<s】";
	BEGIN TXTS;
}

<TXTS>{stxtq}({zhchar}|{enword}|{elchar})		{
	warn() << "字符串和文字之间应当插入空格`" << yytext << "`。" << endl;
	BEGIN INITIAL;
}

<TXTS>{stxtq}{blank}{zhpunc}		{
	warn() << "字符串和标点之间不应当插入空格。" << endl;
	BEGIN INITIAL;
}

<TXTS>{stxtq}	{
	//cout << "【s>】";
	BEGIN INITIAL;
}

<TXTS>\n			{
	error() << "行内字符串不能包含换行。" << endl;
	BEGIN INITIAL;
}

<TXTS>.			{
	//cout << yytext;
}

{lequq}$				{
	//cout << "【↓式1】" << endl;
	BEGIN EQU1;
}

<EQUS>sin|cos|tan|cot|sec|csc|log|min|max|ln|lg	{
	warn() << "在公式中`" << yytext << "`应该写成`\\" << yytext << "`。" << endl;
}

<EQU1>sin|cos|tan|cot|sec|csc|log|min|max|ln|lg	{
	warn() << "在公式中`" << yytext << "`应该写成`\\" << yytext << "`。" << endl;
}

<EQUS>mod	{
	info() << "在公式中`mod`一般写成`\\bmod`。" << endl;
}

<EQU1>mod	{
	info() << "在公式中`mod`一般写成`\\bmod`。" << endl;
}

<EQUS>\*	{
	info() << "在公式中一般不用星号`*`做乘号，而用叉乘`\\times`、点乘`\\cdot`或省略。" << endl;
}

<EQU1>\*	{
	info() << "在公式中一般不用星号`*`做乘号，而用叉乘`\\times`、点乘`\\cdot`或省略。" << endl;
}

<EQUS>\/	{
	info() << "在公式中一般不用斜杠`/`做除号，而用除号`\\div`或分数`\\frac{1}{2}`。" << endl;
}

<EQU1>\/	{
	info() << "在公式中一般不用斜杠`/`做除号，而用除号`\\div`或分数`\\frac{1}{2}`。" << endl;
}

<EQUS>{number}		{
	if(yyleng >= 3)
		warn() << "数`" << yytext << "`比较长，考虑使用变量保存。" << endl;
}

<EQU1>{number}		{
	if(yyleng >= 3)
		warn() << "数`" << yytext << "`比较长，考虑使用变量保存。" << endl;
}

<EQU1>\\				{
	//cout << yytext;
	BEGIN EQU1T;
}

<EQU1T>bmod				{
	//cout << yytext;
	BEGIN EQU1;
}

<EQU1T>.				{
	//cout << yytext;
	BEGIN EQU1;
}

<EQU1>{lequq}$			{
	//cout << "【↑式1】" << endl;
	BEGIN INITIAL;
}

<EQU1>.					{
	//cout << yytext;
}

{sequq}{blank}		{
	error() << "行内公式前$后不能加空格。" << endl;
	BEGIN EQUS;
}

({zhchar}|{enword}|{elchar}){sequq}		{
	warn() << "文字和公式之间应当插入空格`" << yytext << "`。" << endl;
	BEGIN EQUS;
}

{zhpunc}{blank}{sequq}		{
	warn() << "标点和公式之间不应当插入空格。" << endl;
	BEGIN EQUS;
}

{sequq}			{
	//cout << "【<e】";
	BEGIN EQUS;
}

<EQUS>\\				{
	//cout << yytext;
	BEGIN EQUST;
}

<EQUST>bmod				{
	//cout << yytext;
	BEGIN EQUS;
}

<EQUST>.				{
	//cout << yytext;
	BEGIN EQUS;
}

<EQUS>\n		{
	error() << "行内公式不能换行。" << endl;
	BEGIN INITIAL;
}

<EQUS>{sp}{sequq}	{
	error() << "行内公式后$前不能加空格。" << endl;
	BEGIN INITIAL;
}

<EQUS>{sequq}({zhchar}|{enword}|{elchar})		{
	warn() << "公式和文字之间应当插入空格`" << yytext << "`。" << endl;
	BEGIN INITIAL;
}

<EQUS>{sequq}{blank}{zhpunc}		{
	warn() << "公式和标点之间不应当插入空格。" << endl;
	BEGIN INITIAL;
}

<EQUS>{sequq}	{
	//cout << "【e>】";
	BEGIN INITIAL;
}

<EQUS>.			{
	//cout << yytext;
}

{jjvlq}			{
	//cout << "【<v】";
	BEGIN JJV;
}

<JJV>{jjvrq}	{
	//cout << "【v>】";
	BEGIN INITIAL;
}

<JJV>.			{
	//cout << yytext;
}

{jjclq}			{
	//cout << "【<c】";
	BEGIN JJV;
}

<JJC>{jjcrq}	{
	//cout << "【c>】";
	BEGIN INITIAL;
}

<JJC>.			{
	//cout << yytext;
}

{sp}			{
	//cout << "【空】";
}

\n				{
	//cout << "【换】" << endl;
}

.				{
	//cout << "【??】" << yytext;
}

%%

int yywrap(void)
{
	return 1;
}

ostream& error(){
	return cerr << "E " << myoffset << " ";
}

ostream& warn(){
	return cerr << "W " << myoffset << " ";
}

ostream& info(){
	return cerr << "I " << myoffset << " ";
}
