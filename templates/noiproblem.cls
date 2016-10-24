%% 信息学奥林匹克中国国家队候选队员论文模板→NOI题面模板
%% 模板作者：胡伟栋
%% 模板修改：余林韵，陈许旻
%%
\NeedsTeXFormat{LaTeX2e}[1999/12/01]
\ProvidesClass{noiproblem}
[2016/09/10 1.0 Template for NOI Problem]
\LoadClass[12pt, a4paper]{article}
\RequirePackage{enumerate}
\RequirePackage{graphicx,subfigure}
\RequirePackage{amsmath,amsthm,amsfonts,amssymb,bm}
\RequirePackage{txfonts}
\RequirePackage{CJK}
\RequirePackage[adobefonts]{ctex}
\RequirePackage{longtable,multirow}
\RequirePackage{color,xcolor}
\RequirePackage{courier}
\RequirePackage{ifthen}
\RequirePackage{calc}
\RequirePackage{ifpdf}
\RequirePackage{titling}
\RequirePackage{listings}
\RequirePackage{fancyhdr}
\RequirePackage{algorithm,algorithmic}
\RequirePackage{booktabs}
\RequirePackage{ulem}
\usepackage{lastpage}
\usepackage{sectsty}
\usepackage{lipsum}
\usepackage{mathtools,framed,graphicx,xcolor}
\usepackage{titlesec}
\usepackage{fixltx2e}
\usepackage{makecell}
\usepackage{tabularx}
\usepackage{CJKfntef}
\usepackage{fancyvrb}
\usepackage{enumitem}
\usepackage{tabto}
\usepackage{microtype}

%% 页边距
\setlength{\textwidth}{\paperwidth}
\setlength{\textheight}{\paperheight}
\setlength\marginparwidth{0cm}
\setlength\marginparsep{0cm}
\setlength{\oddsidemargin}{0cm}
\setlength{\evensidemargin}{\oddsidemargin}
\setlength{\voffset}{-0.5cm-20pt}
% \addtolength{\textwidth}{-6.4cm}
\addtolength{\textwidth}{-2in}
\setlength{\headheight}{20pt}
\setlength{\topskip}{0pt}
\setlength{\skip\footins}{15pt}
% \setlength{\topmargin}{2.8cm-1in}
\setlength{\topmargin}{0cm}
\setlength{\footskip}{1.5cm}
\setlength{\headsep}{0.5cm}
% \addtolength{\textheight}{-8.6cm}
\addtolength{\textheight}{-2in-1.5cm+0.5cm+20pt}

%% 不显示章节标号
\renewcommand\thesection{}
\renewcommand\thesubsection{}
\renewcommand\thesubsubsection{}

%% title formats %% It doesn't work now QAQ
% \titleformat{\section}{\Large}{~}{0ex}{}
% \sectionfont{\fontsize{180bp}{180bp}}
%\titleformat*{\subsection}{\Large\bfseries}
%\titleformat*{\subsubsection}{\large\bfseries}
%\titleformat*{\paragraph}{\large\bfseries}
%\titleformat*{\subparagraph}{\large\bfseries}

%% 三线表格
\newcommand{\bhline}{\Xhline{5\arrayrulewidth}}
\newcommand{\mhline}{\Xhline{3\arrayrulewidth}}

%% 页眉页脚
\pagestyle{fancy}
\renewcommand{\headheight}{20pt}
\renewcommand{\headrulewidth}{0.2pt}
\renewcommand{\footrulewidth}{0pt}

%% \renewcommand{\sectionmark}[1]{\markleft{#1}}

\rhead{\parbox{\textwidth}{\raggedleft\textnormal{
	\footnotesize
	\ifdefined \theday
		\theday
	\fi
	\nouppercase \leftmark
}}}
\lhead{\parbox{\textwidth}{\textnormal{
	\footnotesize \thetitle
	\ifdefined\subtitle
		\subtitle
	\fi
}}}
\chead{}
\lfoot{}
\cfoot{\parbox{\textwidth}{\centering \footnotesize 第~ \thepage{} 页 ~~~~ 共~ \pageref{LastPage} 页}}
\rfoot{}

\fancypagestyle{Cover}{%
    \fancyhead{}
	\fancyfoot{}
	\renewcommand{\headheight}{0pt}
    \renewcommand{\headrulewidth}{0pt}
	\renewcommand{\footrulewidth}{0pt}
}

%% 字体
\newcommand{\song}{\CJKfamily{song}}    % 宋体
\def\songti{\song}
\newcommand{\fs}{\CJKfamily{fs}}        % 仿宋体
\def\fangsong{\fs}
\newcommand{\kai}{\CJKfamily{kai}}      % 楷体
\def\kaishu{\kai}
\newcommand{\hei}{\CJKfamily{hei}}      % 黑体
\def\heiti{\hei}
\newcommand{\li}{\CJKfamily{li}}        % 隶书
\def\lishu{\li}
\newcommand{\you}{\CJKfamily{you}}      % 幼圆
\def\youyuan{\you}

%% 字号
\newlength\noilinespace
\newcommand{\noiChooseFont}[2]{
   \setlength{\noilinespace}{#2*\real{#1}}
   \fontsize{#2}{\noilinespace}\selectfont}
\def\noiDefineFontsize#1#2{
  \expandafter\newcommand\csname #1\endcsname[1][\baselinestretch]{
    \noiChooseFont{##1}{#2}}}
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

%% New page at every chapter %% It doesn't work now QAQ
% \newcommand{\sectionbreak}{\clearpage}

%% Some styles
%% \newcommand{\filename}[1]{\bfseries \textit{#1}}
\renewcommand{\textbf}[1]{{\bfseries \underline{#1}}}
\renewcommand{\emph}[1]{{\bfseries \textit{#1}}}
\renewcommand{\texttt}[1]{{\ttfamily \underline{#1}}}

%% 代码/样例块
\DefineVerbatimEnvironment{verbatim}{Verbatim}{xleftmargin=2em}

%% 枚举类型间距
\setenumerate[1]{itemsep=0pt,partopsep=0pt,parsep=\parskip,topsep=0pt,leftmargin=3em}
\setitemize[1]{itemsep=0pt,partopsep=0pt,parsep=\parskip,topsep=0pt,leftmargin=3em}
\setdescription{itemsep=0pt,partopsep=0pt,parsep=\parskip,topsep=0pt,leftmargin=3em}

\renewenvironment{abstract}{
\section*{摘~~要}
\kai
}{}

\renewcommand\tableofcontents{%
  \section*{目~~录}
  \@starttoc{toc}\normalsize}

\renewcommand\section{\@startsection{section}{1}{\z@}%
                     {-24bp \@plus -1ex \@minus -.2ex}%
                     {6bp \@plus .2ex}%
                     {\hei \sihao[1.429]}}
\renewcommand\subsection{\@startsection{subsection}{2}{\z@}%
                        {-16bp \@plus -1ex \@minus -.2ex}%
                        {6bp \@plus .2ex}%
                        {\hei\banxiaosi[1.538]}}
\renewcommand\subsubsection{\@startsection{subsubsection}{3}{\z@}%
                           {-16bp \@plus -1ex \@minus -.2ex}%
                           {6bp \@plus .2ex}%
                           {\hei \xiaosi[1.667]}}

\if 0

\fi
