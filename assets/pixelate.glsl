#ifdef GL_ES
precision highp float;
#endif

varying vec4 frag_color; // Output color from vertex shader (not used here, but standard)
varying vec2 tex_coord0; // Texture coordinates from vertex shader

uniform sampler2D texture0; // The input texture

uniform float pixel_size;
uniform vec2 texture_dimensions; // To pass texture width and height

void main()
{
    if (pixel_size <= 0.0) {
        gl_FragColor = texture2D(texture0, tex_coord0);
        return;
    }
    // Ensure texture_dimensions are not zero to prevent division by zero
    if (texture_dimensions.x <= 0.0 || texture_dimensions.y <= 0.0) {
        gl_FragColor = texture2D(texture0, tex_coord0); // Fallback to original texture
        return;
    }

    float dx = pixel_size / texture_dimensions.x;
    float dy = pixel_size / texture_dimensions.y;

    // Ensure dx and dy are not zero if pixel_size is very small but positive
    if (dx <= 0.0 || dy <= 0.0) {
        gl_FragColor = texture2D(texture0, tex_coord0); // Fallback
        return;
    }

    vec2 coord = vec2(dx * floor(tex_coord0.x / dx),
                      dy * floor(tex_coord0.y / dy));
    gl_FragColor = texture2D(texture0, coord);
}
