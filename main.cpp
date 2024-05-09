void log(const char*) {
}

void FOR(int a)
{
	for (int i = 0; i < 10; i++)
	{
		continue;
	}
}

int main() {

	log("sssss");
	int i=0;
	FOR(i);
	return 0;
}