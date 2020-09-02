\NeedsTeXFormat{LaTeX2e}[1999/12/01]
\ProvidesClass{tuack}


\LoadClass[12pt,a4paper,fontset=windowsnew]{ctexart}
\usepackage{enumerate}
\usepackage{graphicx,subfigure}
\usepackage{amsmath,amsthm,amsfonts,amssymb,bm}
\usepackage{longtable,multirow}
\usepackage{color,xcolor}
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
\usepackage{mathtools,framed}
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
\usepackage{hyperref}
\usepackage{geometry}
\usepackage{xeCJKfntef}


% default mono fonts
\setCJKmonofont{SimSun}
\setmonofont{Consolas}


%% 页边距
\geometry{
	a4paper,
	left=2.5cm,
	right=2.5cm,
	top=2.5cm,
	bottom=2.5cm
}
\renewcommand{\baselinestretch}{1.3}


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


%% 字号
\newlength\noilinespace
\newcommand{\noi@choosefont}[2]{
   \setlength{\noilinespace}{ #2*\real{ #1 } }
   \fontsize{ #2 }{\noilinespace}\selectfont}
\def\tuack@definefontsize#1#2{
  \expandafter\newcommand\csname #1\endcsname[1][\baselinestretch]{
    \noi@choosefont{ ##1 }{ #2 }}}
\tuack@definefontsize{chuhao}{42bp}
\tuack@definefontsize{xiaochu}{36bp}
\tuack@definefontsize{yihao}{26bp}
\tuack@definefontsize{xiaoyi}{24bp}
\tuack@definefontsize{erhao}{22bp}
\tuack@definefontsize{xiaoer}{18bp}
\tuack@definefontsize{sanhao}{16bp}
\tuack@definefontsize{xiaosan}{15bp}
\tuack@definefontsize{sihao}{14bp}
\tuack@definefontsize{banxiaosi}{13bp}
\tuack@definefontsize{xiaosi}{12bp}
\tuack@definefontsize{dawu}{11bp}
\tuack@definefontsize{wuhao}{10.5bp}
\tuack@definefontsize{xiaowu}{9bp}
\tuack@definefontsize{liuhao}{7.5bp}
\tuack@definefontsize{xiaoliu}{6.5bp}
\tuack@definefontsize{qihao}{5.5bp}
\tuack@definefontsize{bahao}{5bp}


%% Some styles
%% \newcommand{\filename}[1]{\bfseries\textit{#1}}
\renewcommand{\textbf}[1]{{\bfseries\CJKunderdot{#1}}}
\renewcommand{\emph}[1]{{\bfseries\textit{#1}}}
\renewcommand{\texttt}[1]{{\ttfamily\CJKunderline{#1}}}


%% 枚举类型间距
\setenumerate[1]{itemsep=0pt,partopsep=0pt,parsep=\parskip,topsep=0pt,leftmargin=3em}
\setitemize[1]{itemsep=0pt,partopsep=0pt,parsep=\parskip,topsep=0pt,leftmargin=3em}
\setdescription{itemsep=0pt,partopsep=0pt,parsep=\parskip,topsep=0pt,leftmargin=3em}


% section titles
\renewcommand{\sectionmark}[1]{\markright{#1}}
\renewcommand{\subsectionmark}[1]{}
\renewcommand{\subsubsectionmark}[1]{}

\renewcommand\section{
	\@startsection{section}{1}{\z@}
	{-24bp plus -1ex minus -.2ex}
	{6bp plus .2ex}
	{\heiti \xiaoer[1.429]}
}

\newcommand{\sqbr}[1]{【#1】}
\titleformat{\subsection}{\heiti\banxiaosi}{}{1em}{\sqbr}

\renewcommand\subsubsection{
	\@startsection{subsubsection}{3}{\z@}
	{0ex plus 1ex minus .2ex}
	{1ex plus .2ex}
	{\heiti \xiaosi[1.667]}
}

\newcommand{\tightlist}{\setlength{\itemsep}{0pt}\setlength{\parskip}{0pt}}

\renewcommand\tableofcontents{
	{\xiaosan \bfseries \thecontent \par}
	{\xiaosi \@starttoc{toc}}
}


% math related
\DeclareMathOperator{\xor}{xor}
\DeclarePairedDelimiter{\abs}{\lvert}{\rvert}


% hyperref
\hypersetup{
  setpagesize=false,
  colorlinks=true,
  linkcolor=blue,
  breaklinks=true,
  pdfborder={0 0 0}
}


% listing
\lstset{
  columns=fullflexible,
  keepspaces=true,
  showspaces=false,
  showtabs=false,
  breaklines=true,
  showstringspaces=false,
  breakatwhitespace=true,
  rulecolor=\lst@ifdisplaystyle\color{blue}\fi,
  commentstyle=\itshape\lst@ifdisplaystyle\color{green}\fi,
  stringstyle=\bfseries\lst@ifdisplaystyle\color{amber}\fi,
  keywordstyle=\bfseries\lst@ifdisplaystyle\color{purple}\fi,
  numberstyle=\footnotesize\ttfamily\lst@ifdisplaystyle\color{gray}\fi,
  basicstyle=\ttfamily\normalsize,
  frame=single,
  framesep=3pt,
  xleftmargin=12pt,
  tabsize=4,
  captionpos=b,
  numbers=left
}


% workaround for pandoc generated tex
\newcommand{\passthrough}[1]{#1}
