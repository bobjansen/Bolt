@x Change file for Makefile to support Emscripten compilation
#   If you prefer optimization to debugging, change -g to something like -O:
CFLAGS = -g
@y
#   Emscripten compiler flags
CC = emcc
CFLAGS = -O2 -s ALLOW_MEMORY_GROWTH=1 -s MODULARIZE=1 -s EXPORT_ES6=1
@z

@x Change abstime target for Emscripten
mmix-pipe.o: mmix-pipe.c abstime
	./abstime > abstime.h
	$(CC) $(CFLAGS) -c mmix-pipe.c
	rm abstime.h
@y
mmix-pipe.o: mmix-pipe.c abstime.js
	node abstime.js > abstime.h
	$(CC) $(CFLAGS) -c mmix-pipe.c
	rm abstime.h
@z

@x Change mmmix target for Emscripten
mmmix:  mmix-arith.o mmix-pipe.o mmix-config.o mmix-mem.o mmix-io.o mmmix.c
	$(CC) $(CFLAGS) mmmix.c \
	  mmix-arith.o mmix-pipe.o mmix-config.o mmix-mem.o mmix-io.o -o mmmix
@y
mmmix.js:  mmix-arith.o mmix-pipe.o mmix-config.o mmix-mem.o mmix-io.o mmmix.c
	$(CC) $(CFLAGS) mmmix.c \
	  mmix-arith.o mmix-pipe.o mmix-config.o mmix-mem.o mmix-io.o -o mmmix.js
@z

@x Change mmixal target for Emscripten
mmixal: mmix-arith.o mmixal.c
	$(CC) $(CFLAGS) mmixal.c mmix-arith.o -o mmixal
@y
mmixal.js: mmix-arith.o mmixal.c
	$(CC) $(CFLAGS) mmixal.c mmix-arith.o -o mmixal.js
@z

@x Change mmix target for Emscripten
mmix:   mmix-arith.o mmix-io.o mmix-sim.c abstime
	./abstime > abstime.h
	$(CC) $(CFLAGS) mmix-sim.c mmix-arith.o mmix-io.o -o mmix
	rm abstime.h
@y
mmix.js:   mmix-arith.o mmix-io.o mmix-sim.c abstime.js
	node abstime.js > abstime.h
	$(CC) $(CFLAGS) mmix-sim.c mmix-arith.o mmix-io.o -o mmix.js
	rm abstime.h
@z

@x Change mmotype target for Emscripten
mmotype: mmotype.c
	$(CC) $(CFLAGS) mmotype.c -o mmotype
@y
mmotype.js: mmotype.c
	$(CC) $(CFLAGS) mmotype.c -o mmotype.js
@z

@x Add new targets for Emscripten build
basic:  mmixal mmix
@y
basic:  mmixal.js mmix.js

abstime.js: abstime.c
	$(CC) $(CFLAGS) abstime.c -o abstime.js
@z

@x Update all target for Emscripten
all:    mmixal mmix mmotype mmmix
@y
all:    mmixal.js mmix.js mmotype.js mmmix.js
@z

@x Update clean target to remove .js and .wasm files
clean:
	rm -f *~ *.o *.c *.h *.tex *.log *.dvi *.toc *.idx *.scn *.ps core
@y
clean:
	rm -f *~ *.o *.c *.h *.tex *.log *.dvi *.toc *.idx *.scn *.ps core *.js *.wasm
@z
