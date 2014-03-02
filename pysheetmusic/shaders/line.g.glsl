# version 330 core
layout(points) in;
layout(triangle_strip, max_vertices=4) out;
uniform mat3 matrix;
in vec2 start[], end[];
in float width1[];

void main() {
    vec2 v1 = start[0];
    vec2 v2 = end[0];
    float width = width1[0];
    vec2 p = normalize(v2 - v1);
    p = vec2(-p.y, p.x) * (width / 2);
    gl_Position = vec4(matrix * vec3(v1 - p, 1), 1); EmitVertex();
    gl_Position = vec4(matrix * vec3(v1 + p, 1), 1); EmitVertex();
    gl_Position = vec4(matrix * vec3(v2 - p, 1), 1); EmitVertex();
    gl_Position = vec4(matrix * vec3(v2 + p, 1), 1); EmitVertex();
    EndPrimitive();
}
