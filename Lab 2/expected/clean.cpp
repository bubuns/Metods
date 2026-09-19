int sum_to(int n) {
int total = 0;
int i = 1;
while (i <= n) {
total = total + i;
i = i + 1;
}
return total;
}
int main() {
int limit = 3;
double scale = 1.5;
bool enabled = true;
const char* label = "sum // value";
int result = sum_to(limit);
double weighted = result * scale;
if (enabled && result > 0) {
result = result + 2;
} else {
result = 0;
}
return result;
}
