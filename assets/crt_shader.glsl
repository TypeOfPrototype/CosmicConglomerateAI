// Retro CRT Shader

---VERTEX SHADER---
#ifdef GL_ES
    precision highp float;
#endif

/* Outputs to the fragment shader */
varying vec4 frag_color;
varying vec2 tex_coord0;

/* vertex attributes */
attribute vec2     vPosition;
attribute vec2     vTexCoords0;

/* uniform variables */
uniform mat4       modelview_mat;
uniform mat4       projection_mat;
uniform vec4       color;
uniform float      opacity;
uniform vec2       resolution; // Screen resolution
uniform float      time;       // Time for animations

void main()
{
    frag_color = color * opacity;
    tex_coord0 = vTexCoords0;
    gl_Position = projection_mat * modelview_mat * vec4(vPosition.xy, 0.0, 1.0);
}

---FRAGMENT SHADER---
#ifdef GL_ES
    precision highp float;
#endif

/* Outputs from the vertex shader */
varying vec4 frag_color;
varying vec2 tex_coord0;

/* uniform texture samplers */
uniform sampler2D texture0; // Original game texture

/* Uniforms for CRT effects */
uniform vec2  resolution;         // Viewport resolution (pixels)
uniform float time;               // Time for animations (e.g., scanline movement)
uniform float effect_on;          // 0.0 for off, 1.0 for on

uniform float scanline_intensity;
uniform float curvature_amount;
uniform float vignette_intensity;
uniform float chromatic_aberration_amount;
uniform float noise_amount;

// Function to apply barrel distortion for screen curvature
vec2 barrelDistortion(vec2 coord, float power) {
    vec2 cc = coord - 0.5;
    float dist = dot(cc, cc);
    return coord + cc * dist * power;
}

// Function to generate random noise
float random(vec2 co) {
    return fract(sin(dot(co.xy, vec2(12.9898, 78.233))) * 43758.5453);
}

void main()
{
    if (effect_on == 0.0) {
        gl_FragColor = frag_color * texture2D(texture0, tex_coord0);
        return;
    }

    vec2 uv = tex_coord0;

    // 1. Screen Curvature
    vec2 distorted_uv = barrelDistortion(uv, curvature_amount);

    // Check if the distorted UV is within bounds (0.0 to 1.0)
    // If not, discard the fragment or make it black to simulate screen edge
    if (distorted_uv.x < 0.0 || distorted_uv.x > 1.0 || distorted_uv.y < 0.0 || distorted_uv.y > 1.0) {
        gl_FragColor = vec4(0.0, 0.0, 0.0, 1.0); // Black screen edge
        return;
    }

    // 2. Chromatic Aberration
    // Apply only if distortion is active, otherwise, it looks weird on edges
    vec2 R_uv = distorted_uv;
    vec2 G_uv = distorted_uv;
    vec2 B_uv = distorted_uv;

    if (chromatic_aberration_amount > 0.0) {
        vec2 dir = normalize(distorted_uv - 0.5);
        R_uv = distorted_uv - dir * chromatic_aberration_amount * 0.005; // Red channel shifted
        B_uv = distorted_uv + dir * chromatic_aberration_amount * 0.005; // Blue channel shifted
    }

    // Ensure aberration doesn't sample outside texture bounds (clamp might be too simple)
    // A better way would be to check bounds again like for distortion.
    // For now, let's assume distortion check handles major out-of-bounds.
    // A simpler clamp for safety:
    R_uv = clamp(R_uv, 0.0, 1.0);
    G_uv = clamp(G_uv, 0.0, 1.0); // G_uv is original distorted_uv
    B_uv = clamp(B_uv, 0.0, 1.0);

    float R = texture2D(texture0, R_uv).r;
    float G = texture2D(texture0, G_uv).g;
    float B = texture2D(texture0, B_uv).b;
    vec4 base_color = vec4(R, G, B, texture2D(texture0, G_uv).a);


    // 3. Scanlines
    float scanline = 1.0;
    if (scanline_intensity > 0.0) {
        float scanline_effect = sin((distorted_uv.y + time * 0.01) * resolution.y * 0.5 * scanline_intensity) * 0.5 + 0.5;
        scanline = 1.0 - (1.0 - scanline_effect) * 0.2 * scanline_intensity; // Modulate intensity
    }

    // 4. Noise
    float noise = 0.0;
    if (noise_amount > 0.0) {
        noise = (random(distorted_uv * time) - 0.5) * noise_amount;
    }

    // 5. Vignette
    float vignette = 1.0;
    if (vignette_intensity > 0.0) {
        float d = distance(distorted_uv, vec2(0.5, 0.5));
        vignette = smoothstep(0.8, 0.2 * (1.0 - vignette_intensity), d); // Adjust falloff with intensity
    }

    // Combine effects
    vec4 final_color = base_color * scanline * vignette + noise;

    // Apply original Kivy widget color and opacity
    gl_FragColor = frag_color * final_color;
}
