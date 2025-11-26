@x Change file for mmmix.w to support Emscripten compilation - make buffer static
char buffer[BUF_SIZE];
@y
static char buffer[BUF_SIZE];
@z
