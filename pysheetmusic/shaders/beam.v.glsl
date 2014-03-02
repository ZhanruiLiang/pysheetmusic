# version 330 core
in vec4 line;
in float height;
out vec2 start, end;
out float height1;
void main() {
    start = line.xy;
    end = line.zw;
    height1 = height;
}
