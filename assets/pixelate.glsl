#version 300 es
#ifdef GL_ES
precision highp float;
#endif

/* Outputs from the vertex shader */
varying vec4 frag_color;
varying vec2 tex_coord0;

/* uniform texture samplers */
uniform sampler2D texture0;

uniform float pixel_size;

void main()
{
    float dx = pixel_size / float(textureSize(texture0, 0).x);
    float dy = pixel_size / float(textureSize(texture0, 0).y);
    vec2 coord = vec2(dx * floor(tex_coord0.x / dx),
                      dy * floor(tex_coord0.y / dy));
    gl_FragColor = texture2D(texture0, coord);
}
