#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

int printer(int i)
{
	sleep(1);
	printf("Loop nr: %d\n", i);
}

int main()
{
	for (int i=0;;i++)
		printer(i);

	return 0;
}
