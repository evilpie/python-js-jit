var x, y = +'nan', z = 'string';

x == x ? 1 : 0;
y == y ? 0 : 1;

z == z ? 1 : 0;
z == 'other string' ? 0 : 1;
