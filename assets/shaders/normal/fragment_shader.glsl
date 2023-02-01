#version 330
                const float SCALE = 1;
                uniform sampler2D texture_diffuse;
                uniform sampler2D texture_normal;

                in vec2 uv;
                out vec4 f_color;

                

                void main() {
                    vec4 diffuse = texture(texture_diffuse, uv);
                    vec3 normal = normalize(texture(texture_normal, uv).rgb * 2.0 - 1.0);
                    

                    vec3 light_pos = vec3(0.5, 0.5, .5);
                    vec3 light_dir = normalize(light_pos - vec3(uv, 0.0));
                    float diffuse_factor = max(dot(normal, light_dir), 0.0);


                    f_color = vec4(diffuse.rgb * diffuse_factor, diffuse.a);
                    //f_color = vec4(emission.r, emission.r, emission.r, emission.a);
                    //f_color = vec4(diffuse.rgba * light_pos);
                    //f_color = vec4(vec3(diffuse_factor), 1.0) * 0.75 + diffuse * 0.001;
                    //f_color = vec4(light_dir.xy, 0.0, 1.0) + diffuse * 0.001 * diffuse_factor;
                }