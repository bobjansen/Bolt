@x Change file for abstime.w to support Emscripten
@* Intro. This tiny program prints the number of seconds
elapsed since 00:00:00 Greenwich Mean Time
on January 1, 1970. (Greenwich Mean Time is now more properly
called Coordinated Universal Time, or UTC.)
@y
@* Intro. This tiny program prints the number of seconds
elapsed since 00:00:00 Greenwich Mean Time
on January 1, 1970. (Greenwich Mean Time is now more properly
called Coordinated Universal Time, or UTC.)

This version has been adapted for Emscripten compilation.
@z

@x Fix main() declaration and time format for C99/Emscripten
main()
{
  printf("#define ABSTIME %ld\n",time(NULL));
  return 0;
}
@y
int main()
{
  printf("#define ABSTIME %lld\n",(long long)time(NULL));
  return 0;
}
@z
