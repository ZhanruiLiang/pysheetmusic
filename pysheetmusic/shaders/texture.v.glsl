# version 330 core
in vec4 xyuv;
uniform mat3 matrix;

out vec2 uv;

void main() {
    gl_Position = vec4(matrix * vec3(xyuv.xy, 1), 1);
    uv = xyuv.zw;
}
