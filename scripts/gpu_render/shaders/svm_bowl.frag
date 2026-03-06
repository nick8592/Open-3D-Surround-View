#version 330 core

out vec4 FragColor;

in vec2 TexCoord;

// The 4 raw fisheye camera textures
uniform sampler2D textureFront;
uniform sampler2D textureBack;
uniform sampler2D textureLeft;
uniform sampler2D textureRight;

// The Look-Up Tables (LUTs) for mapping UVs to camera pixels
uniform sampler2D lutFront;
uniform sampler2D lutBack;
uniform sampler2D lutLeft;
uniform sampler2D lutRight;

// Alpha blending weights to merge the seams
uniform sampler2D blendMask;

void main()
{
    // Fetch UV coordinates from the LUTs based on current bowl texture coordinate
    vec2 uvFront = texture(lutFront, TexCoord).rg;
    vec2 uvBack = texture(lutBack, TexCoord).rg;
    vec2 uvLeft = texture(lutLeft, TexCoord).rg;
    vec2 uvRight = texture(lutRight, TexCoord).rg;

    // Sample the actual camera textures using the mapped UVs
    vec4 colorFront = texture(textureFront, uvFront);
    vec4 colorBack = texture(textureBack, uvBack);
    vec4 colorLeft = texture(textureLeft, uvLeft);
    vec4 colorRight = texture(textureRight, uvRight);

    // Sample the blending weights (assumes RGBA channels map to F/B/L/R weights)
    vec4 weights = texture(blendMask, TexCoord);

    // Blend the final color based on the individual camera weights
    vec4 finalColor = (colorFront * weights.r) +
                      (colorBack * weights.g) +
                      (colorLeft * weights.b) +
                      (colorRight * weights.a);

    FragColor = finalColor;
}
