//This is a chk avoiding spaces at each end of a line and \n at end of the file
//You can include .h file like testlib.h here
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <sstream>

FILE *inFile;
FILE *outFile;
FILE *ansFile;
FILE *scoreFile;
FILE *infoFile;
double score;
bool swap_flag;
std::ostringstream info;

const char esc[][5] = {
	"\\0", "\\x01", "\\x02", "\\x03", "\\x04", "\\x05", "\\x06", "\\a",
	"\\b", "\t", "\\n", "\v", "\\f", "\\r", "\\x0e", "\\x0f",
	"\\x10", "\\x11", "\\x12", "\\x13", "\\x14", "\\x15", "\\x16", "\\x17",
	"\\x18", "\\x19", "\\x1a", "\\x1b", "\\x1c", "\\x1d", "\\x1e", "\\x1f"
};
const int CONTEXT_LEN = 10;

struct Reader{
	int ptr, len, line, col;
	bool eof, first;
	FILE *file;
	char buff[CONTEXT_LEN * 3 + 11];
	void fresh(){
		if(!eof && len - ptr < CONTEXT_LEN + 1){
			int lef = std::max(ptr - CONTEXT_LEN, 0);
			int rig = std::min(len, ptr + CONTEXT_LEN * 2 + 1);
			for(int i = lef, j = 0; i <= rig; i++, j++)
				buff[j] = buff[i];
			ptr -= lef;
			len = rig - lef;
			for(int end = ptr + CONTEXT_LEN * 2 + 2; len < end;){
				char c = fgetc(file);
				if(c == EOF){
					eof = true;
					break;
				}
				buff[len++] = c;
			}
			buff[len] = 0;
			first = false;
		}
		if(!line){
			line = 1;
			first = true;
			col++;
		}
	}
	char cur(){
		fresh();
		return buff[ptr];
	}
	char next(){
		if(buff[ptr] == '\n'){
			line++;
			col = 0;
		}
		if(buff[ptr]){
			ptr++;
			col++;
		}
		fresh();
		return buff[ptr];
	}
}outf, ansf;

std::ostream& operator<<(std::ostream& ost, const Reader& r){
	int lef = std::max(r.ptr - CONTEXT_LEN, 0);
	int rig = std::min(r.ptr + CONTEXT_LEN + 1, r.len);
	if(!r.first || lef != 0)
		ost << "...";
	for(int i = lef; i < rig; i++){
		if(i == r.ptr)
			ost << '{';
		if(r.buff[i] < 0 || r.buff[i] >= 32)
			ost << r.buff[i];
		else
			ost << esc[r.buff[i]];
		if(i == r.ptr)
			ost << '}';
	}
	if(!r.eof || rig != r.len)
		ost << "...";
	return ost;
}

void ret(double result, bool add_context = true){
	if(add_context){
		info << "out: [" << outf << "] at line " << outf.line << ", column " << outf.col <<".\n";
		info << "ans: [" << ansf << "] at line " << ansf.line << ", column " << ansf.col <<".\n";
	}
	if(swap_flag){
		//Arbiter only allow to read EXACTLY one line info, no less and no more, and must BEFORE score
		for(const char* p = info.str().data(); *p; p++)
			if(*p < 0 || *p >= 32)
				fputc(*p, infoFile);
			else
				fprintf(infoFile, esc[*p]);
		fputc('\n', infoFile);
	}
	fprintf(scoreFile, "%.6f\n", result * score);
	if(!swap_flag)
		fprintf(infoFile, "%s\n", info.str().data());
	exit(0);
}

int main(int argc, char **argv){
	//You'd better not change this swith block
	switch(argc){
		case 0: case 1:		//LOJ and debug
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
	outf.file = outFile;
	ansf.file = ansFile;
	while(ansf.next()){
		outf.next();
		if(ansf.cur() == '\n')
			for(; outf.cur() == ' '; outf.next());
		if(outf.cur() == '\n' || !outf.cur())
			for(; ansf.cur() == ' '; ansf.next());
		if(!outf.cur())
			if(ansf.cur() == '\n' || !ansf.cur())
				break;
			else{
				info << "The answer is longer than your output.\n";
				ret(0);
			}
		if(ansf.cur() != outf.cur()){
			info << "Your output is different from the answer.\n";
			ret(0);
		}
	}
	for(outf.next(); outf.cur() == ' '; outf.next());
	if(outf.cur()){
		info << "Your output is longer than the answer. \n";
		ret(0);
	}
	info << "Correct.";
	ret(1, false);
	return 0;
}
