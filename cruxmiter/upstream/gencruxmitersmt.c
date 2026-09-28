#include <assert.h>
#include <stdarg.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void die (const char * fmt, ...) {
  va_list ap;
  fputs ("*** gencruxmitersmt: ", stderr);
  va_start (ap, fmt);
  vfprintf (stderr, fmt, ap);
  va_end (ap);
  fputc ('\n', stderr);
  exit (1);
}

static char fmt[10];
static int size;
static int width;
static int seed;

#define MAXBUF 1024
static char buf[MAXBUF];
static int top;

static int * first, * second;
static int adds;

static char * next () {
  char * res;
  res = buf + top;
  top += 128;
  if (top == MAXBUF) top = 0;
  return res;
}

static const char * node (char * prefix, int i) {
  char * res = next ();
  strcpy (res, prefix);
  sprintf (res + strlen (prefix), fmt, i);
  return res;
}

static const char * input (int i) { return node ("x", i); }
static const char * extend (int i) { return node ("e", i); }

static const char * add (int i) {
  if (i < size) return extend (i);
  if (i < 2*size) return extend (second[i-size]);
  return node ("a", i - 2*size);
}

static int print (int * order, int l, int r) {
  int size = r - l, m, res, c, d;
  assert (size > 0);
  if (size == 1) return order[l];
  if (size == 2) m = l + 1;
  else m = l + rand () % (size - 2) + 1;
  assert (l < m), assert (m < r);
  c = print (order, l, m);
  d = print (order, m, r);
  res = adds++;
  printf ("(assert (= %s (bvadd %s %s)))\n", add (res), add (c), add (d));
  return res;
}

int main (int argc, char ** argv) {
  int i, ceilog10, * order, tmp, l, r;
  if (argc < 2) {
    printf ("usage: gencruxmitersmt <size> [ <seed> ]\n");
    exit (0);
  }
  if (argc > 3) die ("too many arguments (run without arguments)");
  for (i = 1; i < argc; i++) {
    if (size > 0) seed = atoi (argv[i]);
    else if ((size = atoi (argv[i])) < 2)
      die ("invalid size '%s' (has to be at least 2)", argv[i]);
  }
  assert (size > 1);
  srand (seed);
  for (width = 1; (1<<width) <= size; width++)
    ;
  assert (width > 1);
  for (tmp = 10, ceilog10 = 1; size-1 >= tmp; ceilog10++, tmp *= 10)
    ;
  sprintf (fmt, "%%0%dd", ceilog10);
  first = malloc (size * sizeof *first);
  for (i = 0; i < size; i++) first[i] = i;
  second = malloc (size * sizeof *second);
  printf ("(set-logic QF_BV)\n");
  for (i = 0; i < size; i++) {
    int j = rand () % (i + 1);
    second[i] = second[j];
    second[j] = i;
  }
  for (int i = 0; i < size; i++)
    printf ("(declare-fun %s () (_ BitVec 1))\n", input (i));
  for (int i = 0; i < size; i++)
    printf ("(declare-fun %s () (_ BitVec %d))\n", extend (i), width);
  for (int i = 0; i < 2*size-2; i++)
    printf ("(declare-fun %s () (_ BitVec %d))\n", add (2*size + i), width);
  for (int i = 0; i < size; i++)
    printf ("(assert (= %s ((_ zero_extend %d) %s)))\n",
      extend (i), width-1, input (i));
  adds = 2*size;
  order = malloc (size * sizeof *second);
  for (int i = 0; i < size; i++) order[i] = i;
  l = print (order, 0, size);
  order = malloc (size * sizeof *second);
  for (int i = 0; i < size; i++) order[i] = size + i;
  r = print (order, 0, size);
  printf ("(assert (distinct %s %s))\n", add (l), add (r));
  printf ("(check-sat)\n");
  printf ("(exit)\n");
  return 0;
}
