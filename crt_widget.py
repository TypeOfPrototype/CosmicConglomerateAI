VERTEX_SHADER = """
#version 120

// This is a basic pass-through vertex shader.
// It receives vertex attributes (position and texture coordinates)
// from the application and passes them to the fragment shader.

// Standard Kivy attributes
attribute vec3 vertex;
attribute vec2 tex_coord;
attribute vec4 color; // Kivy's default vertex format includes color

// Uniforms provided by Kivy's RenderContext
uniform mat4 modelview_mat;
uniform mat4 projection_mat;
// uniform vec4 frag_color; // This is usually a varying, not a uniform passed in by default for custom shaders like this
// uniform float opacity; // Similarly, opacity is often handled via frag_color.a

// Output varying variables to be interpolated and passed to the fragment shader.
varying vec4 frag_color; // To pass vertex color or a default color
varying vec2 tex_coord0; // To pass texture coordinates

void main() {
    // Standard Kivy transformation for vertex position.
    // The FBO content is typically drawn on a simple quad, so vertex.xy is used.
    // z=0, w=1 for 2D rendering.
    gl_Position = projection_mat * modelview_mat * vec4(vertex.xy, 0.0, 1.0);

    // Pass the texture coordinate to the fragment shader.
    // Kivy binds the FBO texture to tex_coord0 by default for the first texture.
    tex_coord0 = tex_coord;

    // Pass the vertex color (or a default color) to the fragment shader.
    // This allows tinting or using vertex colors if needed, though for FBO rendering
    // it's often just white.
    frag_color = color;
}
"""

FRAGMENT_SHADER = """
#version 120

// This fragment shader simulates the visual artifacts of an old CRT monitor.

// Uniforms: These are variables passed from the application to the shader.
uniform vec2 resolution; // Resolution of the screen in pixels.
uniform float time;      // Time in seconds, used for animations like flicker.
uniform sampler2D tex0;  // The input texture (e.g., the game screen).

// Varying variable: Texture coordinate interpolated from the vertex shader.
varying vec2 tex_coord0; // Changed from vTexCoord to match vertex shader

// -- Configuration Constants for Effects --
// These constants can be tweaked to change the intensity of the effects.

// Barrel Distortion
const float barrelPower = 1.15; // Strength of the barrel distortion. Higher values mean more distortion.

// Scanlines
const float scanlineOpacity = 0.15; // How visible the scanlines are (0.0 to 1.0).
const float scanlineDensityFactor = 800.0; // Higher values mean more scanlines.

// Vignetting
const float vignetteOuterRadius = 0.85; // Outer radius of the vignette (0.0 to 1.0).
const float vignetteInnerRadius = 0.35;  // Inner radius of the vignette, where it's brightest (0.0 to 1.0).
const float vignetteOpacity = 0.6;     // Opacity of the vignette effect.

// Chromatic Aberration
const float chromaticAberrationAmount = 0.003; // Amount of color separation.

// Flicker/Jitter
const float flickerIntensity = 0.002; // Intensity of the subtle screen flicker.

// Shadow Mask/Aperture Grille
const float shadowMaskIntensity = 0.15; // Intensity of the shadow mask effect.
const float shadowMaskDensity = 3.0;   // Density of the shadow mask pattern.


// Helper function for barrel distortion.
// Takes texture coordinates (uv) and returns distorted coordinates.
vec2 barrelDistortion(vec2 uv, float power) {
    // Calculate the distance from the center of the screen.
    // The coordinates are shifted so that (0,0) is the center.
    vec2 centeredUV = uv - 0.5;
    float r = dot(centeredUV, centeredUV); // r = x^2 + y^2 (squared distance)
    // Apply the distortion. The formula creates a pincushion or barrel effect.
    // 'pow(r, power)' controls the amount of distortion based on distance from center.
    vec2 distortedUV = centeredUV * pow(r, power - 1.0);
    return distortedUV + 0.5; // Shift back to original coordinate system.
}

// Helper function to generate a random float.
// Used for effects like flicker.
float rand(vec2 co){
    // A common way to generate pseudo-random numbers in shaders.
    // It uses the fractional part of the sine of a large number
    // based on the dot product of the input coordinate and a fixed vector.
    return fract(sin(dot(co.xy ,vec2(12.9898,78.233))) * 43758.5453);
}

void main() {
    // -- 0. Normalize Texture Coordinates --
    // tex_coord0 ranges from 0.0 to 1.0.
    // For some effects, it's easier to work with coordinates
    // that are centered at (0,0) and range from -0.5 to 0.5,
    // or use aspect ratio correction.
    vec2 uv = tex_coord0;

    // -- 1. Barrel Distortion --
    // This effect simulates the curvature of old CRT screens.
    // Lines near the edges of the screen appear to be bent outwards.
    vec2 distortedUV = barrelDistortion(uv, barrelPower);

    // Check if the distorted UV coordinates are outside the valid range [0,1].
    // If so, discard the fragment (make it transparent) to avoid rendering artifacts
    // from sampling outside the texture.
    if (distortedUV.x < 0.0 || distortedUV.x > 1.0 || distortedUV.y < 0.0 || distortedUV.y > 1.0) {
        gl_FragColor = vec4(0.0, 0.0, 0.0, 0.0); // Transparent black
        return;
    }

    // -- 2. Chromatic Aberration --
    // This effect mimics the slight color fringing seen on CRTs due to
    // misalignment of the red, green, and blue electron beams.
    // It's achieved by sampling the texture at slightly offset positions
    // for each color channel.
    vec2 R_uv = distortedUV + vec2(chromaticAberrationAmount, 0.0);
    vec2 G_uv = distortedUV;
    vec2 B_uv = distortedUV - vec2(chromaticAberrationAmount, 0.0);

    float rChannel = texture2D(tex0, R_uv).r;
    float gChannel = texture2D(tex0, G_uv).g;
    float bChannel = texture2D(tex0, B_uv).b;

    vec3 baseColor = vec3(rChannel, gChannel, bChannel);

    // -- 3. Scanlines --
    // Simulates the horizontal lines visible on CRT displays.
    // This is done by darkening every Nth line of pixels.
    // 'scanlineDensityFactor / resolution.y' gives the number of scanlines.
    // 'sin(distortedUV.y * scanlineDensityFactor)' creates a wave pattern.
    // The result is clamped and scaled to control opacity.
    float scanlineEffect = sin(distortedUV.y * scanlineDensityFactor);
    scanlineEffect = clamp(scanlineEffect, 0.0, 1.0); // Ensure it's between 0 and 1
    scanlineEffect = pow(scanlineEffect, 4.0); // Make lines sharper
    vec3 scanlineColor = baseColor * (1.0 - scanlineEffect * scanlineOpacity);
    vec3 color = scanlineColor;

    // -- 4. Shadow Mask / Aperture Grille --
    // Simulates the mask between phosphors on a CRT screen.
    // This creates a fine dot or line pattern.
    // We use a simple repeating pattern based on screen coordinates.
    float maskCoordX = distortedUV.x * resolution.x * shadowMaskDensity / resolution.x; // Normalize by aspect
    float maskCoordY = distortedUV.y * resolution.y * shadowMaskDensity / resolution.y;
    float shadowMaskPattern = 0.0;
    // A common way is to create a grid pattern.
    // This example uses a simple alternating pattern.
    if (mod(floor(maskCoordX) + floor(maskCoordY), 2.0) < 1.0) {
        shadowMaskPattern = 1.0 - shadowMaskIntensity;
    } else {
        shadowMaskPattern = 1.0;
    }
    color *= shadowMaskPattern;


    // -- 5. Vignetting --
    // This effect darkens the corners of the screen, a common characteristic
    // of older displays and lenses.
    // Calculate distance from the center of the screen (0.5, 0.5).
    float distFromCenter = distance(distortedUV, vec2(0.5));
    // 'smoothstep' creates a smooth transition between the inner and outer radius.
    // The vignette factor is 1.0 (no darkening) inside vignetteInnerRadius,
    // and fades to (1.0 - vignetteOpacity) at vignetteOuterRadius.
    float vignette = smoothstep(vignetteOuterRadius, vignetteInnerRadius, distFromCenter);
    color *= (1.0 - (1.0 - vignette) * vignetteOpacity);


    // -- 6. Subtle Flicker/Jitter (Optional) --
    // Adds a very subtle random brightness variation or slight position jitter
    // to mimic the instability of CRT electron beams.
    // 'rand(uv + time)' generates a pseudo-random value that changes over time.
    float flicker = rand(distortedUV.xy + time) * flickerIntensity;
    color += flicker; // Additive flicker, could also be multiplicative.

    // Jitter can be added by slightly offsetting texture coordinates:
    // vec2 jitterOffset = vec2(rand(distortedUV + time * 0.1) - 0.5, rand(distortedUV + time * 0.2) - 0.5) * 0.001;
    // color = texture2D(tex0, distortedUV + jitterOffset); // Resample with jitter

    // Final color output.
    // gl_FragColor is the output color of the fragment.
    gl_FragColor = vec4(color, 1.0);
}
"""

# Python Kivy specific imports
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import RenderContext, Fbo, Color, Rectangle, ClearColor, ClearBuffers
from kivy.graphics.texture import Texture
from kivy.clock import Clock
import time as pytime # Use pytime to avoid conflict with shader 'time' uniform

class CRTEffectWidget(FloatLayout):
    """
    CRTEffectWidget applies a CRT-like visual effect to its children.

    It uses a Framebuffer Object (Fbo) to render its children to an off-screen
    texture. This texture is then drawn to the screen using a custom GLSL shader
    that simulates CRT effects like barrel distortion, scanlines, etc.
    """
    def __init__(self, **kwargs):
        super(CRTEffectWidget, self).__init__(**kwargs)

        # --- FBO and RenderContext Setup ---
        # The RenderContext is where our shaders will live.
        self.canvas = RenderContext(use_parent_projection=True, use_parent_modelview=True)
        self.canvas.shader.vs = VERTEX_SHADER
        self.canvas.shader.fs = FRAGMENT_SHADER

        # The Fbo (Framebuffer Object) is used to render children to a texture.
        # This texture (self.fbo.texture) will be the input 'tex0' for our fragment shader.
        with self.canvas:
            # ClearColor and ClearBuffers are important for FBOs.
            # They ensure the FBO is cleared properly before drawing to it each frame.
            self._fbo_clear_color = ClearColor(0, 0, 0, 0) # Clear with transparent black
            self._fbo_clear_buffers = ClearBuffers(clear_color=True, clear_depth=True)
            self.fbo = Fbo(size=self.size, use_parent_projection=True, use_parent_modelview=True)

        # This Rectangle will display the FBO's texture, processed by the CRT shader.
        # It's drawn on the main canvas (self.canvas), not the FBO's canvas.
        with self.canvas:
            Color(1, 1, 1, 1) # White, so texture colors are not tinted
            self.fbo_rect = Rectangle(size=self.size, pos=self.pos, texture=self.fbo.texture)

        # Bind texture updates and size/pos changes.
        self.fbo.add_reload_observer(self.populate_fbo) # Re-draw FBO content if context is lost
        self.bind(size=self._update_rect_and_fbo, pos=self._update_rect_and_fbo)

        # --- Shader Uniforms ---
        # Initialize shader uniforms. 'tex0' is automatically bound to the FBO texture.
        self.canvas['time'] = 0.0
        self.canvas['resolution'] = list(self.size)

        # Schedule the update_glsl method to be called every frame.
        # 0 means it will be called before the next frame is drawn.
        Clock.schedule_interval(self.update_glsl, 0)
        self._time_start = pytime.time()

        # This list will hold children that are "actually" added to this widget.
        # We manage them here because they're drawn onto the FBO.
        self._real_children = []


    def populate_fbo(self, fbo_instance):
        """
        This method is called to redraw the contents of the FBO.
        It's typically called automatically when the FBO needs to be updated,
        e.g., after a context reload or if a child widget changes.
        """
        # Ensure FBO is properly cleared before drawing children.
        # Note: Kivy's FBO handles much of this internally when self.fbo.draw() is called,
        # but explicit clearing can be good practice if issues arise.
        # For this setup, we add children to fbo.canvas, and Kivy handles their drawing.
        pass # Children are added to fbo.canvas directly.


    def _update_rect_and_fbo(self, instance, value):
        """
        Update the size and position of the FBO and the Rectangle that displays it.
        This is called when the widget's size or position changes.
        """
        self.fbo.size = self.size
        self.fbo_rect.size = self.size
        self.fbo_rect.pos = self.pos
        # Update shader resolution uniform
        # Removing the check `if 'resolution' in self.canvas:` to see if direct assignment works
        # or provides a more specific error if the uniform is problematic.
        self.canvas['resolution'] = list(self.size)

    def update_glsl(self, dt):
        """
        Update GLSL uniforms. This method is called regularly by Kivy's Clock.
        'dt' is the time elapsed since the last call (delta time).
        """
        self.canvas['time'] = pytime.time() - self._time_start
        # Resolution is updated in _update_rect_and_fbo when size changes,
        # but good to ensure it's set if needed, e.g., on initialization.
        # self.canvas['resolution'] = list(self.size) # Already handled by binding

    # --- Widget Management Overrides ---
    # These methods are overridden to redirect child widgets to the FBO's canvas.
    # This is the core trick to make children render to the FBO's texture.

    def add_widget(self, widget, index=0, canvas=None):
        """
        Override add_widget. Instead of adding to this widget's canvas,
        add children to the FBO's canvas.
        """
        # We add the widget's canvas to the FBO's instruction group.
        # This means the widget itself is not a direct child of the FBO in Kivy's
        # widget tree sense, but its visual representation is drawn onto the FBO.
        self.fbo.add(widget.canvas)
        # Keep track of the widget conceptually.
        # super().add_widget is not called to prevent Kivy's default rendering
        # of the child directly onto the parent's canvas.
        self._real_children.append(widget)
        # Manually manage widget properties like parent, if needed for event bubbling, etc.
        # For basic rendering, this might not be strictly necessary, but good for consistency.
        widget.parent = self # Set parent link

    def remove_widget(self, widget):
        """
        Override remove_widget to remove children from the FBO's canvas.
        """
        if widget in self._real_children:
            self.fbo.remove(widget.canvas)
            self._real_children.remove(widget)
            widget.parent = None # Clear parent link
        else:
            # This case handles widgets that might be added by Kivy internally
            # or if the widget wasn't one we redirected.
            super(CRTEffectWidget, self).remove_widget(widget)


    def clear_widgets(self, children=None):
        """
        Override clear_widgets to remove all redirected children from the FBO.
        """
        # If specific children are given, remove them one by one.
        if children is not None:
            for child in list(children): # Iterate over a copy
                self.remove_widget(child)
            return

        # If no children are specified, remove all 'real_children' we are managing.
        for child in list(self._real_children): # Iterate over a copy
            self.fbo.remove(child.canvas)
            child.parent = None # Clear parent link
        self._real_children = []

        # It's also important to clear any other children Kivy might have added
        # to this widget directly (though our add_widget tries to prevent this).
        super(CRTEffectWidget, self).clear_widgets()
