# version 330 core
uniform sampler2D textureSampler;
uniform vec4 color;
in vec2 uv;
out vec4 fragColor;

void main() {
    fragColor = texture(textureSampler, uv).a * color;
}
