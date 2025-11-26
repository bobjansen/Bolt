@x Change file for mmotype.w to fix C99 compatibility warnings
int main(argc,argv)
  int argc;@+char*argv[];
@y
int main(int argc, char*argv[])
@z
