# version 330 core
layout(points) in;
layout(triangle_strip, max_vertices=8) out;
uniform mat3 matrix;
in vec2 start[], end[];
in float width1[];

void emit(vec2 p) {
    gl_Position = vec4(matrix * vec3(p, 1), 1); EmitVertex();
}

void main() {
    vec2 v1 = start[0];
    vec2 v2 = end[0];
    float width = width1[0];
    vec2 p = normalize(v2 - v1);
    vec2 q = (width / 4) * p;
    vec2 r = vec2(-q.y, q.x);
    p = vec2(-p.y, p.x) * (width / 2);
    emit(v2 + p);
    emit(v1 + p);
    emit(v2 + q + r);
    emit(v1 - q + r);
    emit(v2 + q - r);
    emit(v1 - q - r);
    emit(v2 - p);
    emit(v1 - p);
    EndPrimitive();
}
