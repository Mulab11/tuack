\NeedsTeXFormat{LaTeX2e}[1999/12/01]
\ProvidesClass{tuack}
\LoadClass[12pt, a4paper]{article}
\usepackage{enumerate}
\usepackage{graphicx,subfigure}
\usepackage{amsmath,amsthm,amsfonts,amssymb,bm}
\usepackage{txfonts}
\usepackage[BoldFont,SlantFont,CJKchecksingle]{xeCJK}
\setCJKmainfont[BoldFont=SimHei]{SimSun}
\setCJKmonofont{SimSun}
\setmonofont{Consolas}
\usepackage{longtable,multirow}
\usepackage{color,xcolor}
\usepackage{courier}
\usepackage{ifthen}
\usepackage{calc}
\usepackage{ifpdf}
\usepackage{titling}
\usepackage{listings}
\usepackage{fancyhdr}
\usepackage{booktabs}
\usepackage{ulem}
\usepackage{lastpage}
\usepackage{lipsum}
\usepackage{mathtools,framed,graphicx,xcolor}
\usepackage{titlesec}
\usepackage{fixltx2e}
\usepackage{makecell}
\usepackage{tabularx}
\usepackage{fancyvrb}
\usepackage{enumitem}
\usepackage{tabto}
\usepackage{ulem}
\usepackage{ifxetex,ifluatex}
\usepackage{caption}

\XeTeXlinebreaklocale "zh"
\XeTeXlinebreakskip = 0pt plus 1pt minus 0.1pt

\usepackage[T1]{fontenc}
\usepackage{indentfirst}
\setlength{\parindent}{2em}
\renewcommand{\baselinestretch}{1.3}

%% 页边距
\setlength{\textwidth}{\paperwidth}
\setlength{\textheight}{\paperheight}
\setlength\marginparwidth{0cm}
\setlength\marginparsep{0cm}
\setlength{\oddsidemargin}{0cm}
\setlength{\evensidemargin}{\oddsidemargin}
\setlength{\voffset}{-0.5cm-20pt}
\addtolength{\textwidth}{-2in}
\setlength{\topskip}{0pt}
\setlength{\skip\footins}{15pt}
\setlength{\topmargin}{0cm}
\setlength{\footskip}{1.5cm}
\setlength{\headsep}{0.5cm}
\addtolength{\textheight}{-2in-1.5cm+0.5cm+20pt}

%% 不显示章节标号
\renewcommand\thesection{}
\renewcommand\thesubsection{}
\renewcommand\thesubsubsection{}

%% 三线表格
\newcommand{\bhline}{\Xhline{5\arrayrulewidth}}
\newcommand{\mhline}{\Xhline{3\arrayrulewidth}}

%% 页眉页脚
\pagestyle{fancy}
\renewcommand{\headheight}{20pt}
\renewcommand{\headrulewidth}{0.2pt}
\renewcommand{\footrulewidth}{0pt}

\fancypagestyle{Cover}{
    \fancyhead{}
	\fancyfoot{}
	\renewcommand{\headheight}{0pt}
    \renewcommand{\headrulewidth}{0pt}
	\renewcommand{\footrulewidth}{0pt}
}

%% 字体
\setCJKfamilyfont{song}{SimSun}                             %宋体 song  
\newcommand{\song}{\CJKfamily{song}}                        % 宋体   (Windows自带simsun.ttf)  
\setCJKfamilyfont{xs}{NSimSun}                              %新宋体 xs  
\newcommand{\xs}{\CJKfamily{xs}}  
\setCJKfamilyfont{fs}{FangSong}                      %仿宋2312 fs  
\newcommand{\fs}{\CJKfamily{fs}}                            %仿宋体 (Windows自带simfs.ttf)  
\setCJKfamilyfont{kai}{KaiTi}                        %楷体2312  kai  
\newcommand{\kai}{\CJKfamily{kai}}                            
\setCJKfamilyfont{yh}{Microsoft YaHei}                    %微软雅黑 yh  
\newcommand{\yh}{\CJKfamily{yh}}  
\setCJKfamilyfont{hei}{SimHei}                                    %黑体  hei  
\newcommand{\hei}{\CJKfamily{hei}}                          % 黑体   (Windows自带simhei.ttf)  
\setCJKfamilyfont{msunicode}{Arial Unicode MS}            %Arial Unicode MS: msunicode  
\newcommand{\msunicode}{\CJKfamily{msunicode}}  
\setCJKfamilyfont{li}{LiSu}                                            %隶书  li  
\newcommand{\li}{\CJKfamily{li}}  
\setCJKfamilyfont{yy}{YouYuan}                             %幼圆  yy  
\newcommand{\yy}{\CJKfamily{yy}}  
\setCJKfamilyfont{xm}{MingLiU}                                        %细明体  xm  
\newcommand{\xm}{\CJKfamily{xm}}  
\setCJKfamilyfont{xxm}{PMingLiU}                             %新细明体  xxm  
\newcommand{\xxm}{\CJKfamily{xxm}}  
  
\setCJKfamilyfont{hwsong}{STSong}                            %华文宋体  hwsong  
\newcommand{\hwsong}{\CJKfamily{hwsong}}  
\setCJKfamilyfont{hwzs}{STZhongsong}                        %华文中宋  hwzs  
\newcommand{\hwzs}{\CJKfamily{hwzs}}  
\setCJKfamilyfont{hwfs}{STFangsong}                            %华文仿宋  hwfs  
\newcommand{\hwfs}{\CJKfamily{hwfs}}  
\setCJKfamilyfont{hwxh}{STXihei}                                %华文细黑  hwxh  
\newcommand{\hwxh}{\CJKfamily{hwxh}}  
\setCJKfamilyfont{hwl}{STLiti}                                        %华文隶书  hwl  
\newcommand{\hwl}{\CJKfamily{hwl}}  
\setCJKfamilyfont{hwxw}{STXinwei}                                %华文新魏  hwxw  
\newcommand{\hwxw}{\CJKfamily{hwxw}}  
\setCJKfamilyfont{hwk}{STKaiti}                                    %华文楷体  hwk  
\newcommand{\hwk}{\CJKfamily{hwk}}  
\setCJKfamilyfont{hwxk}{STXingkai}                            %华文行楷  hwxk  
\newcommand{\hwxk}{\CJKfamily{hwxk}}  
\setCJKfamilyfont{hwcy}{STCaiyun}                                 %华文彩云 hwcy  
\newcommand{\hwcy}{\CJKfamily{hwcy}}  
\setCJKfamilyfont{hwhp}{STHupo}                                 %华文琥珀   hwhp  
\newcommand{\hwhp}{\CJKfamily{hwhp}}  
  
\setCJKfamilyfont{fzsong}{Simsun (Founder Extended)}     %方正宋体超大字符集   fzsong  
\newcommand{\fzsong}{\CJKfamily{fzsong}}  
\setCJKfamilyfont{fzyao}{FZYaoTi}                                    %方正姚体  fzy  
\newcommand{\fzyao}{\CJKfamily{fzyao}}  
\setCJKfamilyfont{fzshu}{FZShuTi}                                    %方正舒体 fzshu  
\newcommand{\fzshu}{\CJKfamily{fzshu}}  
  
\setCJKfamilyfont{asong}{Adobe Song Std}                        %Adobe 宋体  asong  
\newcommand{\asong}{\CJKfamily{asong}}  
\setCJKfamilyfont{ahei}{Adobe Heiti Std}                            %Adobe 黑体  ahei  
\newcommand{\ahei}{\CJKfamily{ahei}}  
\setCJKfamilyfont{akai}{Adobe Kaiti Std}                            %Adobe 楷体  akai  
\newcommand{\akai}{\CJKfamily{akai}}  

%% 字号
\newlength\noilinespace
\newcommand{\noiChooseFont}[2]{
   \setlength{\noilinespace}{ #2*\real{ #1 } }
   \fontsize{ #2 }{\noilinespace}\selectfont}
\def\noiDefineFontsize#1#2{
  \expandafter\newcommand\csname #1\endcsname[1][\baselinestretch]{
    \noiChooseFont{ ##1 }{ #2 }}}
\noiDefineFontsize{chuhao}{42bp}
\noiDefineFontsize{xiaochu}{36bp}
\noiDefineFontsize{yihao}{26bp}
\noiDefineFontsize{xiaoyi}{24bp}
\noiDefineFontsize{erhao}{22bp}
\noiDefineFontsize{xiaoer}{18bp}
\noiDefineFontsize{sanhao}{16bp}
\noiDefineFontsize{xiaosan}{15bp}
\noiDefineFontsize{sihao}{14bp}
\noiDefineFontsize{banxiaosi}{13bp}
\noiDefineFontsize{xiaosi}{12bp}
\noiDefineFontsize{dawu}{11bp}
\noiDefineFontsize{wuhao}{10.5bp}
\noiDefineFontsize{xiaowu}{9bp}
\noiDefineFontsize{liuhao}{7.5bp}
\noiDefineFontsize{xiaoliu}{6.5bp}
\noiDefineFontsize{qihao}{5.5bp}
\noiDefineFontsize{bahao}{5bp}

%% Some styles
%% \newcommand{\filename}[1]{\bfseries\textit{#1}}
\renewcommand{\textbf}[1]{{\bfseries\CJKunderdot{#1}}}
\renewcommand{\emph}[1]{{\bfseries\textit{#1}}}
\renewcommand{\texttt}[1]{{\ttfamily\uline{#1}}}

%% 代码/样例块
\DefineVerbatimEnvironment{verbatim}{Verbatim}{xleftmargin=2em}

%% 枚举类型间距
\setenumerate[1]{itemsep=0pt,partopsep=0pt,parsep=\parskip,topsep=0pt,leftmargin=3em}
\setitemize[1]{itemsep=0pt,partopsep=0pt,parsep=\parskip,topsep=0pt,leftmargin=3em}
\setdescription{itemsep=0pt,partopsep=0pt,parsep=\parskip,topsep=0pt,leftmargin=3em}

\renewcommand\section{
	\@startsection{section}{1}{\z@}
	{-24bp \@plus -1ex \@minus -.2ex}
	{6bp \@plus .2ex}
	{\hei \xiaoer[1.429]}
}

\renewcommand{\sectionmark}[1]{\markright{#1}}
\renewcommand{\subsectionmark}[1]{ }
\renewcommand{\subsubsectionmark}[1]{ }
\newcommand{\sqbr}[1]{【#1】}
\titleformat{\subsection}{\hei\banxiaosi}{}{1em}{\sqbr}

\renewcommand\subsubsection{
	\@startsection{subsubsection}{3}{\z@}
	{-16bp \@plus -1ex \@minus -.2ex}
	{6bp \@plus .2ex}%
	{\hei \xiaosi[1.667]}
}

\newcommand{\tightlist}{\setlength{\itemsep}{0pt}\setlength{\parskip}{0pt}}

\renewcommand\tableofcontents{
	{\xiaosan \bfseries \thecontent \par}
	{\xiaosi \@starttoc{toc}}
}

\DeclareMathOperator{\xor}{xor}
\DeclarePairedDelimiter{\abs}{\lvert}{\rvert}

% 高亮的代码
\ifxetex
  \usepackage{fontspec,xltxtra,xunicode}
  \defaultfontfeatures{Mapping=tex-text,Scale=MatchLowercase}
  \newcommand{\euro}{€}
\else
  \ifluatex
    \usepackage{fontspec}
    \defaultfontfeatures{Mapping=tex-text,Scale=MatchLowercase}
    \newcommand{\euro}{€}
  \else
    \usepackage[utf8]{inputenc}
    \usepackage{eurosym}
  \fi
\fi
%\DefineShortVerb[commandchars=\\\{\}]{\|}
%\DefineVerbatimEnvironment{Highlighting}{Verbatim}{commandchars=\\\{\}}
% Add ',fontsize=\small' for more characters per line
\newenvironment{Shaded}{\definecolor{shadecolor}{rgb}{0.8,0.8,0.8} \begin{shaded*} }{ \end{shaded*}}

\newcommand{\KeywordTok}[1]{\textcolor[rgb]{0.00,0.44,0.13}{\textbf{{#1}}}}
\newcommand{\DataTypeTok}[1]{\textcolor[rgb]{0.56,0.13,0.00}{{#1}}}
\newcommand{\DecValTok}[1]{\textcolor[rgb]{0.25,0.63,0.44}{{#1}}}
\newcommand{\BaseNTok}[1]{\textcolor[rgb]{0.25,0.63,0.44}{{#1}}}
\newcommand{\FloatTok}[1]{\textcolor[rgb]{0.25,0.63,0.44}{{#1}}}
\newcommand{\CharTok}[1]{\textcolor[rgb]{0.25,0.44,0.63}{{#1}}}
\newcommand{\StringTok}[1]{\textcolor[rgb]{0.25,0.44,0.63}{{#1}}}
\newcommand{\CommentTok}[1]{\textcolor[rgb]{0.38,0.63,0.69}{\textit{{#1}}}}
\newcommand{\OtherTok}[1]{\textcolor[rgb]{0.00,0.44,0.13}{{#1}}}
\newcommand{\AlertTok}[1]{\textcolor[rgb]{1.00,0.00,0.00}{\textbf{{#1}}}}
\newcommand{\FunctionTok}[1]{\textcolor[rgb]{0.02,0.16,0.49}{{#1}}}
\newcommand{\RegionMarkerTok}[1]{{#1}}
\newcommand{\ErrorTok}[1]{\textcolor[rgb]{1.00,0.00,0.00}{\textbf{{#1}}}}
\newcommand{\NormalTok}[1]{{#1}}
\ifxetex
  \usepackage[setpagesize=false, % page size defined by xetex
              unicode=false, % unicode breaks when used with xetex
              xetex,
              colorlinks=true,
              linkcolor=blue]{hyperref}
\else
  \usepackage[unicode=true,
              colorlinks=true,
              linkcolor=blue]{hyperref}
\fi
\hypersetup{breaklinks=true, pdfborder={0 0 0}}
%\setlength{\parindent}{0pt}
%\setlength{\parskip}{6pt plus 2pt minus 1pt}
%\setlength{\emergencystretch}{3em}  % prevent overfull lines
%\setcounter{secnumdepth}{0}

%\EndDefineVerbatimEnvironment{Highlighting}

