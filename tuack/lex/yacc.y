%{
#include "main.h"

extern "C"
{
	void yyerror(const char *s);
	extern int yylex(void);

	extern int myoffset;
}

%}

%type<str>empty
%token<str>empty1

%%

empty:
	empty1
	{

	};

%%

void yyerror(const char *s){
	cerr<<s<<endl;
}

int main(int argc, char** argv){
	if(argc > 1){
		cerr << "format checker version: 0.1" << endl;
		return 0;
	}
	myoffset = 0;
	yyparse();

	return 0;
}
