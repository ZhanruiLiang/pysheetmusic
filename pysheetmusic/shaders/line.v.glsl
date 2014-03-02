# version 330 core
uniform mat3 matrix;
in vec4 line;
in float width;
out vec2 start, end;
out float width1;

void main() {
    start = line.xy;
    end = line.zw;
    width1 = width;
}
