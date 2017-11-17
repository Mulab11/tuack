//You can include .h file like testlib.h here
#include <cstdio>
#include <cstdlib>

FILE *inFile;
FILE *outFile;
FILE *ansFile;
FILE *scoreFile;
FILE *infoFile;
double score;

void ret(double result, const char* info){
	fprintf(infoFile, "%s\n", info);	//Arbiter only allow to read EXACTLY one line info, no less and no more, and must BEFORE score
	fprintf(scoreFile, "%.6f\n", result * score);
	exit(0);
}

int main(int argc, char **argv){
	//You'd better not change this swith block
	switch(argc){
		case 4:		//Arbiter
			inFile = fopen(argv[1], "r");
			outFile = fopen(argv[2], "r");
			ansFile = fopen(argv[3], "r");
			scoreFile = infoFile = fopen("/tmp/_eval.score", "w");
			score = 10;
			break;
		case 5:		//Tsinsen OJ
			inFile = fopen(argv[1], "r");
			outFile = fopen(argv[2], "r");
			ansFile = fopen(argv[3], "r");
			scoreFile = fopen(argv[4], "w");
			infoFile = fopen("tmp", "w");		//Tsinsen doesn't use this file
			score = 1;
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
