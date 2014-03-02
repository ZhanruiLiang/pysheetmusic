# version 330 core
uniform mat3 matrix;
layout(points) in;
layout(triangle_strip, max_vertices=4) out;
in vec2 start[], end[];
in float height1[];

void main() {
    vec2 h = vec2(0, height1[0]);
    gl_Position = vec4(matrix * vec3(start[0], 1), 1); EmitVertex();
    gl_Position = vec4(matrix * vec3(end[0], 1), 1); EmitVertex();
    gl_Position = vec4(matrix * vec3(start[0] + h, 1), 1); EmitVertex();
    gl_Position = vec4(matrix * vec3(end[0] + h, 1), 1); EmitVertex();
    EndPrimitive();
}
