#version 330
                const float SCALE = 1;

                in vec2 in_vert;
                in vec2 in_uv;
                out vec2 uv;

                void main() {
                    uv = in_uv * SCALE;
                    gl_Position = vec4(in_vert, 0.0, 1.0);
                }