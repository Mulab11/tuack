//You can include .h file like testlib.h here
#include <cstdio>
#include <cstdlib>
#include <cstring>

FILE *inFile;
FILE *outFile;
FILE *ansFile;
FILE *scoreFile;
FILE *infoFile;
double score;
bool swap_flag;

void ret(double result, const char* info){
	const char esc[][5] = {
		"\\0", "\\x01", "\\x02", "\\x03", "\\x04", "\\x05", "\\x06", "\\a",
		"\\b", "\t", "\\n", "\v", "\\f", "\\r", "\\x0e", "\\x0f",
		"\\x10", "\\x11", "\\x12", "\\x13", "\\x14", "\\x15", "\\x16", "\\x17",
		"\\x18", "\\x19", "\\x1a", "\\x1b", "\\x1c", "\\x1d", "\\x1e", "\\x1f"
	};
	if(swap_flag){
		//Arbiter only allow to read EXACTLY one line info, no less and no more, and must BEFORE score
		for(const char* p = info; *p; p++)
			if(*p < 0 || *p >= 32)
				fputc(*p, infoFile);
			else
				fprintf(infoFile, esc[*p]);
		fputc('\n', infoFile);
	}
	fprintf(scoreFile, "%.6f\n", result * score);
	if(!swap_flag)
		fprintf(infoFile, "%s\n", info);
	exit(0);
}

int main(int argc, char **argv){
	//You'd better not change this swith block
	switch(argc){
		case 0:		//LOJ
			inFile = fopen("input", "r");
			outFile = fopen("user_out", "r");
			ansFile = fopen("answer", "r");
			scoreFile = stdout;
			infoFile = stderr;
			score = 100;
			break;
		case 4:		//Arbiter
			inFile = fopen(argv[1], "r");
			outFile = fopen(argv[2], "r");
			ansFile = fopen(argv[3], "r");
			scoreFile = infoFile = fopen("/tmp/_eval.score", "w");
			score = 10;
			swap_flag = true;
			break;
		case 5:
			if(strcmp(argv[4], "THUOJ") == 0){	//Tsinghua OJ(OJ for DSA course)
				inFile = fopen(argv[1], "r");
				outFile = fopen(argv[3], "r");
				ansFile = fopen(argv[2], "r");
				scoreFile = stdout;
				infoFile = stdout;
				score = 100;
			}else{								//Tsinsen OJ
				inFile = fopen(argv[1], "r");
				outFile = fopen(argv[2], "r");
				ansFile = fopen(argv[3], "r");
				scoreFile = fopen(argv[4], "w");
				infoFile = fopen("tmp", "w");		//Tsinsen doesn't use this file
				score = 1;
			}
			break;
		case 7:		//Lemon and TUOJ
			inFile = fopen(argv[1], "r");
			outFile = fopen(argv[2], "r");
			ansFile = fopen(argv[3], "r");
			FILE *fs = fopen(argv[4], "r");
			if(fs)
				fscanf(fs, "%lf", &score);		//Current TUOJ
			else
				sscanf(argv[4], "%lf", &score);	//Lemon and future TUOJ
			scoreFile = fopen(argv[5], "w");
			infoFile = fopen(argv[6], "w");
			break;
	}
	int a, b;
	if(fscanf(outFile, "%d", &a) != 1)
		ret(0, "Can\'t read the integer.");
	fscanf(ansFile, "%d", &b);
	if(a == b)
		ret(1, "Correct.");
	else
		ret(0, "Wrong answer.");
	return 0;
}
